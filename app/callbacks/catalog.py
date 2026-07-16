"""Callback-данные выбора вида воды и количества бутылей."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class WaterTypeCallback(CallbackData, prefix="wt"):
    """Выбор вида воды на первом шаге заказа."""

    code: str
    # значение WaterType: "slm" | "srm" | "gaz"


class BottleCallback(CallbackData, prefix="btl"):
    """Счётчик количества бутылей (по 20 л) на карточке-калькуляторе."""

    action: str
    # "inc" | "dec" | "continue" | "back"
