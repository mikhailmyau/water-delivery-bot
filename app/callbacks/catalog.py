"""Callback-данные выбора вида воды и объёма."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class WaterTypeCallback(CallbackData, prefix="wt"):
    """Выбор вида воды на первом шаге заказа."""

    code: str
    # значение WaterType: "slm" | "srm" | "vsm" | "gaz"


class VolumeCallback(CallbackData, prefix="vol"):
    """Выбор объёма заказа в литрах (готовое значение, не ввод)."""

    liters: int


class CatalogCallback(CallbackData, prefix="cat"):
    """Действия на экране каталога/калькулятора."""

    action: str
    # "continue" | "back"
