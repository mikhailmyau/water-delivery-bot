"""Тесты PromoService."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.database.models.promo_code import DiscountType
from app.database.repositories.promo_code_repository import PromoCodeRepository
from app.services.promo_service import PromoService

pytestmark = pytest.mark.asyncio


async def test_unknown_promo_is_invalid(session):
    service = PromoService(session)
    result = await service.validate("NOPE")
    assert result.is_valid is False


async def test_valid_percent_promo(session):
    repo = PromoCodeRepository(session)
    await repo.create("SAVE10", DiscountType.PERCENT, 10, None, None)
    await session.commit()

    service = PromoService(session)
    result = await service.validate("save10")
    assert result.is_valid is True
    assert service.calculate_discount(result.promo, 10000) == 1000


async def test_fixed_discount_never_exceeds_price(session):
    repo = PromoCodeRepository(session)
    promo = await repo.create("BIG", DiscountType.FIXED, 100_000, None, None)
    await session.commit()

    service = PromoService(session)
    assert service.calculate_discount(promo, 5000) == 5000


async def test_expired_promo_is_invalid(session):
    repo = PromoCodeRepository(session)
    await repo.create("OLD", DiscountType.FIXED, 1000, None, datetime.now(UTC) - timedelta(days=1))
    await session.commit()

    service = PromoService(session)
    result = await service.validate("OLD")
    assert result.is_valid is False


async def test_usage_limit_exhausted(session):
    repo = PromoCodeRepository(session)
    promo = await repo.create("ONE", DiscountType.FIXED, 500, 1, None)
    await repo.increment_usage(promo)
    await session.commit()

    service = PromoService(session)
    result = await service.validate("ONE")
    assert result.is_valid is False


async def test_inactive_promo_is_invalid(session):
    repo = PromoCodeRepository(session)
    promo = await repo.create("DEAD", DiscountType.PERCENT, 5, None, None)
    await repo.set_active(promo, False)
    await session.commit()

    service = PromoService(session)
    result = await service.validate("DEAD")
    assert result.is_valid is False
