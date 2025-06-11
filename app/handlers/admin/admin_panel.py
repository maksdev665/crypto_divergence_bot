import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models import Admin, CurrencyPair, BotSettings, Divergence
from app.keyboards.admin_kb import (
    get_admin_main_menu,
    get_bot_control_kb,
    get_pairs_menu_kb,
    get_settings_menu_kb,
    get_back_kb
)
from app.config import SUPERADMIN_IDS

logger = logging.getLogger(__name__)

router = Router()

async def process_admin_panel(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    
    # Проверяем пользователя на администратов
    query = select(Admin).where(Admin.user_id == user_id)
    result = await session.execute(query) # type: ignore
    admin = result.scalar_one_or_none()
    
    # Если пользователь не админ, но он в списке суперадминов, добавляем его
    if admin is None and user_id in SUPERADMIN_IDS:
        admin = Admin(
            user_id=user_id,
            username=message.from_user.username,
            is_superadmin=True,
            is_active=True
        )
        session.add(admin)
        await session.commit()

        await message.answer(
            "👋 Добро пожаловать в админ-панель! Вы добавлены как суперадмин."
        )
    elif admin is None:
        await message.answer('⛔ У вас нет доступа к админ-панели.')
        return 
    elif not admin.is_active:
        await message.answer('⛔ Ваш аккаунт администратора деактивирован.')
        return
    else:
        await message.answer('👋 Добро пожаловать в админ-панель!')
    
    # Отправляем главное меню
    await show_admin_main_menu(message)


@router.message(Command('admin'))
async def cmd_admin(message: Message, session: AsyncSession):
    await process_admin_panel(message, session)

async def show_admin_main_menu(message: Message):
    """Показывает главное меню админ-панели"""
    await message.answer(
        '🔧 <b>Панель управления ботом</b>\n\n Выберите раздел:',
        reply_markup=get_admin_main_menu(),
        parse_mode='HTML'
    )

@router.callback_query(F.data == 'admin_main_menu')
async def cb_admin_main_menu(callback: CallbackQuery):
    """Обработка нажатия на кнопку возврата в главное меню"""
    await callback.message.edit_text(
        '🔧 <b>Панель управления ботом</b>\n\n Выберите раздел:',
        reply_markup=get_admin_main_menu(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == 'bot_control')
async def cb_bot_control(callback: CallbackQuery, session: AsyncSession):
    """Управление состоянием бота (вкл/выкл)"""
    # Получаем текущий статус бота
    query = select(BotSettings).where(BotSettings.key == 'bot_active')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    is_active = True # По умолчанию бот активен
    if setting is not None and setting.value_bool is not None:
        is_active = setting.value_bool

    status_text = '🟢 Активен' if is_active else '🔴 Остановлен'

    await callback.message.edit_text(
        f"⚙️ <b>Управление ботом</b>\n\n"
        f"Текущий статус: {status_text}\n\n"
        "Выберите действие:",
        reply_markup=get_bot_control_kb(is_active),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == 'bot_activate')
async def cb_bot_active(callback: CallbackQuery, session: AsyncSession):
    """Активация бота"""
    # Получаем текущую настройку
    query = select(BotSettings).where(BotSettings.key == 'bot_active')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    if setting is None:
        # Создаем настройку, если она не существует
        setting = BotSettings(key='bot_active', value_bool=True)
        session.add(setting)
    else:
        setting.value_bool = True

    await session.commit()

    await callback.message.edit_text(
        "⚙️ <b>Управление ботом</b>\n\n"
        "Текущий статус: 🟢 Активен\n\n"
        "Бот успешно активирован и будет отправлять уведомления о дивергенциях.",
        reply_markup=get_bot_control_kb(True),
        parse_mode='HTML'
    )
    await callback.answer('✅ Бот активирован')

@router.callback_query(F.data == 'bot_deactivate')
async def cb_bot_deactivate(callback: CallbackQuery, session: AsyncSession):
    """Деактивация бота"""
    # Получаем текущую настройку
    query = select(BotSettings).where(BotSettings.key == 'bot_active')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    if setting is None:
        # Создаем настройку, если она не существует
        setting = BotSettings(key='bot_active', value_bool=False)
        session.add(setting)
    else:
        setting.value_bool = False

    await session.commit()

    await callback.message.edit_text(
        "⚙️ <b>Управление ботом</b>\n\n"
        "Текущий статус: 🔴 Остановлен\n\n"
        "Бот остановлен и не будет отправлять уведомления о дивергенциях.",
        reply_markup=get_bot_control_kb(False),
        parse_mode='HTML'
    )
    await callback.answer('✅ Бот остановлен')

@router.callback_query(F.data == 'show_stats')
async def cb_show_stats(callback: CallbackQuery, session: AsyncSession):
    """Показать статистику бота"""
    # Получаем количество активных пар
    pairs_query = select(CurrencyPair).where(CurrencyPair.is_active == True)
    pairs_result = await session.execute(pairs_query)
    active_pairs_count = len(pairs_result.scalars().all())

    # Получаем общее количество пар
    all_pairs_query = select(CurrencyPair)
    all_pairs_result = await session.execute(all_pairs_query)
    all_pairs_count = len(all_pairs_result.scalars().all())

    # Получаем количество обнаруженных дивергенций
    divergence_query = select(Divergence)
    divergence_result = await session.execute(divergence_query)
    divergence_count = len(divergence_result.scalars().all())

    # Получаем статус бота
    status_query = select(BotSettings).where(BotSettings.key == 'bot_active')
    status_result = await session.execute(status_query)
    status_setting = status_result.scalar_one_or_none()

    is_active = True
    if status_setting is not None and status_setting.value_bool is not None:
        is_active = status_setting.value_bool

    status_text = "🟢 Активен" if is_active else "🔴 Остановлен"

    stats_message = (
        "📊 <b>Статистика бота</b>\n\n"
        f"Статус бота: {status_text}\n"
        f"Активных валютных пар: {active_pairs_count}/{all_pairs_count}\n"
        f"Обнаружено дивергенций: {divergence_count}\n\n"
    )

    await callback.message.edit_text(
        stats_message,
        reply_markup=get_back_kb('admin_main_menu'),
        parse_mode='HTML'
    )
    await callback.answer()