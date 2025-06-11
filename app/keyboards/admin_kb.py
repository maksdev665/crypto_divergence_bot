from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Union, Dict, Optional
from app.database.models import CurrencyPair

def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Создает главное меню админ-панели"""
    kb = InlineKeyboardBuilder()

    kb.button(text='🤖 Управление ботом', callback_data='bot_control')
    kb.button(text='📊 Управление валютными парами', callback_data='pairs_management')
    kb.button(text='⚙️ Настройки', callback_data='bot_settings')
    kb.button(text='📈 Статистика', callback_data='show_stats')

    # Располагаем кнопки в столбик
    kb.adjust(1)

    return kb.as_markup()


def get_bot_control_kb(is_active: bool) -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления ботом"""
    kb = InlineKeyboardBuilder()

    if is_active:
        kb.button(text='🔴 Остановить бота', callback_data='bot_deactivate')
    else:
        kb.button(text='🟢 Запустить бота', callback_data='bot_activate')
    
    kb.button(text='📈 Статистика', callback_data='show_stats')
    kb.button(text='🔙 Назад', callback_data='admin_main_menu')

    kb.adjust(1)

    return kb.as_markup()


def get_pairs_menu_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру для меню управления валютными парами"""
    kb = InlineKeyboardBuilder()

    kb.button(text='➕ Добавить валютную пару', callback_data='add_pair')
    kb.button(text='📋 Список валютных пар', callback_data='list_pairs')
    kb.button(text='🔙 Назад', callback_data='admin_main_menu')

    kb.adjust(1)

    return kb.as_markup()


def get_settings_menu_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру для меню настроек"""
    kb = InlineKeyboardBuilder()

    kb.button(text='📢 ID группы для уведомлений', callback_data='set_group_id')
    kb.button(text='⏱ Интервал проверки', callback_data='set_check_interval')
    kb.button(text='📊 Порог дивергенции по умолчанию', callback_data='set_default_threshold')
    kb.button(text='🔙 Назад', callback_data='admin_main_menu')

    kb.adjust(1)

    return kb.as_markup()


def get_back_kb(callback_data: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой 'Назад'"""
    kb = InlineKeyboardBuilder()
    kb.button(text='🔙 Назад', callback_data=callback_data)
    return kb.as_markup()


def get_pairs_list_kb(pairs: List[CurrencyPair]) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком валютных пар"""
    kb = InlineKeyboardBuilder()

    # Сортируем пары: сначала активные, потом неактивные
    sorted_pairs = sorted(pairs, key=lambda p: (not p.is_active, p.symbol))

    for pair in sorted_pairs:
        status_emoji = '🟢' if pair.is_active else '🔴'
        kb.button(
            text=f'{status_emoji} {pair.symbol}',
            callback_data=f'pair_{pair.id}'
        )
    
    kb.button(text='🔙 Назад', callback_data='pairs_management')

    kb.adjust(1)

    return kb.as_markup()


def get_pair_actions_kb(pair_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Создает клавиатуру для действий с валютной парой"""
    kb = InlineKeyboardBuilder()

    # Кнопка активации/деактивации
    if is_active:
        kb.button(text='🔴 Деактивировать', callback_data=f'toggle_pair_{pair_id}')
    else:
        kb.button(text='🟢 Активировать', callback_data=f'toggle_pair_{pair_id}')
    
    kb.button(text='✏️ Изменить порог дивергенции', callback_data=f'edit_threshold_{pair_id}')
    kb.button(text='🗑 Удалить пару', callbakc_data=f'delete_pair_{pair_id}')
    kb.button(text='🔙 Назад', callback_data='list_pair')

    kb.adjust(1)

    return kb.as_markup()


def get_confirm_kb(confirm_callback: str, cancel_callback: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для подтверждения действия"""
    kb = InlineKeyboardBuilder()

    kb.button(text='✅ Да, подтверждаю',callback_data=confirm_callback)
    kb.button(text='❌ Отмена', callback_data=cancel_callback)

    kb.adjust(1)

    return kb.as_markup()

