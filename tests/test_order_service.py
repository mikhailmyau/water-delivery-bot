"""Тесты OrderService: расчёт и создание заказа (без промокодов и платной доставки)."""

from __future__ import annotations

import pytest

from app.database.models.order import PaymentStatus
from app.database.models.water_type import WaterType
from app.database.repositories.user_repository import UserRepository
from app.services.order_service import OrderService

pytestmark = pytest.mark.asyncio


async def test_calculate_matches_default_slm_price(session):
    # 8 бутылей (160 л) СЛМ по умолчанию 77 ₽/л -> 12 320 ₽, доставка включена.
    service = OrderService(session)
    calculation = await service.calculate(WaterType.SLM, 8)
    assert calculation.volume == 160
    assert calculation.price_per_liter == 7700
    assert calculation.total_price == 7700 * 160


async def test_calculate_uses_price_of_selected_type(session):
    service = OrderService(session)
    calculation = await service.calculate(WaterType.SRM, 2)
    assert calculation.volume == 40
    assert calculation.price_per_liter == 10000
    assert calculation.total_price == 10000 * 40


async def test_create_order_generates_zero_padded_number(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(111, "u", "U", None, "ru", False)
    await session.flush()

    service = OrderService(session)
    order = await service.create_order(
        user, "Москва", "Ленина", "1", WaterType.SLM, 6, "до 1 дня", True
    )
    await session.commit()

    assert order.order_number == f"{order.id:06d}"
    assert order.payment_status == PaymentStatus.NEW
    assert order.volume == 120
    assert order.bottles == 6
    assert order.delivery_days_estimate == "до 1 дня"
    assert order.city_matched is True
    assert user.orders_count == 1


async def test_create_order_with_unmatched_city_flags_it(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(444, "u4", "U4", None, "ru", False)
    await session.flush()

    service = OrderService(session)
    order = await service.create_order(
        user, "Мой посёлок", "Центральная", "1", WaterType.GAZ, 2, "до 5 дней", False
    )
    await session.commit()

    assert order.city_matched is False
    assert order.delivery_days_estimate == "до 5 дней"


async def test_cancel_order_marks_failed_and_cancelled(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(333, "u3", "U3", None, "ru", False)
    await session.flush()

    service = OrderService(session)
    order = await service.create_order(
        user, "Казань", "Баумана", "5", WaterType.SLM, 6, "до 3 дней", True
    )
    await service.cancel_order(order)
    await session.commit()

    assert order.payment_status == PaymentStatus.FAILED
    assert order.delivery_status.value == "cancelled"
