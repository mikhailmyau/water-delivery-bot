"""Callback-данные главного меню."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="menu"):
    """Навигация из главного меню."""

    action: str
    # "order" | "catalog" | "delivery" | "promo" | "support" | "faq" | "home"
