"""Тесты FSM: состояния существуют, уникальны и идут в ожидаемом порядке."""

from __future__ import annotations

from app.states.admin_states import AdminDeliveryStates, AdminPriceStates, AdminPromoStates
from app.states.order_states import OrderStates
from app.states.promo_states import PromoStates


def test_order_states_sequence():
    expected = [
        "waiting_city",
        "waiting_address",
        "waiting_house",
        "waiting_confirmation",
        "waiting_payment",
    ]
    names = [state.state.split(":")[-1] for state in OrderStates.__all_states__]
    assert names == expected


def test_order_states_are_unique():
    values = [state.state for state in OrderStates.__all_states__]
    assert len(values) == len(set(values))


def test_promo_states_has_waiting_code():
    names = [state.state.split(":")[-1] for state in PromoStates.__all_states__]
    assert names == ["waiting_code"]


def test_admin_price_states():
    names = [state.state.split(":")[-1] for state in AdminPriceStates.__all_states__]
    assert names == ["waiting_price"]


def test_admin_delivery_states_cover_all_parameters():
    names = {state.state.split(":")[-1] for state in AdminDeliveryStates.__all_states__}
    assert names == {
        "waiting_delivery_price",
        "waiting_free_delivery_from",
        "waiting_delivery_days",
        "waiting_express_days",
    }


def test_admin_promo_states_sequence():
    expected = [
        "waiting_code",
        "waiting_discount_type",
        "waiting_discount_value",
        "waiting_usage_limit",
        "waiting_expiry_days",
    ]
    names = [state.state.split(":")[-1] for state in AdminPromoStates.__all_states__]
    assert names == expected
