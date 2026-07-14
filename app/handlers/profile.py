"""Личный кабинет пользователя (/profile)."""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.order_repository import OrderRepository
from app.utils.money import format_price

router = Router(name="profile")


@router.message(Command("profile"))
async def handle_profile(message: Message, session: AsyncSession, user: User) -> None:
    order_repo = OrderRepository(session)
    recent_orders = await order_repo.list_by_user(user.id, limit=5)

    lines = [
        "━━━━━━━━━━━━━━",
        "👤 Личный кабинет",
        "━━━━━━━━━━━━━━",
        f"Всего заказов: {user.orders_count}",
        f"Оплачено заказов: {user.paid_orders_count}",
        f"Сумма покупок: {format_price(user.total_spent)}",
    ]
    if recent_orders:
        lines.append("━━━━━━━━━━━━━━")
        lines.append("Последние заказы:")
        for order in recent_orders:
            lines.append(
                f"#{order.order_number} — {order.volume} л — {format_price(order.total_price)}"
            )
    lines.append("━━━━━━━━━━━━━━")
    await message.answer("\n".join(lines))
