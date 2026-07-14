"""Репозиторий пользователей."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import utcnow
from app.database.models.user import User
from app.database.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Доступ к таблице users."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str | None,
        is_admin: bool,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def touch_activity(self, user: User) -> None:
        """Обновляет метку последней активности и, при изменении, профиль пользователя."""
        user.last_activity_at = utcnow()
        await self.session.flush()

    async def update_profile(
        self,
        user: User,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> None:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        await self.session.flush()

    async def increment_orders_count(self, user: User) -> None:
        user.orders_count += 1
        await self.session.flush()

    async def register_paid_order(self, user: User, total_price: int) -> None:
        user.paid_orders_count += 1
        user.total_spent += total_price
        await self.session.flush()

    async def count_all(self) -> int:
        result = await self.session.execute(select(User.id))
        return len(result.all())

    async def count_created_after(self, since: datetime) -> int:
        result = await self.session.execute(select(User.id).where(User.created_at >= since))
        return len(result.all())

    async def list_active_telegram_ids(self) -> list[int]:
        """Все telegram_id, кроме заблокировавших бота — используется для рассылки."""
        result = await self.session.execute(
            select(User.telegram_id).where(User.is_blocked.is_(False))
        )
        return [row[0] for row in result.all()]

    async def mark_blocked(self, telegram_id: int, blocked: bool = True) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is not None:
            user.is_blocked = blocked
            await self.session.flush()
