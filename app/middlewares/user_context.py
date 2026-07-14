"""Middleware, обеспечивающий наличие записи пользователя в БД для каждого апдейта."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.repositories.user_repository import UserRepository


class UserContextMiddleware(BaseMiddleware):
    """Находит или создаёт пользователя, кладёт его в data['user']."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user: TelegramUser | None = data.get("event_from_user")
        if telegram_user is None:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(telegram_user.id)
        is_admin = telegram_user.id in settings.admin_ids

        if user is None:
            user = await repo.create(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                is_admin=is_admin,
            )
        else:
            if (
                user.username != telegram_user.username
                or user.first_name != telegram_user.first_name
                or user.last_name != telegram_user.last_name
            ):
                await repo.update_profile(
                    user, telegram_user.username, telegram_user.first_name, telegram_user.last_name
                )
            if user.is_admin != is_admin:
                user.is_admin = is_admin
            await repo.touch_activity(user)

        data["user"] = user
        data["is_admin"] = is_admin
        return await handler(event, data)
