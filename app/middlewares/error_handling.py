"""Глобальный перехват исключений: ни одна ошибка не должна «уронить» бота.

Пользователь получает дружелюбное сообщение без технических подробностей,
а сама ошибка полностью логируется (ТЗ, глава 24).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

logger = logging.getLogger("app.errors")

_USER_FRIENDLY_MESSAGE = "Что-то пошло не так. Попробуйте ещё раз."


class ErrorHandlingMiddleware(BaseMiddleware):
    """Оборачивает обработку апдейта: логирует исключение и отвечает пользователю."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Unhandled exception while processing update")
            await self._notify_user(event)
            return None

    @staticmethod
    async def _notify_user(event: TelegramObject) -> None:
        try:
            if isinstance(event, CallbackQuery):
                await event.answer(_USER_FRIENDLY_MESSAGE, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(_USER_FRIENDLY_MESSAGE)
        except (
            Exception
        ):  # noqa: BLE001 — уведомление лучшее усилие, не должно плодить новые ошибки
            logger.warning("Failed to notify user about handled error", exc_info=True)
