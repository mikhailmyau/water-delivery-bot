"""Сервис массовой рассылки сообщений пользователям."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound, TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger("app.broadcast")

_BROADCAST_CHUNK_SIZE = 25
_BROADCAST_CHUNK_DELAY_SECONDS = 1.0


class BroadcastContentType(str, Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    ANIMATION = "animation"
    DOCUMENT = "document"


@dataclass(frozen=True, slots=True)
class BroadcastContent:
    """Содержимое рассылки: текст и, опционально, file_id медиа."""

    content_type: BroadcastContentType
    text: str | None
    file_id: str | None


@dataclass(slots=True)
class BroadcastResult:
    sent: int = 0
    blocked: int = 0
    failed: int = 0


class BroadcastService:
    """Отправляет содержимое рассылки всем активным пользователям пачками, без спама и флуда."""

    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        self.bot = bot
        self.user_repo = UserRepository(session)

    async def send(self, content: BroadcastContent) -> BroadcastResult:
        telegram_ids = await self.user_repo.list_active_telegram_ids()
        result = BroadcastResult()

        for start in range(0, len(telegram_ids), _BROADCAST_CHUNK_SIZE):
            chunk = telegram_ids[start : start + _BROADCAST_CHUNK_SIZE]
            await asyncio.gather(
                *(self._send_one(telegram_id, content, result) for telegram_id in chunk)
            )
            await asyncio.sleep(_BROADCAST_CHUNK_DELAY_SECONDS)

        return result

    async def _send_one(
        self, telegram_id: int, content: BroadcastContent, result: BroadcastResult
    ) -> None:
        try:
            await self._dispatch(telegram_id, content)
            result.sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await self._dispatch(telegram_id, content)
                result.sent += 1
            except (
                Exception
            ):  # noqa: BLE001 — рассылка не должна прерываться из-за одного получателя
                result.failed += 1
        except (TelegramForbiddenError, TelegramNotFound):
            await self.user_repo.mark_blocked(telegram_id, True)
            result.blocked += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("Broadcast to %s failed: %s", telegram_id, exc)
            result.failed += 1

    async def _dispatch(self, telegram_id: int, content: BroadcastContent) -> None:
        if content.content_type == BroadcastContentType.TEXT:
            await self.bot.send_message(telegram_id, content.text or "")
            return

        # Для всех остальных типов file_id всегда заполнен — см. handlers/admin/broadcast.py.
        file_id = content.file_id
        assert file_id is not None
        if content.content_type == BroadcastContentType.PHOTO:
            await self.bot.send_photo(telegram_id, file_id, caption=content.text)
        elif content.content_type == BroadcastContentType.VIDEO:
            await self.bot.send_video(telegram_id, file_id, caption=content.text)
        elif content.content_type == BroadcastContentType.ANIMATION:
            await self.bot.send_animation(telegram_id, file_id, caption=content.text)
        elif content.content_type == BroadcastContentType.DOCUMENT:
            await self.bot.send_document(telegram_id, file_id, caption=content.text)
