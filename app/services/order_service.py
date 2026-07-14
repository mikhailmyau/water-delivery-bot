"""Сервис оформления и сопровождения заказа.

Любое действие пользователя атомарно: заказ создаётся одной транзакцией,
после успешного commit сессии он уже не может оказаться в неопределённом
состоянии (см. ТЗ, глава 57 «Бизнес-логика»).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.order import DeliveryStatus, Order, PaymentStatus
from app.database.models.promo_code import PromoCode
from app.database.models.user import User
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.delivery_service import DeliveryService
from app.services.price_service import PriceService
from app.services.promo_service import PromoService


@dataclass(frozen=True, slots=True)
class OrderCalculation:
    """Итог расчёта стоимости заказа до его создания (для карточки-калькулятора)."""

    volume: int
    price_per_liter: int
    product_price: int
    delivery_price: int
    is_free_delivery: bool
    discount: int
    total_price: int


class OrderService:
    """Оркестрирует расчёт стоимости и создание заказа."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.order_repo = OrderRepository(session)
        self.user_repo = UserRepository(session)
        self.price_service = PriceService(session)
        self.delivery_service = DeliveryService(session)
        self.promo_service = PromoService(session)
        self.analytics_service = AnalyticsService(session)

    async def calculate(
        self, volume: int, promo: PromoCode | None = None
    ) -> OrderCalculation:
        price_per_liter = await self.price_service.get_price_per_liter()
        product_price = price_per_liter * volume
        quote = await self.delivery_service.calculate(volume)
        discount = self.promo_service.calculate_discount(promo, product_price) if promo else 0
        total_price = max(product_price - discount + quote.price, 0)
        return OrderCalculation(
            volume=volume,
            price_per_liter=price_per_liter,
            product_price=product_price,
            delivery_price=quote.price,
            is_free_delivery=quote.is_free,
            discount=discount,
            total_price=total_price,
        )

    async def create_order(
        self,
        user: User,
        city: str,
        street: str,
        house: str,
        volume: int,
        promo: PromoCode | None,
    ) -> Order:
        calculation = await self.calculate(volume, promo)
        order = await self.order_repo.create(
            order_number=self._temporary_order_number(),
            user_id=user.id,
            city=city.strip(),
            street=street.strip(),
            house=house.strip(),
            volume=volume,
            price_per_liter=calculation.price_per_liter,
            delivery_price=calculation.delivery_price,
            discount=calculation.discount,
            total_price=calculation.total_price,
            promo_code_id=promo.id if promo else None,
        )
        order.order_number = f"{order.id:06d}"
        await self.session.flush()

        if promo is not None:
            await self.promo_service.register_usage(promo)
            await self.analytics_service.track(
                AnalyticsEvents.PROMO_APPLIED, user_id=user.id, order_id=order.id
            )

        await self.user_repo.increment_orders_count(user)
        await self.analytics_service.track(
            AnalyticsEvents.ORDER_CREATED, user_id=user.id, order_id=order.id
        )
        return order

    async def cancel_order(self, order: Order) -> None:
        await self.order_repo.set_delivery_status(order, DeliveryStatus.CANCELLED)
        if order.payment_status in (PaymentStatus.NEW, PaymentStatus.WAITING):
            await self.order_repo.set_payment_status(order, PaymentStatus.FAILED)

    @staticmethod
    def _temporary_order_number() -> str:
        """Временный уникальный номер до получения id; заменяется на #{id:06d} сразу после flush."""
        return f"TMP{uuid.uuid4().hex[:10]}"
