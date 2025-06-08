from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models import Admin
from app.config import SUPERADMIN_IDS

class AdminMiddleware(BaseMiddleware):
    """Middleware для проверки прав администратора"""
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id в зависимости от типа события
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            # Для других типов событий просто пропускаем
            return await handler(event, data)

        # Проверяем, является ли пользователь суперадмином
        if user_id in SUPERADMIN_IDS:
            data['is_admin'] = True
            data['is_active'] = True
            return await handler(event, data)

        # Получаем сессию БД
        session: AsyncSession = data.get('session')
        if not session:
            # Если нет сессии, не можем проверить права
            data['is_admin'] = False
            data['is_superadmin'] = False
            return await handler(event, data)

        # Проверяем, есть ли пользователь в базе админов
        query = select(Admin).where(Admin.user_id == user_id)
        result = await session.execute(query)
        admin = result.scalar_one_or_none()

        if admin and admin.is_active:
            data['is_admin'] = True
            data['is_superadmin'] = admin.is_superadmin
        else:
            data['is_admin'] = False
            data['is_superadmin'] = False
        
        return await handler(event, data)