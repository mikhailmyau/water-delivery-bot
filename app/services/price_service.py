"""Сервис расчёта стоимости товара.

Три вида воды — три независимые цены за литр (см. BotSettings). Это
единственное, что покупатель видит и что администратор реально меняет
через /price: доставка теперь всегда включена в цену (см. app/data/cities.py
и app/handlers/order.py), отдельного "тарифа доставки" в проекте больше нет.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.water_type import WaterType
from app.services.settings_service import SettingsService

_SETTINGS_FIELD_BY_TYPE: dict[WaterType, str] = {
    WaterType.SLM: "price_slm_per_liter",
    WaterType.SRM: "price_srm_per_liter",
    WaterType.VSM: "price_vsm_per_liter",
    WaterType.GAZ: "price_gaz_per_liter",
}


class PriceService:
    """Рассчитывает стоимость воды по выбранному виду. Ничего не знает о доставке."""

    def __init__(self, session: AsyncSession) -> None:
        self.settings_service = SettingsService(session)

    async def get_price_per_liter(self, water_type: WaterType) -> int:
        settings = await self.settings_service.get()
        return getattr(settings, _SETTINGS_FIELD_BY_TYPE[water_type])

    async def get_all_prices(self) -> dict[WaterType, int]:
        settings = await self.settings_service.get()
        return {
            water_type: getattr(settings, field)
            for water_type, field in _SETTINGS_FIELD_BY_TYPE.items()
        }

    async def calculate_product_price(self, water_type: WaterType, volume: int) -> int:
        price_per_liter = await self.get_price_per_liter(water_type)
        return price_per_liter * volume

    async def set_price_per_liter(self, water_type: WaterType, price_per_liter: int) -> int:
        await self.settings_service.update(**{_SETTINGS_FIELD_BY_TYPE[water_type]: price_per_liter})
        return price_per_liter
