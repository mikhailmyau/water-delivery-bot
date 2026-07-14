"""Фильтр доступа администратора.

Если пользователь не администратор — апдейт полностью игнорируется, никакая
информация о существовании админ-команд наружу не раскрывается (ТЗ, глава 46).
"""

from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.config import settings


class IsAdmin(BaseFilter):
    """Пропускает апдейт только если его отправил администратор из ADMIN_IDS."""

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return user.id in settings.admin_ids
