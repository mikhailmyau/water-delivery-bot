"""Callback-данные каталога и выбора объёма."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class VolumeCallback(CallbackData, prefix="vol"):
    """Выбор объёма заказа в литрах."""

    liters: int


class CatalogCallback(CallbackData, prefix="cat"):
    """Действия на экране каталога/калькулятора."""

    action: str
    # "continue" | "back"
