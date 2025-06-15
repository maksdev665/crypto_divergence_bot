from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.database.models import CurrencyPair, Divergence
from app.services.binance_api import BinanceAPI

logger = logging.getLogger(__name__)


class DivergenceAnalyzer:
    """Класс для анализа дивергенций между криптовалютными парами"""

    def __init__(self, session: AsyncSession, binance_api: BinanceAPI):
        self.session = session
        self.binance_api = binance_api

    async def get_active_pairs(self) -> List[CurrencyPair]:
        """Получает список активных валютных пар для отслеживания"""
        query = select(CurrencyPair).where(CurrencyPair.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_current_prices(self, pairs: List[CurrencyPair]) -> Dict[str, float]:
        """Получает текущие цены для списка валютных пар"""
        if not pairs:
            return {}
        
        symbols = [pair.symbol for pair in pairs]
        try:
            ticker_data = await self.binance_api.get_multiple_ticker_prices(symbols)
            return {item['symbol']: float(item['price']) for item in ticker_data}
        except Exception as e:
            logger.error(f"Error getting prices: {str(e)}")
            return {}

    async def calculate_divergence(
            self,
            pair1: CurrencyPair,
            pair2: CurrencyPair,
            prices: Dict[str, float]
    ) -> Optional[Tuple[float, str]]:
        """
        Рассчитывает дивергенцию между двумя валютными парами
        
        Возвращает процент дивергенции и описание, если дивергенция превышает порог,
        иначе возвращает None
        """
        if pair1.symbol not in prices or pair2.symbol not in prices:
            logger.warning(f"Missing price data for {pair1.symbol} or {pair2.symbol}")
            return None

        price1 = prices[pair1.symbol]
        price2 = prices[pair2.symbol]

        # Рассчитываем процентное изменение соотношения цен
        divergence_percent = self._calculate_divergence_percentage(price1, price2)

        # Проверяем, превышает ли дивергенция пороговое значение
        threshold = max(pair1.devergence_threshold, pair2.devergence_threshold)
        if abs(divergence_percent) >= threshold:
            direction = 'расходятся' if divergence_percent > 0 else 'сходятся'
            description = (
                f"Обнаружена дивергенция {abs(divergence_percent):.2f}% между {pair1.symbol} "
                f"и {pair2.symbol}. Пары {direction}.\n"
                f"Текущие цены: {pair1.symbol} = {price1:.8f}, {pair2.symbol} = {price2:.8f}"
            )
            return divergence_percent, description
        
        return None
    
    def _calculate_divergence_percentage(self, price1: float, price2: float) -> float:
        """
        Рассчитывает процент дивергенции между двумя ценами
        
        В этом примере мы используем простую формулу процентного изменения соотношения,
        но здесь может быть более сложная логика для реальной торговой стратегии.
        """
        # Получаем базовое соотношение цен
        ratio = price1 / price2

        # Нормализуем на единицу для упрощения сравнения
        normalized_ratio = ratio / 1.0

        # Рассчитываем процент отклонения от базового соотношения
        # В реальной стратегии здесь может быть сравнение с историческим соотношением
        divergence_percent = (normalized_ratio - 1.0) * 100

        return divergence_percent
    
    async def record_divergence(
            self,
            pair1: CurrencyPair,
            pair2: CurrencyPair,
            divergence_percent: float,
            prices: Dict[str, float],
            description: str
    ) -> Divergence:
        """Записывает найденную дивергенцию в базу данных"""
        divergence = Divergence(
            pair1_id=pair1.id,
            pair2_id=pair2.id,
            pair1_symbol=pair1.symbol,
            pair2_symbol=pair2.symbol,
            pair1_price=prices[pair1.symbol],
            pair2_price=prices[pair2.symbol],
            divergence_percent=divergence_percent,
            desciption=description,
            detected_at=datetime.now(timezone.utc()),
            notification_sent=False
        )

        self.session.add(divergence)
        await self.session.commit()
        await self.session.refresh(divergence)
        return divergence
    
    async def check_all_pairs(self) -> List[Divergence]:
        """
        Проверяет все возможные комбинации активных пар на наличие дивергенций
        
        Возвращает список обнаруженных дивергенций
        """
        pairs = await self.get_active_pairs()
        if len(pairs) < 2:
            logger.info('Недостаточно активных пар для анализа дивергенций')
            return []
        
        # Получаем текущие цены для всех пар
        prices = await self.get_current_prices(pairs)
        if not prices:
            logger.error('Не удалось получить цены')
            return []
        
        found_divergences = []

        # Проверяем все возможные комбинации пар
        for i, pair1 in enumerate(pairs):
            for pair2 in pairs[i+1:]:
                # Проверяем дивергенцию
                divergence_result = await self.calculate_divergence(pair1, pair2, prices)
                if divergence_result:
                    divergence_percent, description = divergence_result

                    # Проверяем, не было ли недавно такой же дивергенции
                    if not await self._is_recent_duplicate(pair1.id, pair2.id):
                        # Записываем дивергенцию в базу данных
                        divergence = await self.record_divergence(pair1, pair2, divergence_percent, prices, description)
                        found_divergences.append(divergence)

        return found_divergences
    
    async def _is_recent_duplicate(self, pair1_id: int, pair2_id: int) -> bool:
        """
        Проверяет, была ли недавно зарегистрирована дивергенция между теми же парами
        чтобы избежать частых дублирующих уведомлений
        """
        one_hour_ago = datetime.now(timezone.utc()) - timedelta(hour=1)

        # Проверяем в обоих направлениях (pair1-pair2 и pair2-pair1)
        query = select(Divergence).where(
            and_(
                or_(
                    and_(Divergence.pair1_id == pair1_id, Divergence.pair2_id == pair2_id),
                    and_(Divergence.pair1_id == pair1_id, Divergence.pair2_id == pair2_id)
                ),
                Divergence.detected_id >= one_hour_ago
            )
        )

        result = await self.session.execute(query)
        return result.first() is not None
    
    async def mark_as_notified(self, divergence_id: int) -> None:
        """Отмечает дивергенцию как отправленную в уведомлении"""
        query = select(Divergence).where(Divergence.id == divergence_id)
        result = await self.session.execute(query)
        divergence = result.scalar_one_or_none()

        if divergence:
            divergence.notification_sent = True
            await self.session.commit()
