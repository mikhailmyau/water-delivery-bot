"""Модель заказа и связанные перечисления статусов."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BigIntPK, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.payment import Payment
    from app.database.models.promo_code import PromoCode
    from app.database.models.user import User


class PaymentStatus(str, enum.Enum):
    """Статус оплаты заказа."""

    NEW = "new"
    WAITING = "waiting"
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REFUNDED = "refunded"


class DeliveryStatus(str, enum.Enum):
    """Статус доставки заказа."""

    CREATED = "created"
    WAITING_PAYMENT = "waiting_payment"
    PAID = "paid"
    PROCESSING = "processing"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(TimestampMixin, Base):
    """Заказ на доставку воды."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    city: Mapped[str] = mapped_column(String(128), nullable=False)
    street: Mapped[str] = mapped_column(String(256), nullable=False)
    house: Mapped[str] = mapped_column(String(32), nullable=False)

    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    """Объём заказа в литрах: одно из значений AVAILABLE_VOLUMES_LITERS."""

    price_per_liter: Mapped[int] = mapped_column(Integer, nullable=False)
    """Цена за литр в копейках на момент оформления заказа."""

    delivery_price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Стоимость доставки в копейках."""

    discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    """Сумма скидки в копейках."""

    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    """Итоговая сумма к оплате в копейках."""

    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False, length=16),
        default=PaymentStatus.NEW,
        nullable=False,
        index=True,
    )
    delivery_status: Mapped[DeliveryStatus] = mapped_column(
        SAEnum(DeliveryStatus, native_enum=False, length=20),
        default=DeliveryStatus.CREATED,
        nullable=False,
        index=True,
    )

    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey("promo_codes.id"), nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reminder_first_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reminder_second_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    promo_code: Mapped[PromoCode | None] = relationship("PromoCode", foreign_keys=[promo_code_id])
    payments: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="order", order_by="Payment.created_at.desc()"
    )

    @property
    def current_payment(self) -> Payment | None:
        """Последний созданный платёж по заказу (заказ может иметь несколько попыток оплаты)."""
        return self.payments[0] if self.payments else None

    def __repr__(self) -> str:
        return f"Order(id={self.id}, number={self.order_number}, status={self.payment_status})"
