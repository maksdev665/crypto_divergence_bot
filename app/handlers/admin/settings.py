from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.settings import BotSettings
from app.keyboards.admin_kb import get_settings_menu_kb, get_back_kb
from app.utils.states import AdminStates
from app.config import DEFAULT_DIVERGENCE_THRESHOLD, CHECK_INTERVAL
import logging


logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == 'bot_settings')
async def cb_bot_settings(callback: CallbackQuery):
    """Настройки бота"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки бота</b>\n\n"
        "Выберите настройку для изменения:",
        reply_markup=get_settings_menu_kb(),
        parse_mode='HTML'
    )
    await callback.answer()


@router.callback_query(F.data == 'set_group_id')
async def cb_set_group_id(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Настройка ID группы для уведомлений"""
    # Получаем текущее значение
    query = select(BotSettings).where(BotSettings.key == 'notification_group_id')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    current_value = 'Не установлено'
    if setting and setting.value:
        current_value = setting.value

    await callback.message.edit_text(
        "📢 <b>Настройка группы для уведомлений</b>\n\n"
        f"Текущее значение: <code>{current_value}</code>\n\n"
        "Пожалуйста, введите ID группы или канала, куда бот будет отправлять уведомления о дивергенциях.\n\n"
        "<i>Важно: Бот должен быть добавлен в группу/канал и иметь права на отправку сообщений.</i>",
        reply_markup=get_back_kb('bot_settings'),
        parse_mode='HTML'
    )
    await state.set_state(AdminStates.set_group_id)
    await callback.answer()


@router.message(StateFilter(AdminStates.set_group_id))
async def process_set_group_id(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода ID группы"""
    group_id = message.text.strip()

    # Проверяем что введено число
    if not group_id.startswith('-100') and not group_id.lstrip('0').isdigit():
        await message.answer(
            '❌ ID группы/канала должен быть числом. Пожалуйста, проверьте и попробуйте снова.',
            reply_markup=get_back_kb('bot_settings')
        )
        return
    
    # Сохраняем настройку
    query = select(BotSettings).where(BotSettings.key == 'notification_group_id')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    if setting is None:
        setting = BotSettings(key='notification_group_id', value=group_id)
        session.add(setting)
    else:
        setting.value = group_id
    
    await session.commit()

    await message.answer(
        f"✅ ID группы для уведомлений успешно установлен: <code>{group_id}</code>",
        reply_markup=get_back_kb('bot_settings'),
        parse_mode='HTML'
    )
    
    await state.clear()


@router.callback_query(F.data == 'set_check_interval')
async def cb_set_check_interval(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Настройка интервала проверки дивергенций"""
    # Получаем текущее значение
    query = select(BotSettings).where(BotSettings.key == 'check_interval')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    current_value = CHECK_INTERVAL
    if setting and setting.value_int:
        current_value = setting.value_int

    # Переводим секунды в минуты для удобство
    current_minutes = current_value // 60

    await callback.message.edit_text(
        "⏱ <b>Настройка интервала проверки</b>\n\n"
        f"Текущее значение: {current_minutes} минут\n\n"
        "Пожалуйста, введите интервал проверки дивергенций в минутах (от 1 до 60):",
        reply_markup=get_back_kb('bot_settings'),
        parse_mode='HTML'
    )
    
    await state.set_state(AdminStates.set_check_interval)
    await callback.answer()


@router.message(StateFilter(AdminStates.set_check_interval))
async def process_set_check_interval(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода интервала проверки"""
    try:
        interval_minutes = int(message.text.strip())
        if interval_minutes < 1 or interval_minutes > 60:
            raise ValueError('Интервал должен быть от 1 до 60 минут')
    except ValueError:
        await message.answer(
            '❌ Пожалуйста, введите целое число от 1 до 60.',
            reply_markup=get_back_kb('bot_settings')
        )
        return
    
    # Переводим минуты в секунды
    interval_seconds = interval_minutes * 60

    # Сохраняем настройку
    query = select(BotSettings).where(BotSettings.key == 'check_interal')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    if setting is None:
        setting = BotSettings(key='check_interval', value_int=interval_seconds)
        session.add(setting)
    else:
        setting.value_int = interval_seconds

    await session.commit()

    await message.answer(
        f"✅ Интервал проверки дивергенций успешно установлен: {interval_minutes} минут",
        reply_markup=get_back_kb('bot_settings')
    )

    await state.clear()


@router.callback_query(F.data == 'set_default_threshold')
async def cb_set_default_threshold(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Настройка порога дивергенции по умолчанию"""
    # Получаем текущее значение
    query = select(BotSettings).where(BotSettings.key == 'default_divergence_threshold')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    current_value = DEFAULT_DIVERGENCE_THRESHOLD
    if setting and setting.value_float:
        current_value = setting.value_float

    await callback.message.edit_text(
        "📊 <b>Настройка порога дивергенции по умолчанию</b>\n\n"
        f"Текущее значение: {current_value}%\n\n"
        "Пожалуйста, введите порог дивергенции по умолчанию в процентах (например, 5.0):",
        reply_markup=get_back_kb('bot_settings'),
        parse_mode='HTML'
    )

    await state.set_state(AdminStates.set_default_threshold)
    await callback.answer()


@router.message(StateFilter(AdminStates.set_default_threshold))
async def process_set_default_threshold(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода порога дивергенции по умолчанию"""
    try:
        threshold = float(message.text.strip().replace(',', '.'))
        if threshold <= 0:
            raise ValueError('Порог должен быть положительным числом')
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите положительное число. Например, 5.0",
            reply_markup=get_back_kb('bot_settings')
        )
        return
    
    # Сохраняем настройку
    query = select(BotSettings).where(BotSettings.key == 'default_divergence_threshold')
    result = await session.execute(query)
    setting = result.scalar_one_or_none()

    if setting is None:
        setting = BotSettings(key='default_divergence_threshold')
        session.add(setting)
    else:
        setting.value_float = threshold
    
    await session.commit()

    await message.answer(
        f"✅ Порог дивергенции по умолчанию успешно установлен: {threshold}%",
        reply_markup=get_back_kb('bot_settings')
    )
    
    await state.clear()

