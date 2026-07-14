"""Репозиторий событий аналитики."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.analytics_event import AnalyticsEvent
from app.database.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository):
    """Доступ к таблице analytics_events."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add_event(
        self,
        event: str,
        user_id: int | None,
        order_id: int | None,
        metadata_json: str | None,
    ) -> AnalyticsEvent:
        record = AnalyticsEvent(
            event=event, user_id=user_id, order_id=order_id, event_metadata=metadata_json
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def count_distinct_users_since(self, event: str, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(func.distinct(AnalyticsEvent.user_id))).where(
                AnalyticsEvent.event == event,
                AnalyticsEvent.created_at >= since,
                AnalyticsEvent.user_id.is_not(None),
            )
        )
        return int(result.scalar_one())
