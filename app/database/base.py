"""Базовый класс декларативных моделей и общие миксины."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Текущее время в UTC. Все даты в проекте хранятся в UTC."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей проекта."""

    type_annotation_map = {
        int: BigInteger,
    }


class TimestampMixin:
    """Добавляет поля created_at / updated_at, хранимые в UTC."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
