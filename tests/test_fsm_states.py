"""Тесты FSM: состояния существуют, уникальны и идут в ожидаемом порядке."""

from __future__ import annotations

from app.states.admin_states import AdminPriceStates
from app.states.order_states import OrderStates


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


def test_admin_price_states():
    names = [state.state.split(":")[-1] for state in AdminPriceStates.__all_states__]
    assert names == ["waiting_price"]
