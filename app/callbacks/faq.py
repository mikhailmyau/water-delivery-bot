"""Callback-данные раздела FAQ."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class FaqCallback(CallbackData, prefix="faq"):
    """Открытие ответа на конкретный вопрос или возврат к списку."""

    action: str
    # "open" | "back"
    question_id: int = 0
