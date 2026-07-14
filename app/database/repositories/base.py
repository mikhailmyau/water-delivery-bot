"""Базовый класс репозитория."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Общий предок всех репозиториев: хранит сессию и не содержит бизнес-логики."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
