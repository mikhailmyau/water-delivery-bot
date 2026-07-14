"""Общие фикстуры тестов.

Переменные окружения выставляются до первого импорта app.config, иначе
pydantic-settings упадёт из-за отсутствующего BOT_TOKEN.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "000000:TEST-TOKEN")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ADMIN_IDS", "1")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
from app.services.settings_service import SettingsService


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as db_session:
        yield db_session
    await engine.dispose()


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    SettingsService.invalidate_cache()
    yield
    SettingsService.invalidate_cache()
