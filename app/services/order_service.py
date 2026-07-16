"""Сервис оформления и сопровождения заказа.

Любое действие пользователя атомарно: заказ создаётся одной транзакцией,
после успешного commit сессии он уже не может оказаться в неопределённом
состоянии.

Доставка нигде в расчёте не участвует — она всегда включена в цену воды
(таксист/курьер довозит бутыли до двери, это заложено в тариф). Единственное,
что зависит от города, — обещанный срок, и это не цена, а текст-снимок
(см. Order.delivery_days_estimate), который передаётся сюда уже готовым из
хендлера (там же, где выбирается город, — см. app/handlers/order.py).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.order import DeliveryStatus, Order, PaymentStatus
from app.database.models.user import User
from app.database.models.water_type import WaterType
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.user_repository import UserRepository
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.price_service import PriceService
from app.utils.constants import BOTTLE_VOLUME_LITERS


@dataclass(frozen=True, slots=True)
class OrderCalculation:
    """Итог расчёта стоимости заказа до его создания (для карточки-калькулятора)."""

    water_type: WaterType
    volume: int
    price_per_liter: int
    total_price: int


class OrderService:
    """Оркестрирует расчёт стоимости и создание заказа."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.order_repo = OrderRepository(session)
        self.user_repo = UserRepository(session)
        self.price_service = PriceService(session)
        self.analytics_service = AnalyticsService(session)

    async def calculate(self, water_type: WaterType, bottles: int) -> OrderCalculation:
        volume = bottles * BOTTLE_VOLUME_LITERS
        price_per_liter = await self.price_service.get_price_per_liter(water_type)
        total_price = price_per_liter * volume
        return OrderCalculation(
            water_type=water_type,
            volume=volume,
            price_per_liter=price_per_liter,
            total_price=total_price,
        )

    async def create_order(
        self,
        user: User,
        city: str,
        street: str,
        house: str,
        water_type: WaterType,
        bottles: int,
        delivery_days_estimate: str,
        city_matched: bool,
    ) -> Order:
        calculation = await self.calculate(water_type, bottles)
        order = await self.order_repo.create(
            order_number=self._temporary_order_number(),
            user_id=user.id,
            city=city.strip(),
            street=street.strip(),
            house=house.strip(),
            water_type=calculation.water_type,
            volume=calculation.volume,
            price_per_liter=calculation.price_per_liter,
            total_price=calculation.total_price,
            delivery_days_estimate=delivery_days_estimate,
            city_matched=city_matched,
        )
        order.order_number = f"{order.id:06d}"
        await self.session.flush()

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
