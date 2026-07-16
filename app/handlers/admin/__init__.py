"""Регистрация административных роутеров."""

from aiogram import Router

from app.handlers.admin import broadcast, logs, menu, orders, price, stats

router = Router(name="admin")
router.include_router(menu.router)
router.include_router(orders.router)
router.include_router(price.router)
router.include_router(broadcast.router)
router.include_router(stats.router)
router.include_router(logs.router)

__all__ = ["router"]
