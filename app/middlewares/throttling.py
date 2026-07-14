"""Антифлуд: ограничение частоты /start и защита от повторных нажатий кнопок.

См. ТЗ, главы 61–62. Реализовано в памяти процесса — для одного инстанса бота
этого достаточно; при горизонтальном масштабировании стоит перенести ключи в Redis.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.utils.constants import START_THROTTLE_SECONDS

_CALLBACK_DEBOUNCE_SECONDS = 0.7


class RateLimiter:
    """Простой лимитер вида «не больше N раз за окно W секунд» для одного ключа."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str, limit: int, window_seconds: float) -> bool:
        now = time.monotonic()
        hits = [t for t in self._hits.get(key, []) if now - t < window_seconds]
        if len(hits) >= limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True


class StartThrottlingMiddleware(BaseMiddleware):
    """Не чаще одного /start в секунду от одного пользователя."""

    def __init__(self) -> None:
        self._last_start_at: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            user_id = event.from_user.id if event.from_user else 0
            now = time.monotonic()
            last = self._last_start_at.get(user_id, 0.0)
            if now - last < START_THROTTLE_SECONDS:
                return None
            self._last_start_at[user_id] = now
        return await handler(event, data)


class CallbackDebounceMiddleware(BaseMiddleware):
    """Игнорирует повторный клик по той же inline-кнопке в течение короткого окна.

    Защищает от создания дублей заказов и других действий при двойном нажатии.
    """

    def __init__(self) -> None:
        self._last_click_at: dict[str, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery) and event.data:
            key = f"{event.from_user.id}:{event.data}"
            now = time.monotonic()
            last = self._last_click_at.get(key, 0.0)
            if now - last < _CALLBACK_DEBOUNCE_SECONDS:
                await event.answer()
                return None
            self._last_click_at[key] = now
        return await handler(event, data)
