"""Модель настроек проекта, хранимых в базе данных (без перезапуска бота)."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, BigIntPK, TimestampMixin

SETTINGS_SINGLETON_ID = 1


class BotSettings(TimestampMixin, Base):
    """Единственная строка с настройками проекта (singleton)."""

    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, default=SETTINGS_SINGLETON_ID)

    price_per_liter: Mapped[int] = mapped_column(Integer, nullable=False, default=7800)
    """Цена за литр в копейках. По умолчанию 78 ₽."""

    delivery_price: Mapped[int] = mapped_column(Integer, nullable=False, default=50000)
    """Стоимость платной доставки в копейках. По умолчанию 500 ₽."""

    free_delivery_from_liters: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    """Порог бесплатной доставки в литрах."""

    delivery_days: Mapped[str] = mapped_column(String(32), nullable=False, default="до 5 дней")
    express_delivery_days: Mapped[str] = mapped_column(
        String(32), nullable=False, default="1–3 дня"
    )

    welcome_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=(
            "💧 ДОСТАВКА ПИТЬЕВОЙ ВОДЫ\n\n"
            "Быстро. Надёжно. С доставкой по всей России.\n\n"
            "Минимальный заказ — 120 литров\n"
            "Средний срок доставки — до 5 дней"
        ),
    )
    faq_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    support_link: Mapped[str] = mapped_column(String(256), nullable=False, default="https://t.me/")
    banner_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"BotSettings(price_per_liter={self.price_per_liter})"
