"""Сервис отправки уведомлений клиентам и администраторам.

Доставка уведомлений — побочный эффект, а не часть транзакции: сбой отправки
(сеть, недоступный Telegram API, блокировка бота) никогда не должен всплыть
наружу и откатить уже совершённые изменения в БД (например, статус оплаты
заказа, выставленный до вызова этого сервиса).
"""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramNotFound, TelegramRetryAfter
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
        """Отправляет сообщение пользователю. Возвращает False, если доставить не удалось."""
        try:
            await self.bot.send_message(telegram_id, text, reply_markup=reply_markup)
            return True
        except TelegramRetryAfter as exc:
            logger.warning("Flood control at sending to %s, retry after %s", telegram_id, exc.retry_after)
        except (TelegramForbiddenError, TelegramNotFound):
            logger.info("User %s is unreachable (blocked bot or deleted account)", telegram_id)
        except TelegramAPIError as exc:
            logger.error("Failed to send message to %s: %s", telegram_id, exc)
        except Exception:  # noqa: BLE001 — доставка уведомления не должна ронять вызывающий код
            logger.exception("Unexpected error while sending message to %s", telegram_id)
        return False

    async def send_to_admin_group(
        self, text: str, reply_markup: InlineKeyboardMarkup | None = None
    ) -> None:
        if settings.admin_group_id is None:
            return
        try:
            await self.bot.send_message(settings.admin_group_id, text, reply_markup=reply_markup)
        except TelegramAPIError as exc:
            logger.error("Failed to notify admin group %s: %s", settings.admin_group_id, exc)
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error while notifying admin group %s", settings.admin_group_id)

    async def send_to_all_admins(self, text: str) -> None:
        for admin_id in settings.admin_ids:
            await self.send_to_user(admin_id, text)
