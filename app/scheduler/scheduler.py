"""Создание и настройка APScheduler."""

from __future__ import annotations

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.scheduler.jobs import send_first_order_nudges, send_payment_reminders

_REMINDER_CHECK_INTERVAL_MINUTES = 5
# Окно nudge-а — часы, поэтому проверять его можно заметно реже, чем платёжные
# напоминания (которые считаются в минутах).
_FIRST_ORDER_NUDGE_CHECK_INTERVAL_MINUTES = 20


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(
        send_payment_reminders,
        trigger=IntervalTrigger(minutes=_REMINDER_CHECK_INTERVAL_MINUTES),
        kwargs={"bot": bot},
        id="payment_reminders",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        send_first_order_nudges,
        trigger=IntervalTrigger(minutes=_FIRST_ORDER_NUDGE_CHECK_INTERVAL_MINUTES),
        kwargs={"bot": bot},
        id="first_order_nudges",
        replace_existing=True,
        max_instances=1,
    )
    return scheduler
