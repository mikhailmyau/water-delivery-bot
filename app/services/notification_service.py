"""Сервис отправки уведомлений клиентам и администраторам."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup

from app.config import settings

logger = logging.getLogger("app.notifications")


class NotificationService:
    """Единая точка отправки сообщений через Telegram Bot API."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_to_user(
        self,
        telegram_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> bool:
        """Отправляет сообщение пользователю. Возвращает False, если пользователь заблокировал бота."""
        try:
            await self.bot.send_message(telegram_id, text, reply_markup=reply_markup)
            return True
        except TelegramRetryAfter as exc:
            logger.warning("Flood control at sending to %s, retry after %s", telegram_id, exc.retry_after)
            return False
        except (TelegramForbiddenError, TelegramNotFound):
            logger.info("User %s is unreachable (blocked bot or deleted account)", telegram_id)
            return False

    async def send_to_admin_group(
        self, text: str, reply_markup: InlineKeyboardMarkup | None = None
    ) -> None:
        if settings.admin_group_id is None:
            return
        try:
            await self.bot.send_message(settings.admin_group_id, text, reply_markup=reply_markup)
        except (TelegramForbiddenError, TelegramNotFound) as exc:
            logger.error("Failed to notify admin group %s: %s", settings.admin_group_id, exc)

    async def send_to_all_admins(self, text: str) -> None:
        for admin_id in settings.admin_ids:
            await self.send_to_user(admin_id, text)
