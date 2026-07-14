"""Модель пользователя Telegram."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, BigIntPK, TimestampMixin, utcnow


class User(TimestampMixin, Base):
    """Пользователь бота."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(8), nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_activity_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True, nullable=False
    )

    orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paid_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    """Сумма всех оплаченных заказов в копейках."""

    def __repr__(self) -> str:
        return f"User(id={self.id}, telegram_id={self.telegram_id})"

    @property
    def average_check(self) -> int:
        """Средний чек в копейках."""
        if self.paid_orders_count == 0:
            return 0
        return self.total_spent // self.paid_orders_count

    @property
    def full_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        name = " ".join(part for part in parts if part).strip()
        return name or (self.username or f"id{self.telegram_id}")
