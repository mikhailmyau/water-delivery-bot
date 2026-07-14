"""Создание и настройка APScheduler."""

from __future__ import annotations

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.scheduler.jobs import send_payment_reminders

_REMINDER_CHECK_INTERVAL_MINUTES = 5


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
    return scheduler
