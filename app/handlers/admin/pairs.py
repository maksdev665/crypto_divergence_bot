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

    