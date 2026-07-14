"""Сервис аналитики: фиксирует события и считает показатели."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.analytics_repository import AnalyticsRepository
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.user_repository import UserRepository


class AnalyticsEvents:
    """Имена событий аналитики. Единый источник, чтобы не разъезжались строки."""

    BOT_STARTED = "bot_started"
    CATALOG_OPENED = "catalog_opened"
    VOLUME_SELECTED = "volume_selected"
    ORDER_STARTED = "order_started"
    ORDER_CREATED = "order_created"
    PAYMENT_ATTEMPTED = "payment_attempted"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_CANCELLED = "payment_cancelled"
    PROMO_APPLIED = "promo_applied"
    FAQ_OPENED = "faq_opened"
    SUPPORT_OPENED = "support_opened"


class AnalyticsService:
    """Запись событий и агрегированные показатели воронки."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AnalyticsRepository(session)
        self.order_repo = OrderRepository(session)
        self.user_repo = UserRepository(session)

    async def track(
        self,
        event: str,
        *,
        user_id: int | None = None,
        order_id: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        await self.repo.add_event(event, user_id, order_id, metadata_json)

    async def get_funnel(self, since: datetime) -> dict[str, int]:
        return {
            "started": await self.repo.count_distinct_users_since(
                AnalyticsEvents.BOT_STARTED, since
            ),
            "catalog_opened": await self.repo.count_distinct_users_since(
                AnalyticsEvents.CATALOG_OPENED, since
            ),
            "volume_selected": await self.repo.count_distinct_users_since(
                AnalyticsEvents.VOLUME_SELECTED, since
            ),
            "order_started": await self.repo.count_distinct_users_since(
                AnalyticsEvents.ORDER_STARTED, since
            ),
            "order_created": await self.repo.count_distinct_users_since(
                AnalyticsEvents.ORDER_CREATED, since
            ),
            "paid": await self.repo.count_distinct_users_since(
                AnalyticsEvents.PAYMENT_SUCCEEDED, since
            ),
        }

    @staticmethod
    def period_start(period: str) -> datetime:
        now = datetime.now(timezone.utc)
        if period == "today":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "week":
            return now - timedelta(days=7)
        if period == "month":
            return now - timedelta(days=30)
        return datetime(2000, 1, 1, tzinfo=timezone.utc)
