"""Сборка Bot и Dispatcher: middleware, роутеры, хранилище FSM.

bot.py не должен содержать ничего из этого — здесь и только здесь провод
между всеми частями приложения (ТЗ, глава 17).
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database.session import async_session_factory
from app.handlers import router as root_router
from app.middlewares.database import DatabaseMiddleware
from app.middlewares.error_handling import ErrorHandlingMiddleware
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.throttling import CallbackDebounceMiddleware, StartThrottlingMiddleware
from app.middlewares.user_context import UserContextMiddleware


def _create_storage() -> BaseStorage:
    if settings.redis_url:
        from aiogram.fsm.storage.redis import RedisStorage

        return RedisStorage.from_url(settings.redis_url)
    return MemoryStorage()


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher(storage=_create_storage())

    # Порядок важен: каждый следующий middleware оборачивается предыдущим.
    dispatcher.update.outer_middleware(ErrorHandlingMiddleware())
    dispatcher.update.outer_middleware(LoggingMiddleware())
    dispatcher.update.outer_middleware(DatabaseMiddleware(async_session_factory))
    dispatcher.update.outer_middleware(UserContextMiddleware())
    dispatcher.update.outer_middleware(StartThrottlingMiddleware())
    dispatcher.update.outer_middleware(CallbackDebounceMiddleware())

    dispatcher.include_router(root_router)
    return dispatcher
