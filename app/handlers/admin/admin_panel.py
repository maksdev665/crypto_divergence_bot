import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command('start'))
async def cmd_admin(message: Message):
    user_id = message.from_user.id
    
    # Проверяем пользователя на администратов