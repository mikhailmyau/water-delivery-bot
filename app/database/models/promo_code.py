"""Модель промокода."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class DiscountType(str, enum.Enum):
    """Тип скидки промокода."""

    FIXED = "fixed"
    """Фиксированная сумма в копейках."""

    PERCENT = "percent"
    """Процент от стоимости товара (0-100)."""


class PromoCode(TimestampMixin, Base):
    """Промокод на скидку."""

    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(
        SAEnum(DiscountType, native_enum=False, length=16), nullable=False
    )
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    """Для FIXED — копейки, для PERCENT — целое число процентов 1-100."""

    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    """None означает неограниченное количество использований."""

    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"PromoCode(code={self.code})"
