from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession, async_sessionmaker
from app.config import POSTGRES_URI
from typing import AsyncGenerator

# Создание асинхронного движка
engine = create_async_engine(POSTGRES_URI, echo=True)

# Асинхронная фабрика сессий (новая форма с SQLAlchemy 2.0)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
 

# Зависимость для FastAPI или просто генератор сессии
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session