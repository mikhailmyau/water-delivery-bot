"""Middleware сквозного логирования всех апдейтов."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger("app.updates")


class LoggingMiddleware(BaseMiddleware):
    """Логирует каждое входящее действие пользователя и результат его обработки."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        description = self._describe(event)
        try:
            result = await handler(event, data)
        except Exception:
            logger.exception("%s -> FAILED", description)
            raise
        logger.info("%s -> OK", description)
        return result

    @staticmethod
    def _describe(event: TelegramObject) -> str:
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else "unknown"
            return f"user={user_id} message={event.text!r}"
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else "unknown"
            return f"user={user_id} callback={event.data!r}"
        return f"event={type(event).__name__}"
