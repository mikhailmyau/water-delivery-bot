"""Сервис статистики для административной панели (/stats, раздел Заказы)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsService


@dataclass(frozen=True, slots=True)
class PeriodStats:
    """Сводная статистика за период."""

    new_users: int
    orders_created: int
    orders_paid: int
    orders_unpaid: int
    orders_cancelled: int
    revenue: int
    average_check: int
    conversion_percent: float


class StatsService:
    """Считает бизнес-показатели за произвольный период."""

    def __init__(self, session: AsyncSession) -> None:
        self.order_repo = OrderRepository(session)
        self.user_repo = UserRepository(session)
        self.analytics_service = AnalyticsService(session)

    async def get_period_stats(self, period: str) -> PeriodStats:
        since = AnalyticsService.period_start(period)
        created = await self.order_repo.count_created_since(since)
        paid = await self.order_repo.count_paid_since(since)
        unpaid = await self.order_repo.count_unpaid_since(since)
        cancelled = await self.order_repo.count_cancelled_since(since)
        revenue = await self.order_repo.revenue_since(since)
        average_check = await self.order_repo.average_check_since(since)
        new_users = await self.user_repo.count_created_after(since)
        conversion = (paid / created * 100) if created else 0.0
        return PeriodStats(
            new_users=new_users,
            orders_created=created,
            orders_paid=paid,
            orders_unpaid=unpaid,
            orders_cancelled=cancelled,
            revenue=revenue,
            average_check=average_check,
            conversion_percent=round(conversion, 1),
        )

    async def get_today_summary(self) -> PeriodStats:
        return await self.get_period_stats("today")

    async def get_funnel(self, period: str) -> dict[str, int]:
        since = AnalyticsService.period_start(period)
        return await self.analytics_service.get_funnel(since)

    @staticmethod
    def since_start_of_today() -> datetime:
        now = datetime.now(UTC)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
