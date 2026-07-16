"""Callback-данные оформления и оплаты заказа."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class OrderCallback(CallbackData, prefix="ord"):
    """Действия на карточке заказа."""

    action: str
    # "pay" | "edit_address" | "back" | "cancel" | "check_payment"
    order_id: int
