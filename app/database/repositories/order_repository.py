"""Репозиторий заказов."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.base import utcnow
from app.database.models.order import DeliveryStatus, Order, PaymentStatus
from app.database.repositories.base import BaseRepository
from app.utils.constants import ADMIN_RECENT_ORDERS_LIMIT


class OrderRepository(BaseRepository):
    """Доступ к таблице orders."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(
        self,
        order_number: str,
        user_id: int,
        city: str,
        street: str,
        house: str,
        volume: int,
        price_per_liter: int,
        delivery_price: int,
        discount: int,
        total_price: int,
        promo_code_id: int | None,
    ) -> Order:
        order = Order(
            order_number=order_number,
            user_id=user_id,
            city=city,
            street=street,
            house=house,
            volume=volume,
            price_per_liter=price_per_liter,
            delivery_price=delivery_price,
            discount=discount,
            total_price=total_price,
            promo_code_id=promo_code_id,
            payment_status=PaymentStatus.NEW,
            delivery_status=DeliveryStatus.CREATED,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_by_id(self, order_id: int, *, with_relations: bool = False) -> Order | None:
        if with_relations:
            result = await self.session.execute(
                select(Order)
                .options(
                    selectinload(Order.user),
                    selectinload(Order.promo_code),
                    selectinload(Order.payments),
                )
                .where(Order.id == order_id)
            )
            return result.scalar_one_or_none()
        return await self.session.get(Order, order_id)

    async def get_by_number(self, order_number: str) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = ADMIN_RECENT_ORDERS_LIMIT) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.user))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_unpaid(self, limit: int = ADMIN_RECENT_ORDERS_LIMIT) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.user))
            .where(Order.payment_status.in_([PaymentStatus.NEW, PaymentStatus.WAITING]))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int, limit: int = 10) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_awaiting_first_reminder(
        self, older_than: datetime
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.user))
            .where(
                Order.payment_status.in_([PaymentStatus.NEW, PaymentStatus.WAITING]),
                Order.created_at <= older_than,
                Order.reminder_first_sent_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def list_awaiting_second_reminder(
        self, older_than: datetime
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.user))
            .where(
                Order.payment_status.in_([PaymentStatus.NEW, PaymentStatus.WAITING]),
                Order.reminder_first_sent_at.is_not(None),
                Order.reminder_first_sent_at <= older_than,
                Order.reminder_second_sent_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def mark_reminder_sent(self, order: Order, *, second: bool = False) -> None:
        if second:
            order.reminder_second_sent_at = utcnow()
        else:
            order.reminder_first_sent_at = utcnow()
        await self.session.flush()

    async def set_payment_status(self, order: Order, status: PaymentStatus) -> None:
        order.payment_status = status
        if status == PaymentStatus.SUCCESS:
            order.paid_at = utcnow()
            order.delivery_status = DeliveryStatus.PAID
        await self.session.flush()

    async def set_delivery_status(self, order: Order, status: DeliveryStatus) -> None:
        order.delivery_status = status
        await self.session.flush()

    async def update_address(self, order: Order, city: str, street: str, house: str) -> None:
        order.city = city
        order.street = street
        order.house = house
        await self.session.flush()

    async def delete(self, order: Order) -> None:
        await self.session.delete(order)
        await self.session.flush()

    async def count_created_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(Order.id)).where(Order.created_at >= since)
        )
        return int(result.scalar_one())

    async def count_paid_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                Order.payment_status == PaymentStatus.SUCCESS,
                Order.paid_at >= since,
            )
        )
        return int(result.scalar_one())

    async def count_unpaid_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                Order.payment_status.in_([PaymentStatus.NEW, PaymentStatus.WAITING]),
                Order.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def count_cancelled_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                Order.delivery_status == DeliveryStatus.CANCELLED,
                Order.updated_at >= since,
            )
        )
        return int(result.scalar_one())

    async def revenue_since(self, since: datetime) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Order.total_price), 0)).where(
                Order.payment_status == PaymentStatus.SUCCESS,
                Order.paid_at >= since,
            )
        )
        return int(result.scalar_one())

    async def average_check_since(self, since: datetime) -> int:
        paid_count = await self.count_paid_since(since)
        if paid_count == 0:
            return 0
        revenue = await self.revenue_since(since)
        return revenue // paid_count
