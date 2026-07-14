"""Тесты слоя репозиториев на in-memory SQLite."""

from __future__ import annotations

import pytest

from app.database.models.order import PaymentStatus
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.user_repository import UserRepository
from app.services.order_service import OrderService

pytestmark = pytest.mark.asyncio


async def test_user_repository_get_or_create(session):
    repo = UserRepository(session)
    assert await repo.get_by_telegram_id(555) is None

    user = await repo.create(555, "name", "First", "Last", "ru", False)
    await session.commit()

    found = await repo.get_by_telegram_id(555)
    assert found is not None
    assert found.id == user.id


async def test_order_repository_list_unpaid(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(777, "n", "N", None, "ru", False)
    await session.flush()

    order_service = OrderService(session)
    order = await order_service.create_order(user, "Москва", "Тверская", "1", 120, None)
    await session.commit()

    order_repo = OrderRepository(session)
    unpaid = await order_repo.list_unpaid()
    assert any(o.id == order.id for o in unpaid)

    await order_repo.set_payment_status(order, PaymentStatus.SUCCESS)
    await session.commit()

    unpaid_after = await order_repo.list_unpaid()
    assert all(o.id != order.id for o in unpaid_after)


async def test_order_repository_get_by_number(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(888, "n2", "N2", None, "ru", False)
    await session.flush()

    order_service = OrderService(session)
    order = await order_service.create_order(user, "Казань", "Баумана", "1", 120, None)
    await session.commit()

    order_repo = OrderRepository(session)
    found = await order_repo.get_by_number(order.order_number)
    assert found is not None
    assert found.id == order.id
