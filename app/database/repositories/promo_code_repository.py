"""Репозиторий промокодов."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.promo_code import DiscountType, PromoCode
from app.database.repositories.base import BaseRepository


class PromoCodeRepository(BaseRepository):
    """Доступ к таблице promo_codes."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_code(self, code: str) -> PromoCode | None:
        result = await self.session.execute(
            select(PromoCode).where(PromoCode.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, promo_code_id: int) -> PromoCode | None:
        return await self.session.get(PromoCode, promo_code_id)

    async def list_all(self) -> list[PromoCode]:
        result = await self.session.execute(
            select(PromoCode).order_by(PromoCode.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        code: str,
        discount_type: DiscountType,
        discount_value: int,
        usage_limit: int | None,
        expires_at: datetime | None,
    ) -> PromoCode:
        promo = PromoCode(
            code=code.upper(),
            discount_type=discount_type,
            discount_value=discount_value,
            usage_limit=usage_limit,
            expires_at=expires_at,
            is_active=True,
        )
        self.session.add(promo)
        await self.session.flush()
        return promo

    async def increment_usage(self, promo: PromoCode) -> None:
        promo.used_count += 1
        await self.session.flush()

    async def set_active(self, promo: PromoCode, is_active: bool) -> None:
        promo.is_active = is_active
        await self.session.flush()

    async def delete(self, promo: PromoCode) -> None:
        await self.session.delete(promo)
        await self.session.flush()
