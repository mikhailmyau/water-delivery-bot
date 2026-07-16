"""Тесты PriceService: у каждого из трёх видов воды своя независимая цена."""

from __future__ import annotations

import pytest

from app.database.models.water_type import WaterType
from app.services.price_service import PriceService

pytestmark = pytest.mark.asyncio


async def test_default_prices(session):
    service = PriceService(session)
    assert await service.get_price_per_liter(WaterType.SLM) == 7700
    assert await service.get_price_per_liter(WaterType.SRM) == 10000
    assert await service.get_price_per_liter(WaterType.GAZ) == 8000


async def test_calculate_product_price(session):
    service = PriceService(session)
    assert await service.calculate_product_price(WaterType.SLM, 160) == 7700 * 160


async def test_set_price_per_liter_applies_immediately_and_only_to_that_type(session):
    service = PriceService(session)
    await service.set_price_per_liter(WaterType.SLM, 8000)
    assert await service.get_price_per_liter(WaterType.SLM) == 8000
    # Цены других видов воды не затронуты.
    assert await service.get_price_per_liter(WaterType.SRM) == 10000
    assert await service.get_price_per_liter(WaterType.GAZ) == 8000


async def test_get_all_prices_returns_all_three_types(session):
    service = PriceService(session)
    prices = await service.get_all_prices()
    assert set(prices) == {WaterType.SLM, WaterType.SRM, WaterType.GAZ}
