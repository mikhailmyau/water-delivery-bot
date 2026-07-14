"""Модель платежа во внешней платёжной системе."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class PaymentProviderStatus(str, enum.Enum):
    """Статус платежа на стороне платёжного провайдера."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"


class Payment(TimestampMixin, Base):
    """Платёж, созданный у внешнего платёжного провайдера для конкретного заказа."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True, nullable=False)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_payment_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )

    status: Mapped[PaymentProviderStatus] = mapped_column(
        SAEnum(PaymentProviderStatus, native_enum=False, length=16),
        default=PaymentProviderStatus.PENDING,
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    """Сумма платежа в копейках."""

    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    payment_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Полный JSON-ответ платёжного API, сохраняется как есть."""

    order: Mapped["Order"] = relationship(
        "Order", back_populates="payments", foreign_keys=[order_id]
    )

    def __repr__(self) -> str:
        return f"Payment(id={self.id}, provider={self.provider}, status={self.status})"
