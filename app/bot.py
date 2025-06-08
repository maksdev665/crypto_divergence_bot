import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import BOT_TOKEN, CHECK_INTERVAL
from app.database.engine import get_session
from app.middlewares.admin_middleware import AdminMiddleware


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


# Функция для запуска бота
async def main():
    from app.handlers import common
    from app.handlers.admin import admin_panel

    # Регистрация общие обработчики
    dp.include_router(common.router)

    # Регистрируем обработчики админ-панели с middleware
    admin_router = admin_panel.router
    admin_router.message.middleware(AdminMiddleware())
    admin_router.callback_query.middleware(AdminMiddleware())
    dp.include_router(admin_router)

    # Регистрируем middleware для сессии БД для всех обработчиков
    dp.update.middleware(AsyncSessionMiddleware(get_session))

    # Устанавливаем комманды бота
    await set_bot_commands()

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