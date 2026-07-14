"""Тесты DeliveryService."""

from __future__ import annotations

import pytest

from app.services.delivery_service import DeliveryService

pytestmark = pytest.mark.asyncio


async def test_free_delivery_above_threshold(session):
    service = DeliveryService(session)
    quote = await service.calculate(160)
    assert quote.is_free is True
    assert quote.price == 0


async def test_paid_delivery_below_threshold(session):
    service = DeliveryService(session)
    await service.update_settings(free_delivery_from_liters=200)
    quote = await service.calculate(160)
    assert quote.is_free is False
    assert quote.price == 50000


async def test_delivery_days_are_configurable(session):
    service = DeliveryService(session)
    await service.update_settings(delivery_days="до 3 дней", express_delivery_days="1 день")
    quote = await service.calculate(120)
    assert quote.standard_days == "до 3 дней"
    assert quote.express_days == "1 день"
