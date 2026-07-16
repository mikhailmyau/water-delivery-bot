"""Callback-данные выбора города доставки (алфавитный указатель)."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class CityCallback(CallbackData, prefix="city"):
    """Навигация по справочнику городов."""

    action: str
    # "letter"  — value = буква, показать города на неё
    # "pick"    — value = id города из app/data/cities.py
    # "manual"  — перейти на ручной ввод города текстом
    # "letters" — вернуться к алфавиту
    value: str = ""
