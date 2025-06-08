import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models import Admin, CurrencyPair, BotSettings
from app.keyboards.admin_kb import (
    get_admin_main_menu
)
from app.config import SUPERADMIN_IDS

logger = logging.getLogger(__name__)

router = Router()

async def process_admin_panel(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    print(user_id)
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