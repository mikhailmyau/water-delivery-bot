"""Работа с денежными суммами. Все суммы в проекте хранятся в целых копейках."""

from __future__ import annotations


def kopecks_to_rubles_str(kopecks: int) -> str:
    """Форматирует копейки в рубли для отображения пользователю, например 1248050 -> '12 480,50'."""
    rubles, remainder = divmod(abs(kopecks), 100)
    sign = "-" if kopecks < 0 else ""
    formatted_rubles = f"{rubles:,}".replace(",", " ")
    if remainder:
        return f"{sign}{formatted_rubles},{remainder:02d}"
    return f"{sign}{formatted_rubles}"


def format_price(kopecks: int) -> str:
    """Форматирует сумму с символом рубля, например 1248000 -> '12 480 ₽'."""
    return f"{kopecks_to_rubles_str(kopecks)} ₽"


def rubles_to_kopecks(rubles: float) -> int:
    """Переводит введённое администратором значение в рублях в целые копейки."""
    return round(rubles * 100)
