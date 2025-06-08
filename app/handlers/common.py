from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from app.keyboards.inline_kb import get_start_kb
from app.handlers.admin.admin_panel import process_admin_panel

router = Router()

@router.message(Command('start'))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
        "Я бот для отслеживания дивергенций между криптовалютными парами.\n\n"
        "🔍 Я анализирую цены на Binance и отправляю уведомления, когда обнаруживаю "
        "значительные расхождения между валютными парами.\n\n"
        "Для управления ботом используйте команду /admin",
        reply_markup=get_start_kb()
    )
    print(message.from_user)

@router.message(Command('help'))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📚 <b>Справка по боту</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Запустить бота\n"
        "/help - Показать справку\n"
        "/admin - Панель администратора\n\n"
        "<b>Что делает этот бот?</b>\n"
        "Бот анализирует цены криптовалютных пар на Binance и отслеживает дивергенции между ними. "
        "Когда расхождение превышает заданный порог, бот отправляет уведомление в настроенную группу.\n\n"
        "<b>Как это работает?</b>\n"
        "1. Админ добавляет валютные пары для отслеживания\n"
        "2. Бот регулярно проверяет цены и рассчитывает дивергенции\n"
        "3. При обнаружении значительных расхождений бот отправляет уведомления\n\n"
        "<b>Доступ к боту</b>\n"
        "Управление ботом доступно только администраторам.",
        parse_mode='HTML'
    )

@router.callback_query(F.data == 'about')
async def cb_about(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "🤖 <b>О боте</b>\n\n"
            "Этот бот разработан для трейдеров, которые хотят отслеживать дивергенции "
            "между различными криптовалютными парами.\n\n"
            "<b>Возможности:</b>\n"
            "• Отслеживание множества валютных пар\n"
            "• Настраиваемые пороги дивергенций\n"
            "• Оповещения в Telegram группу или канал\n"
            "• Гибкие настройки параметров\n"
            "• Удобная админ-панель\n\n"
            "<b>Технологии:</b>\n"
            "• Python 3.10+\n"
            "• aiogram 3.x\n"
            "• SQLAlchemy 2.0\n"
            "• PostgreSQL\n"
            "• Binance API\n\n"
            "Для доступа к управлению ботом используйте команду /admin",
            reply_markup=get_start_kb(),
            parse_mode='HTML'
        )
    except TelegramBadRequest as e:
        if 'message is not modified' in str(e):
            pass
        else:
            raise
    await callback.answer()

@router.callback_query(F.data == 'admin_panel')
async def cb_admin_panel(callback: CallbackQuery, session: AsyncSession):
    """Обработчик кнопки 'Админ-панель'"""
    await callback.message.answer('Переход в панель администратора...')
    await process_admin_panel(callback.from_user, session)
    await callback.answer()