"""Модель события аналитики (воронка, конверсия)."""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, BigIntPK, TimestampMixin


class AnalyticsEvent(TimestampMixin, Base):
    """Единичное событие пользовательской активности."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    event: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"), nullable=True, index=True
    )
    event_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Дополнительные данные события в формате JSON-строки."""

    def __repr__(self) -> str:
        return f"AnalyticsEvent(event={self.event}, user_id={self.user_id})"
