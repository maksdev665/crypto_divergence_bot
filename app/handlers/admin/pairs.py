import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models import CurrencyPair
from app.keyboards.admin_kb import (
    get_pairs_menu_kb,
    get_back_kb,
    get_pairs_list_kb,
    get_pair_actions_kb,
    get_confirm_kb
)
from app.utils.states import AdminStates
from app.services.binance_api import BinanceAPI

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == 'pairs_management')
async def cb_pairs_management(callback: CallbackQuery):
    """Управление валютными парами"""
    await callback.message.edit_text(
        "📊 <b>Управление валютными парами</b>\n\n"
        "Выберите действие:",
        reply_markup=get_pairs_menu_kb(),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data == 'add_pair')
async def cb_add_pair(callback: CallbackQuery, state: FSMContext):
    """Добавление новой валютной пары"""
    await callback.message.edit_text(
        "📝 <b>Добавление валютной пары</b>\n\n"
        "Введите символ валютной пары в формате BTCUSDT или ETHBTC:",
        reply_markup=get_back_kb('pairs_management'),
        parse_mode='HTML'
    )
    await state.set_state(AdminStates.add_pair_symbol)
    await callback.answer()

@router.message(StateFilter(AdminStates.add_pair_symbol))
async def process_add_pair_symbol(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода символа валютной пары"""
    symbol = message.text.strip().upper()

    # Проверяем, существует ли пара на Binance
    binance_api = BinanceAPI()
    is_valid = await binance_api.validate_pair(symbol)

    if not is_valid:
        await message.answer(
            '❌ Валютная пара не найдена на Binance. Пожалуйста, проверьте символ и попробуйте снова.',
            reply_markup=get_back_kb('pairs_management')
        )
        return

    # Проверяем, не добавлена ли уже эта пара
    query = select(CurrencyPair).where(CurrencyPair.symbol == symbol)
    result = await session.execute(query)
    existing_pair = result.scalar_one_or_none()

    if existing_pair:
        await message.answer(
            f"⚠️ Валютная пара {symbol} уже добавлена в систему.\n\n"
            f"Статус: {'Активна' if existing_pair.is_active else 'Не активна'}\n"
            f"Порог дивергенции: {existing_pair.devergence_threshold}%",
            reply_markup=get_back_kb('pairs_management')
        )
        await state.clear()
        return

    # Определяем базовый и котируемый активы
    # Обычно последние 4 символа - это котируемый актив (USDT, BUSD и т.д.)
    # Но могут быть исключения, поэтому это упрощение
    if len(symbol) <= 4:
        await message.answer(
            '❌ Неверный формат символа. Пожалуйста, введите символ в формате BTCUSDT или ETHBTC.',
            reply_markup=get_back_kb('pairs_management')
        )
        return
    
    quote_asset = symbol[-4:] if symbol[-4:] in ['USDT', 'BUSD', 'USDC'] else symbol[-3:]
    base_asset = symbol[:len(symbol) - len(quote_asset)]

    # Сохраняем данные в состоянии
    await state.update_data(
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset
    )

    await message.answer(
        f"📝 <b>Настройка порога дивергенции для {symbol}</b>\n\n"
        f"Базовый актив: {base_asset}\n"
        f"Котируемый актив: {quote_asset}\n\n"
        "Введите порог дивергенции в процентах (например, 5.0):",
        reply_markup=get_back_kb('pairs_management'),
        parse_mode='HTML'
    )
    
    await state.set_state(AdminStates.add_pair_threshold)

@router.message(StateFilter(AdminStates.add_pair_threshold))
async def process_add_pair_threshold(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода порога дивергенции"""
    try:
        threshold = float(message.text.strip().replace(',', '.'))
        if threshold <= 0:
            raise ValueError('Порог должен быть положительным числом')
    except ValueError:
        await message.answer(
            '❌ Пожалуйста, введите положительное число. Например, 5.0',
            reply_markup=get_back_kb('pairs_management')
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    symbol = data.get('symbol')
    base_asset = data.get('base_asset')
    quote_asset = data.get('quote_asset')

    # Создаем новую валютную пару
    new_pair = CurrencyPair(
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        is_active=True,
        devergence_threshold=threshold
    )

    session.add(new_pair)
    await session.commit()

    await message.answer(
        f"✅ Валютная пара {symbol} успешно добавлена!\n\n"
        f"Базовый актив: {base_asset}\n"
        f"Котируемый актив: {quote_asset}\n"
        f"Порог дивергенции: {threshold}%\n"
        f"Статус: Активна",
        reply_markup=get_back_kb('pairs_management')
    )

    await state.clear()

@router.callback_query(F.data == 'list_pairs')
async def cb_list_pairs(callback: CallbackQuery, session: AsyncSession):
    """Просмотр списка валютных пар"""
    # Получаем все пары из базы
    query = select(CurrencyPair)
    result = await session.execute(query)
    pairs = result.scalars().all()

    if not pairs:
        await callback.message.edit_text(
            "📊 <b>Список валютных пар</b>\n\n"
            "Пока не добавлено ни одной валютной пары.",
            reply_markup=get_back_kb('pairs_management'),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📊 <b>Список валютных пар</b>\n\n"
        "Выберите пару для управления:",
        reply_markup=get_pairs_list_kb(pairs),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data.startswith('pair_'))
async def cb_pair_details(callback: CallbackQuery, session: AsyncSession):
    """Показать детали и действия для выбранной валютной пары"""
    pair_id = int(callback.data.split('_')[1])

    # Получаем информацию о паре
    query = select(CurrencyPair).where(CurrencyPair.id == pair_id)
    result = await session.execute(query)
    pair = result.scalar_one_or_none()

    if not pair:
        await callback.message.exit_text(
            '❌ Валютная пара не найдена.',
            reply_markup=get_back_kb('list_pairs')
        )
        await callback.answer()
        return
    
    status = "🟢 Активна" if pair.is_active else "🔴 Не активна"

    await callback.message.edit_text(
        f"📊 <b>Валютная пара {pair.symbol}</b>\n\n"
        f"Базовый актив: {pair.base_asset}\n"
        f"Котируемый актив: {pair.quote_asset}\n"
        f"Порог дивергенции: {pair.devergence_threshold}%\n"
        f"Статус: {status}\n\n"
        "Выберите действие:",
        reply_markup=get_pair_actions_kb(pair.id, pair.is_active),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data.startswith('toggle_pair_'))
async def cb_toggle_pair(callback: CallbackQuery, session: AsyncSession):
    """Изменить статус активности валютной пары"""
    pair_id = int(callback.data.split('_')[2])

    # Получаем информацию о паре
    query = select(CurrencyPair).where(CurrencyPair.id == pair_id)
    result = await session.execute(query)
    pair = result.scalar_one_or_none()

    if not pair:
        await callback.message.edit(
            '❌ Валютная пара не найдена.',
            reply_markup=get_back_kb('list_pairs')
        )
        await callback.answer()
        return

    # Меняем статус на противоположный
    pair.is_active = not pair.is_active
    await session.commit()

    new_status = "🟢 Активна" if pair.is_active else "🔴 Не активна"
    action_text = "активирована" if pair.is_active else "деактивирована"

    await callback.message.edit_text(
        f"✅ Валютная пара {pair.symbol} успешно {action_text}!\n\n"
        f"Базовый актив: {pair.base_asset}\n"
        f"Котируемый актив: {pair.quote_asset}\n"
        f"Порог дивергенции: {pair.devergence_threshold}%\n"
        f"Статус: {new_status}",
        reply_markup=get_pair_actions_kb(pair.id, pair.is_active),
        parse_mode='HTML'
    )
    await callback.answer(f"✅ Пара {action_text}")

@router.callback_query(F.data.startswith('edit_threshold_'))
async def cb_edit_threshold(callback: CallbackQuery, state: FSMContext):
    """Изменить порог дивергенции для валютной пары"""
    pair_id = int(callback.data.split('_')[2])

    await state.update_data(pair_id=pair_id)
    await state.set_state(AdminStates.edit_threshold)

    await callback.message.edit_text(
        "📝 <b>Изменение порога дивергенции</b>\n\n"
        "Введите новое значение порога в процентах (например, 5.0):",
        reply_markup=get_back_kb(f'pair_{pair_id}'),
        parse_mode='HTML'
    )
    await callback.answer()

@router.message(StateFilter(AdminStates.edit_threshold))
async def process_edit_threshold(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка ввода нового порога дивергенции"""
    try:
        threshold = float(message.text.strip().replace(',', '.'))
        if threshold < 0:
            raise ValueError('Порог должен быть положительным числом')
    except ValueError:
        await message.answer(
            '❌ Пожалуйста, введите положительное число. Например, 5.0',
            reply_markup=get_back_kb('pairs_management')
        )
        return
    
    # Получаем ID пары из состояния
    data = await state.get_data()
    pair_id = data.get('pair_id')

    # Обновляем порог
    query = select(CurrencyPair).where(CurrencyPair.id == pair_id)
    result = await session.execute(query)
    pair = result.scalar_one_or_none()

    if not pair:
        await message.answer(
            '❌ Валютная пара не найдена.',
            reply_markup=get_back_kb('pair_management')
        )
        await state.clear()
        return
    
    pair.devergence_threshold = threshold
    await session.commit()

    status = "🟢 Активна" if pair.is_active else "🔴 Не активна"

    await message.answer(
        f"✅ Порог дивергенции для {pair.symbol} успешно изменен!\n\n"
        f"Базовый актив: {pair.base_asset}\n"
        f"Котируемый актив: {pair.quote_asset}\n"
        f"Новый порог дивергенции: {threshold}%\n"
        f"Статус: {status}",
        reply_markup=get_pair_actions_kb(pair.id, pair.is_active)
    )

    await state.clear()

@router.callback_query(F.data.startswith('delete_pair_'))
async def cb_confirm_delete_pair(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подтверждение удаления валютной пары"""
    pair_id = int(callback.data.split('_')[2])

    # Получаем информацию о паре
    query = select(CurrencyPair).where(CurrencyPair.id == pair_id)
    result = await session.execute(query)
    pair = result.scalar_one_or_none()

    if not pair:
        await callback.message.exit_text(
            '❌ Валютная пара не найдена.',
            reply_markup=get_back_kb('list_pairs')
        )
        await callback.answer()
        return
    
    await state.update_data(pair_id=pair_id, pair_symbol=pair.symbol)

    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Вы уверены, что хотите удалить валютную пару {pair.symbol}?\n\n"
        "Это действие нельзя отменить.",
        reply_markup=get_confirm_kb(f'confirm_delete_{pair_id}', f'pair_{pair_id}'),
        parse_mode='HTML'
    )
    await callback.answer()

@router.callback_query(F.data.startswith('confirm_delete_'))
async def cb_delete_pair(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Удаление валютной пары"""
    pair_id = int(callback.data.split("_")[2])
    
    # Получаем информацию о паре
    query = select(CurrencyPair).where(CurrencyPair.id == pair_id)
    result = await session.execute(query)
    pair = result.scalar_one_or_none()
    
    if not pair:
        await callback.message.edit_text(
            "❌ Валютная пара не найдена.",
            reply_markup=get_back_kb("list_pairs")
        )
        await callback.answer()
        return
    
    pair_symbol = pair.symbol
    
    # Удаляем пару
    await session.delete(pair)
    await session.commit()
    
    await callback.message.edit_text(
        f"✅ Валютная пара {pair_symbol} успешно удалена!",
        reply_markup=get_back_kb("list_pairs")
    )
    await callback.answer("✅ Пара удалена")
    await state.clear()

