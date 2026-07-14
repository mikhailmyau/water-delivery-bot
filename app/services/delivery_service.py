"""Сервис расчёта стоимости и сроков доставки."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings_service import SettingsService


@dataclass(frozen=True, slots=True)
class DeliveryQuote:
    """Итог расчёта доставки для конкретного объёма заказа."""

    price: int
    is_free: bool
    standard_days: str
    express_days: str


class DeliveryService:
    """Определяет стоимость и ориентировочный срок доставки."""

    def __init__(self, session: AsyncSession) -> None:
        self.settings_service = SettingsService(session)

    async def calculate(self, volume: int) -> DeliveryQuote:
        settings = await self.settings_service.get()
        is_free = volume >= settings.free_delivery_from_liters
        return DeliveryQuote(
            price=0 if is_free else settings.delivery_price,
            is_free=is_free,
            standard_days=settings.delivery_days,
            express_days=settings.express_delivery_days,
        )

    async def update_settings(
        self,
        *,
        delivery_price: int | None = None,
        free_delivery_from_liters: int | None = None,
        delivery_days: str | None = None,
        express_delivery_days: str | None = None,
    ) -> None:
        fields = {
            key: value
            for key, value in {
                "delivery_price": delivery_price,
                "free_delivery_from_liters": free_delivery_from_liters,
                "delivery_days": delivery_days,
                "express_delivery_days": express_delivery_days,
            }.items()
            if value is not None
        }
        if fields:
            await self.settings_service.update(**fields)
