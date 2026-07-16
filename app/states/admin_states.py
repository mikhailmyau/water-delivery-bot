"""Состояния административных сценариев."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminPriceStates(StatesGroup):
    """Изменение цены за литр для одного из трёх видов воды (/price).

    Какой именно вид воды сейчас редактируется, хранится не в отдельном
    состоянии, а в FSM-данных (`editing_water_type`) — состояние одно и то же
    независимо от того, какую из трёх цен меняет администратор.
    """

    waiting_price = State()


class AdminBroadcastStates(StatesGroup):
    """Подготовка рассылки (/broadcast)."""

    waiting_content = State()
    waiting_confirmation = State()


class AdminOrderStates(StatesGroup):
    """Поиск заказа и отправка сообщения клиенту из карточки заказа."""

    waiting_search_number = State()
    waiting_client_message = State()
