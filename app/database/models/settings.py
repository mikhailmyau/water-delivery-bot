"""Модель настроек проекта, хранимых в базе данных (без перезапуска бота)."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.content import BRAND_NAME
from app.database.base import Base, BigIntPK, TimestampMixin

SETTINGS_SINGLETON_ID = 1


class BotSettings(TimestampMixin, Base):
    """Единственная строка с настройками проекта (singleton).

    Доставка сюда не входит: она везде бесплатна (включена в цену воды) и
    её срок зависит только от города покупателя — см. app/data/cities.py.
    Администратор управляет только тем, что реально нужно менять на ходу:
    ценами и вступительным текстом.
    """

    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, default=SETTINGS_SINGLETON_ID)

    price_slm_per_liter: Mapped[int] = mapped_column(Integer, nullable=False, default=7099)
    """СЛМ (слабоминерализованная негаз.), цена за литр в копейках. По умолчанию 70,99 ₽."""

    price_srm_per_liter: Mapped[int] = mapped_column(Integer, nullable=False, default=7999)
    """СРМ (среднеминерализованная негаз.), цена за литр в копейках. По умолчанию 79,99 ₽."""

    price_vsm_per_liter: Mapped[int] = mapped_column(Integer, nullable=False, default=10290)
    """ВСМ (высокоминерализованная негаз.), цена за литр в копейках. По умолчанию 102,90 ₽."""

    price_gaz_per_liter: Mapped[int] = mapped_column(Integer, nullable=False, default=8499)
    """ГАЗ (газированная), цена за литр в копейках. По умолчанию 84,99 ₽."""

    welcome_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=(
            "🚰 <b>ВНУТРЕННИЕ РЕЗЕРВЫ ВОДЫ С ДОСТАВКОЙ ПО РФ</b> 🚰\n\n"
            f"<i>Вода от {BRAND_NAME} — крупнейшего поставщика воды с тысячами "
            "довольных клиентов!</i>"
        ),
    )
    """Вступительный абзац приветствия. Цены и ссылка на отзывы достраиваются
    автоматически и всегда показывают актуальные значения — см.
    app/utils/formatting.py::format_welcome_message."""

    support_link: Mapped[str] = mapped_column(String(256), nullable=False, default="https://t.me/")
    banner_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"BotSettings(id={self.id})"
