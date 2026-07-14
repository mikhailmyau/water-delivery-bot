"""Точка входа приложения.

Содержит только инициализацию, регистрацию (через loader.py), запуск polling
и корректное завершение работы — никакой бизнес-логики (ТЗ, глава 17).
"""

from __future__ import annotations

import asyncio
import logging

from aiohttp import web

from app.config import settings
from app.loader import create_bot, create_dispatcher
from app.logging_config import configure_logging
from app.scheduler.scheduler import create_scheduler
from app.webhook_server import create_webhook_app

logger = logging.getLogger("app.bot")


async def _start_webhook_server(bot) -> web.AppRunner:
    app = create_webhook_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.payment_webhook_host, settings.payment_webhook_port)
    await site.start()
    logger.info(
        "Payment webhook server started on %s:%s",
        settings.payment_webhook_host,
        settings.payment_webhook_port,
    )
    return runner


async def main() -> None:
    configure_logging()
    logger.info(
        "Starting water delivery bot (debug=%s, payment_provider=%s)",
        settings.debug,
        settings.payment_provider,
    )

    bot = create_bot()
    dispatcher = create_dispatcher()

    webhook_runner = await _start_webhook_server(bot)
    scheduler = create_scheduler(bot)
    scheduler.start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await webhook_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
