import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import BOT_TOKEN, CHECK_INTERVAL
from app.database.engine import get_session
from app.database.models import BotSettings
from app.middlewares.admin_middleware import AdminMiddleware
from app.services.binance_api import BinanceAPI
from app.services.divergence import DivergenceAnalyzer
from app.services.notifications import NotificationService




# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создадим экземпляр бота
bot = Bot(token=BOT_TOKEN)

# Создадим диспетчер с хранилищем состояний
dp = Dispatcher(storage=MemoryStorage())

# Задаем команды бота
async def set_bot_commands():
    commands = [
        BotCommand(command='start', description='Запуск бота'),
        BotCommand(command='help', description='Помощь'),
        BotCommand(command='admin', description='Панель администратора')
    ]
    await bot.set_my_commands(commands)


async def check_divergence_task():
    """Фоновая задача для проверки дивергенций между валютными парами"""
    logger.info('Запуск фоновой задачи проверки дивергенций')

    while True:
        try:
            # Создаем новую сессию для каждой итерации
            async for session in get_session():
                # Получаем текущий интервал проверки из настроек
                query = select(BotSettings).where(BotSettings.key == 'check_interval')
                result = await session.execute(query)
                setting = result.scalar_one_or_none()

                interval = CHECK_INTERVAL
                if setting and setting.value_int:
                    interval = setting.value_int

                # Проверяем статус бота
                status_query = select(BotSettings).where(BotSettings.key == 'bot_active')
                status_result = await session.execute(status_query)
                status_setting = status_result.scalar_one_or_none()

                is_active = True
                if status_setting is not None and status_setting.value_bool is not None:
                    is_active = status_setting.value_bool
                
                if not is_active:
                    logger.info('Бот не активен, пропускаем проверку дивергенций')
                    break

                # Создаем сервисы
                binance_api = BinanceAPI()
                divergence_analyzer = DivergenceAnalyzer(session, binance_api)
                notification_service = NotificationService(bot, session)

                # Проверяем дивергенции
                logger.info('Проверка дивергенций...')
                divergences = await divergence_analyzer.check_all_pairs()

                if divergences:
                    logger.info(f"Обнаружено {len(divergences)} дивергенций")
                    # Отправляем уведомления
                    for divergence in divergences:
                        success = await notification_service.send_divergence_notificaton(divergence)
                        if success:
                            await divergence_analyzer.mark_as_notified(divergence.id)
                else:
                    logger.info('Дивергенций не обнаружено')
            
                logger.info(f"Следующая проверка через {interval} секунд")
                break
                
        except Exception as e:
            logger.error(f"Ошибка при проверке дивергенций: {str(e)}")

        await asyncio.sleep(interval)

# Функция для запуска бота
async def main():
    from app.handlers import common
    from app.handlers.admin import admin_panel, pairs, settings

    # Регистрация общие обработчики
    dp.include_router(common.router)

    # Регистрируем обработчики админ-панели с middleware
    admin_router = admin_panel.router
    admin_router.message.middleware(AdminMiddleware())
    admin_router.callback_query.middleware(AdminMiddleware())
    dp.include_router(admin_router)

    # Регистрируем остальные обработчики админ-панели
    pairs_router = pairs.router
    pairs_router.message.middleware(AdminMiddleware())
    pairs_router.callback_query.middleware(AdminMiddleware())
    dp.include_router(pairs_router)

    settings_router = settings.router
    settings_router.message.middleware(AdminMiddleware())
    settings_router.callback_query.middleware(AdminMiddleware())
    dp.include_router(settings_router)

    # Регистрируем middleware для сессии БД для всех обработчиков
    dp.update.middleware(AsyncSessionMiddleware(get_session))

    # Устанавливаем комманды бота
    await set_bot_commands()

    # Запускаем фоновую задачу проверки дивергенций
    asyncio.create_task(check_divergence_task())

    # Запуск бота
    await dp.start_polling(bot)


# Middleware для внедрения сессии БД
class AsyncSessionMiddleware:
    def __init__(self, session_pool):
        self.session_pool = session_pool
    
    async def __call__(self, handler, event, data):
        async for session in self.session_pool():
            data['session'] = session
            return await handler(event, data)