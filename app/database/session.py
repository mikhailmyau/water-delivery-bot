"""Создание асинхронного движка SQLAlchemy и фабрики сессий."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database.base import Base

_connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=_connect_args,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def init_models() -> None:
    """Создаёт таблицы, если их ещё нет (используется вне Alembic, например в тестах)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Контекстный менеджер сессии для использования вне middleware (сервисы, планировщик)."""
    async with async_session_factory() as session:
        yield session
