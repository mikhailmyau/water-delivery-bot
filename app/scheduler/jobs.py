"""Периодические задачи. Сейчас — единственная: напоминания о неоплаченных заказах.

Не более двух напоминаний на заказ, интервалы настраиваются через .env
(REMINDER_FIRST_DELAY_MINUTES / REMINDER_SECOND_DELAY_MINUTES) — см. ТЗ, глава
«Неоплаченные заказы».
"""

from __future__ import annotations

import logging
from datetime import timedelta

from aiogram import Bot

from app.config import settings
from app.database.base import utcnow
from app.database.repositories.order_repository import OrderRepository
from app.database.session import get_session
from app.keyboards.user import build_reminder_keyboard
from app.services.notification_service import NotificationService
from app.utils.formatting import format_reminder_message

logger = logging.getLogger("app.scheduler")


async def send_payment_reminders(bot: Bot) -> None:
    """Отправляет первое и второе напоминание тем, чьи заказы всё ещё не оплачены."""
    async with get_session() as session:
        order_repo = OrderRepository(session)
        notification_service = NotificationService(bot)

        first_threshold = utcnow() - timedelta(minutes=settings.reminder_first_delay_minutes)
        first_batch = await order_repo.list_awaiting_first_reminder(first_threshold)
        for order in first_batch:
            if order.user is None or order.user.is_blocked:
                continue
            await notification_service.send_to_user(
                order.user.telegram_id,
                format_reminder_message(second=False),
                build_reminder_keyboard(order.id),
            )
            await order_repo.mark_reminder_sent(order, second=False)
            logger.info("First payment reminder sent: order=%s", order.order_number)

        second_threshold = utcnow() - timedelta(minutes=settings.reminder_second_delay_minutes)
        second_batch = await order_repo.list_awaiting_second_reminder(second_threshold)
        for order in second_batch:
            if order.user is None or order.user.is_blocked:
                continue
            await notification_service.send_to_user(
                order.user.telegram_id,
                format_reminder_message(second=True),
                build_reminder_keyboard(order.id),
            )
            await order_repo.mark_reminder_sent(order, second=True)
            logger.info("Second payment reminder sent: order=%s", order.order_number)

        await session.commit()
