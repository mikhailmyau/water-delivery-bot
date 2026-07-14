"""Сервис оплаты: создание платежа и обработка результата (в т.ч. из webhook).

Обработка результата идемпотентна (см. ТЗ, глава 64): повторный webhook по
уже обработанному платежу не создаёт второй заказ, не шлёт повторное
уведомление и не начисляет скидку дважды.
"""

from __future__ import annotations

import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models.order import Order, PaymentStatus
from app.database.models.payment import Payment, PaymentProviderStatus
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.payment_repository import PaymentRepository
from app.database.repositories.user_repository import UserRepository
from app.payments.base import PaymentProvider, PaymentStatusResult
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.notification_service import NotificationService
from app.services.settings_service import SettingsService
from app.utils.constants import CURRENCY_CODE
from app.utils.formatting import format_admin_new_order_card, format_payment_success

logger = logging.getLogger("app.payments")


class PaymentService:
    """Оркестрирует создание платежа и последующую обработку статуса."""

    def __init__(
        self,
        session: AsyncSession,
        provider: PaymentProvider,
        bot: Bot | None = None,
    ) -> None:
        self.session = session
        self.provider = provider
        self.order_repo = OrderRepository(session)
        self.payment_repo = PaymentRepository(session)
        self.user_repo = UserRepository(session)
        self.analytics_service = AnalyticsService(session)
        self.settings_service = SettingsService(session)
        self.notifications = NotificationService(bot) if bot is not None else None

    async def create_payment_for_order(self, order: Order) -> Payment:
        return_url = settings.public_base_url
        created = await self.provider.create_payment(
            order_id=order.id,
            order_number=order.order_number,
            amount=order.total_price,
            description=f"Заказ #{order.order_number} — питьевая вода {order.volume} л",
            return_url=return_url,
        )
        payment = await self.payment_repo.create(
            order_id=order.id,
            provider=self.provider.name,
            provider_payment_id=created.provider_payment_id,
            amount=order.total_price,
            currency=CURRENCY_CODE,
            payment_url=created.payment_url,
            raw_response=created.raw_response,
        )
        await self.order_repo.set_payment_status(order, PaymentStatus.WAITING)
        await self.analytics_service.track(
            AnalyticsEvents.PAYMENT_ATTEMPTED, user_id=order.user_id, order_id=order.id
        )
        logger.info("Payment created: order=%s provider_payment_id=%s", order.order_number, payment.provider_payment_id)
        return payment

    async def handle_status_result(self, status_result: PaymentStatusResult) -> Order | None:
        """Применяет результат опроса/webhook к заказу. Возвращает Order, если статус изменился."""
        payment = await self.payment_repo.get_by_provider_payment_id(
            status_result.provider_payment_id
        )
        if payment is None:
            logger.warning(
                "Webhook for unknown payment_id=%s ignored", status_result.provider_payment_id
            )
            return None

        if payment.status == PaymentProviderStatus.SUCCEEDED:
            # Уже обработан ранее — идемпотентно игнорируем повторный webhook.
            return None

        if status_result.is_succeeded:
            return await self._handle_success(payment, status_result)
        if status_result.is_canceled:
            await self._handle_cancel(payment, status_result)
            return None
        return None

    async def _handle_success(
        self, payment: Payment, status_result: PaymentStatusResult
    ) -> Order | None:
        order = await self.order_repo.get_by_id(payment.order_id, with_relations=True)
        if order is None:
            logger.error("Payment %s references missing order_id=%s", payment.id, payment.order_id)
            return None

        if status_result.amount != order.total_price:
            logger.error(
                "Payment amount mismatch for order %s: expected=%s got=%s",
                order.order_number,
                order.total_price,
                status_result.amount,
            )
            return None

        await self.payment_repo.set_status(
            payment, PaymentProviderStatus.SUCCEEDED, status_result.raw_response
        )
        await self.order_repo.set_payment_status(order, PaymentStatus.SUCCESS)
        await self.user_repo.register_paid_order(order.user, order.total_price)
        await self.analytics_service.track(
            AnalyticsEvents.PAYMENT_SUCCEEDED, user_id=order.user_id, order_id=order.id
        )
        logger.info("Payment succeeded: order=%s amount=%s", order.order_number, status_result.amount)

        if self.notifications is not None:
            bot_settings = await self.settings_service.get()
            await self.notifications.send_to_user(
                order.user.telegram_id,
                format_payment_success(order, bot_settings.delivery_days),
            )
        return order

    async def _handle_cancel(self, payment: Payment, status_result: PaymentStatusResult) -> None:
        order = await self.order_repo.get_by_id(payment.order_id)
        await self.payment_repo.set_status(
            payment, PaymentProviderStatus.CANCELED, status_result.raw_response
        )
        if order is not None:
            await self.analytics_service.track(
                AnalyticsEvents.PAYMENT_CANCELLED, user_id=order.user_id, order_id=order.id
            )
        logger.info("Payment canceled: provider_payment_id=%s", payment.provider_payment_id)

    async def notify_admin_group_new_order(self, order: Order) -> None:
        if self.notifications is not None:
            await self.notifications.send_to_admin_group(format_admin_new_order_card(order))
