import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import BOT_TOKEN

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
        BotCommand(command='start', description='Запуск бота')
    ]
    await bot.set_my_commands(commands)


# Функция для запуска бота
async def main():
    from app.handlers import common

    # Регистрация общие обработчики
    dp.include_router(common.router)

    # Устанавливаем комманды бота
    await set_bot_commands()

    # Запуск бота
    await dp.start_polling(bot)