"""Тесты OrderService: расчёт и создание заказа."""

from __future__ import annotations

import pytest

from app.database.models.order import PaymentStatus
from app.database.models.promo_code import DiscountType
from app.database.repositories.promo_code_repository import PromoCodeRepository
from app.database.repositories.user_repository import UserRepository
from app.services.order_service import OrderService

pytestmark = pytest.mark.asyncio


async def test_calculate_matches_spec_example(session):
    # ТЗ, глава 9: 160 литров, 78 ₽/л, бесплатная доставка -> 12480 ₽.
    service = OrderService(session)
    calculation = await service.calculate(160)
    assert calculation.price_per_liter == 7800
    assert calculation.product_price == 1_248_000
    assert calculation.is_free_delivery is True
    assert calculation.total_price == 1_248_000


async def test_create_order_generates_zero_padded_number(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(111, "u", "U", None, "ru", False)
    await session.flush()

    service = OrderService(session)
    order = await service.create_order(user, "Москва", "Ленина", "1", 120, None)
    await session.commit()

    assert order.order_number == f"{order.id:06d}"
    assert order.payment_status == PaymentStatus.NEW
    assert user.orders_count == 1


async def test_create_order_applies_promo_discount(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(222, "u2", "U2", None, "ru", False)
    promo = await PromoCodeRepository(session).create(
        "SALE10", DiscountType.PERCENT, 10, None, None
    )
    await session.flush()

    service = OrderService(session)
    order = await service.create_order(user, "СПб", "Невский", "1", 120, promo)
    await session.commit()

    expected_product_price = 7800 * 120
    expected_discount = expected_product_price // 10
    assert order.discount == expected_discount
    assert order.total_price == expected_product_price - expected_discount


async def test_cancel_order_marks_failed_and_cancelled(session):
    user_repo = UserRepository(session)
    user = await user_repo.create(333, "u3", "U3", None, "ru", False)
    await session.flush()

    service = OrderService(session)
    order = await service.create_order(user, "Казань", "Баумана", "5", 120, None)
    await service.cancel_order(order)
    await session.commit()

    assert order.payment_status == PaymentStatus.FAILED
    assert order.delivery_status.value == "cancelled"
