from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Optional

def get_start_kb() -> InlineKeyboardMarkup:
    """Создает клавиатуру для стартового сообщения"""
    kb = InlineKeyboardBuilder()

    kb.button(text='📊 О боте', callback_data='about')
    kb.button(text='🔧 Админ-панель', callback_data='admin_panel')

    kb.adjust(1)

    return kb.as_markup()