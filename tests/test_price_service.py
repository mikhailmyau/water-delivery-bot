"""Тесты PriceService."""

from __future__ import annotations

import pytest

from app.services.price_service import PriceService

pytestmark = pytest.mark.asyncio


async def test_default_price_per_liter(session):
    service = PriceService(session)
    assert await service.get_price_per_liter() == 7800


async def test_calculate_product_price(session):
    service = PriceService(session)
    assert await service.calculate_product_price(160) == 7800 * 160


async def test_set_price_per_liter_applies_immediately(session):
    service = PriceService(session)
    await service.set_price_per_liter(8000)
    assert await service.get_price_per_liter() == 8000
    assert await service.calculate_product_price(120) == 8000 * 120
