"""Сервис проверки и применения промокодов."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.promo_code import DiscountType, PromoCode
from app.database.repositories.promo_code_repository import PromoCodeRepository


@dataclass(frozen=True, slots=True)
class PromoValidationResult:
    """Результат проверки промокода."""

    is_valid: bool
    promo: PromoCode | None = None
    error_message: str = ""


class PromoService:
    """Проверяет валидность промокода и рассчитывает скидку."""

    _NOT_FOUND_MESSAGE = "К сожалению, такой промокод не найден или срок его действия истёк."

    def __init__(self, session: AsyncSession) -> None:
        self.repo = PromoCodeRepository(session)

    async def validate(self, code: str) -> PromoValidationResult:
        promo = await self.repo.get_by_code(code.strip())
        if promo is None or not promo.is_active:
            return PromoValidationResult(False, error_message=self._NOT_FOUND_MESSAGE)
        if promo.expires_at is not None and promo.expires_at < datetime.now(timezone.utc):
            return PromoValidationResult(False, error_message=self._NOT_FOUND_MESSAGE)
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            return PromoValidationResult(False, error_message=self._NOT_FOUND_MESSAGE)
        return PromoValidationResult(True, promo=promo)

    def calculate_discount(self, promo: PromoCode, product_price: int) -> int:
        if promo.discount_type == DiscountType.FIXED:
            return min(promo.discount_value, product_price)
        discount = product_price * promo.discount_value // 100
        return min(discount, product_price)

    async def register_usage(self, promo: PromoCode) -> None:
        await self.repo.increment_usage(promo)
