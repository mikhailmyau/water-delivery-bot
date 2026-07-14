"""Состояния административных сценариев."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminPriceStates(StatesGroup):
    """Изменение цены за литр (/price)."""

    waiting_price = State()


class AdminDeliveryStates(StatesGroup):
    """Изменение параметров доставки (/delivery)."""

    waiting_delivery_price = State()
    waiting_free_delivery_from = State()
    waiting_delivery_days = State()
    waiting_express_days = State()


class AdminPromoStates(StatesGroup):
    """Создание промокода (/promo)."""

    waiting_code = State()
    waiting_discount_type = State()
    waiting_discount_value = State()
    waiting_usage_limit = State()
    waiting_expiry_days = State()


class AdminBroadcastStates(StatesGroup):
    """Подготовка рассылки (/broadcast)."""

    waiting_content = State()
    waiting_confirmation = State()
