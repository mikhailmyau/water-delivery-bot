"""Репозиторий настроек проекта (singleton-строка в БД)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.settings import SETTINGS_SINGLETON_ID, BotSettings
from app.database.repositories.base import BaseRepository


class SettingsRepository(BaseRepository):
    """Доступ к таблице bot_settings."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get(self) -> BotSettings:
        settings = await self.session.get(BotSettings, SETTINGS_SINGLETON_ID)
        if settings is None:
            settings = BotSettings(id=SETTINGS_SINGLETON_ID)
            self.session.add(settings)
            await self.session.flush()
        return settings

    async def save(self, settings: BotSettings) -> None:
        await self.session.flush()
