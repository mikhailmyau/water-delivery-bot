"""Базовый класс декларативных моделей и общие миксины."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Текущее время в UTC. Все даты в проекте хранятся в UTC."""
    return datetime.now(UTC)


def ensure_utc(value: datetime | None) -> datetime | None:
    """Гарантирует наличие tzinfo=UTC.

    SQLite не хранит offset и всегда возвращает naive datetime, даже для
    колонок DateTime(timezone=True) — в отличие от PostgreSQL. Прямое
    Python-сравнение naive/aware значений валит TypeError, поэтому перед
    любым таким сравнением значение из БД нужно пропустить через эту функцию.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


# SQLite отдаёт auto-increment ("ROWID alias") только колонке, объявленной
# буквально как "INTEGER PRIMARY KEY" — BIGINT PRIMARY KEY этим свойством не
# обладает, и вставка без явного id падает с NOT NULL. Поэтому первичные ключи
# используют BIGINT везде, кроме SQLite, где остаётся обычный INTEGER.
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


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
