"""Сервис расчёта стоимости товара."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings_service import SettingsService


class PriceService:
    """Рассчитывает стоимость воды. Ничего не знает о доставке и промокодах."""

    def __init__(self, session: AsyncSession) -> None:
        self.settings_service = SettingsService(session)

    async def get_price_per_liter(self) -> int:
        settings = await self.settings_service.get()
        return settings.price_per_liter

    async def calculate_product_price(self, volume: int) -> int:
        price_per_liter = await self.get_price_per_liter()
        return price_per_liter * volume

    async def set_price_per_liter(self, price_per_liter: int) -> int:
        await self.settings_service.update(price_per_liter=price_per_liter)
        return price_per_liter
