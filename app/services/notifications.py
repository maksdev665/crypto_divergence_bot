import logging
from typing import List, Optional
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models import Divergence, BotSettings
from app.config import NOTIFICATION_GROUP_ID

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений о дивергенциях в Telegram"""

    def __init__(self, bot: Bot, session: AsyncSession):
        self.bot = bot
        self.session = session

    async def get_notification_group_id(self) -> str:
        """Получает ID группы для отправки уведомлений из настроек или конфига"""
        query = select(BotSettings).where(BotSettings.key == 'notification_group_id')
        result = await self.session.execute(query)
        setting = result.scalar_one_or_none()

        if setting and setting.value:
            return setting.value
        
        # Если настройка не найдена в БД, используем значение из конфига
        return NOTIFICATION_GROUP_ID
    
    async def get_bot_status(self) -> bool:
        """Проверяет, активен ли бот для отправки уведомлений"""
        query = select(BotSettings).where(BotSettings.key == 'bot_active')
        result = await self.session.execute(query)
        setting = result.scalar_one_or_none()

        # По умолчанию бот активен
        if setting is None or setting.value_bool is None:
            return  True
        
        return setting.value_bool
    
    async def format_divergence_message(self, divergence: Divergence) -> str:
        """Форматирует сообщение о дивергенции для отправки"""
        message = (
            f"🔔 <b>Обнаружена дивергенция!</b>\n\n"
            f"<b>Пары:</b> {divergence.pair1_symbol} и {divergence.pair2_symbol}\n"
            f"<b>Величина:</b> {abs(divergence.divergence_percent):.2f}%\n"
            f"<b>Время:</b> {divergence.detected_at.strftime('%d.%m.%Y %H:%M:%S')} UTC\n\n"
            f"<b>Цены:</b>\n"
            f"• {divergence.pair1_symbol}: {divergence.pair1_price:.8f}\n"
            f"• {divergence.pair2_symbol}: {divergence.pair2_price:.8f}\n\n"
        )

        # Добавляем эмодзи направления
        if divergence.divergence_percent > 0:
            message += '📈 Пары <b>расходятся</b>'
        else:
            message += '📉 Пары <b>сходятся</b>'

        return message
    
    async def test_message(self) -> str:
        return '📈 Пары <b>расходятся</b>'
    
    async def send_divergence_notification(self, divergence: Divergence) -> bool:
        """Отправляет уведомление о дивергенции в Telegram группу"""
        # Проверяем, активен ли бот
        if not await self.get_bot_status():
            logger.info('Бот не активен, уведомления не отправляются')
            return False
        
        group_id = await self.get_notification_group_id()
        if not group_id:
            logger.error('ID группы для уведомлений не найден')
            return False
        
        # message = await self.format_divergence_message(divergence)
        message = await self.test_message()
        print(group_id)
        try:
            await self.bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления: {str(e)}")
            return False
        
    async def process_pending_notifications(self) -> int:
        """
        Обрабатывает все ожидающие уведомления о дивергенциях
        
        Возвращает количество успешно отправленных уведомлений
        """
        # Получаем все неотправленные уведомления
        query = select(Divergence).where(Divergence.notification_sent == False)
        result = await self.session.execute(query)
        pending_divergence = result.scalars().all()

        if not pending_divergence:
            return 0
        
        sent_count = 0
        for divergence in pending_divergence:
            success = await self.send_divergence_notification(divergence)
            if success:
                # Отмечаем как отправленное
                divergence.notification_sent = True
                sent_count += 1
        
        # Сохраняем изменения в БД
        await self.session().commit()
        return sent_count()

