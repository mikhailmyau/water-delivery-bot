"""Состояния сценария оформления заказа."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Пошаговое оформление заказа: город → адрес → дом → подтверждение → оплата."""

    waiting_city = State()
    waiting_address = State()
    waiting_house = State()
    waiting_confirmation = State()
    waiting_payment = State()
