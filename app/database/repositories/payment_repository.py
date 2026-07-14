"""Репозиторий платежей."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.payment import Payment, PaymentProviderStatus
from app.database.repositories.base import BaseRepository


class PaymentRepository(BaseRepository):
    """Доступ к таблице payments."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(
        self,
        order_id: int,
        provider: str,
        provider_payment_id: str,
        amount: int,
        currency: str,
        payment_url: str | None,
        raw_response: str | None,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            provider=provider,
            provider_payment_id=provider_payment_id,
            amount=amount,
            currency=currency,
            payment_url=payment_url,
            raw_response=raw_response,
            status=PaymentProviderStatus.PENDING,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_provider_payment_id(self, provider_payment_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        return result.scalar_one_or_none()

    async def set_status(
        self, payment: Payment, status: PaymentProviderStatus, raw_response: str | None = None
    ) -> None:
        payment.status = status
        if raw_response is not None:
            payment.raw_response = raw_response
        await self.session.flush()
