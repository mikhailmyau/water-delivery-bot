"""Сервис настроек проекта с in-process кэшем.

Настройки читаются из БД администратором крайне редко, а используются на каждом
экране — поэтому кэшируются в памяти процесса. Кэш сбрасывается сразу после
любого изменения, так что новые значения применяются мгновенно и без
перезапуска бота (см. ТЗ, глава 59).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.settings import BotSettings
from app.database.repositories.settings_repository import SettingsRepository


class SettingsService:
    """Доступ к настройкам проекта поверх SettingsRepository с кэшированием."""

    _cache: BotSettings | None = None

    def __init__(self, session: AsyncSession) -> None:
        self.repo = SettingsRepository(session)

    async def get(self) -> BotSettings:
        if SettingsService._cache is None:
            SettingsService._cache = await self.repo.get()
        return SettingsService._cache

    async def update(self, **fields: object) -> BotSettings:
        settings = await self.repo.get()
        for field_name, value in fields.items():
            setattr(settings, field_name, value)
        await self.repo.save(settings)
        SettingsService._cache = settings
        return settings

    @classmethod
    def invalidate_cache(cls) -> None:
        cls._cache = None
