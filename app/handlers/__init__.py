"""Регистрация всех роутеров проекта."""

from aiogram import Router

from app.handlers import admin, catalog, faq, order, payment, profile, promo, start, support

router = Router(name="root")
# Админский роутер подключается первым: у него собственный фильтр IsAdmin,
# поэтому обычные пользователи в его хендлеры никогда не попадают.
router.include_router(admin.router)
router.include_router(start.router)
router.include_router(catalog.router)
router.include_router(order.router)
router.include_router(payment.router)
router.include_router(promo.router)
router.include_router(faq.router)
router.include_router(support.router)
router.include_router(profile.router)

__all__ = ["router"]
