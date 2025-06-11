import aiohttp
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Tuple, Any
import logging
from app.config import BINANCE_API_KEY, BINANCE_API_SECRET

logger = logging.getLogger(__name__)

class BinanceAPI:
    '''Клас для работы с Binance API'''
    BASE_URL = 'https://api.binance.com'

    def __init__(self, api_key: str = BINANCE_API_KEY, api_secret: str = BINANCE_API_SECRET):
        self.api_key = api_key
        self.api_secret = api_secret

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        signed: bool = False,
        timeout: int = 10
    ) -> Dict:
        '''Выполняет запрос к Binance API'''
        url = f'{self.BASE_URL}{endpoint}'
        headers = {'X-MBX-APIKEY': self.api_key} if self.api_key else {}

        if signed and self.api_secret:
            # Добавляем timestamp для подписание запроса
            if params is None:
                params = {}
            params['timestamp'] = int(time.time() * 1000)
            query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method=method, url=url, params=params, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f' Binance API error: {response.status}, {error_text}')
                        raise Exception(f'Binance API error: {response.status}, {error_text}')
        except Exception as e:
            logger.error(f'Error making request to Binance: {str(e)}')
            raise

    async def get_ticker_price(self, symbol: str) -> Dict:
        '''Получает текущую цену для валютной парой'''
        endpoint = '/api/v3/ticker/price'
        params = {'symbol': symbol}
        return await self._make_request('GET', endpoint, params)
    
    async def get_multiple_ticker_prices(self, symbols: List[str]) -> List[Dict]:
        """Получает текущие цены для нескольких валютных пар"""
        endpoint = "/api/v3/ticker/price"
        result = await self._make_request('GET', endpoint)

        # Фильтруем результаты по запрошенным символам
        if symbols:
            return [item for item in result if item['symbol'] in symbols]
        return result

    async def get_exchange_info(self) -> Dict:
        """Получает информацию о доступных валютных парах"""
        endpoint = "/api/v3/exchangeInfo"
        return await self._make_request('GET', endpoint)
    
    async def get_available_pairs(self) -> List[Dict]:
        """Возвращает список доступных валютных пар"""
        exchange_info = await self.get_exchange_info()
        return exchange_info.get('symbols', [])

    async def validate_pair(self, symbol: str) -> bool:
        """Проверяет существование валютной пары на бирже"""
        try:
            pairs = await self.get_available_pairs()
            return any(pair['symbol'] == symbol for pair in pairs)
        except Exception as e:
            logger.error(f'Error validating pair {symbol}: {str(e)}')
            return False
