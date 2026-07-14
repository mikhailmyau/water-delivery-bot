"""Тестовый платёжный провайдер.

Работает полностью локально, без внешних зависимостей — чтобы проект можно
было запустить и провести заказ от начала до конца сразу после установки,
до подключения боевого платёжного API. Использует тот же webhook-контракт,
что и боевые провайдеры (см. app/payments/base.py), поэтому переключение на
реальный шлюз не требует изменений в остальной части проекта.
"""

from __future__ import annotations

import json
import uuid

from app.payments.base import CreatedPayment, PaymentProvider, PaymentStatusResult


class MockPaymentProvider(PaymentProvider):
    """Имитирует платёжный шлюз: выдаёт ссылку на локальную страницу подтверждения оплаты."""

    name = "mock"

    def __init__(self, public_base_url: str, webhook_path: str) -> None:
        self._public_base_url = public_base_url.rstrip("/")
        self._webhook_path = webhook_path

    async def create_payment(
        self,
        *,
        order_id: int,
        order_number: str,
        amount: int,
        description: str,
        return_url: str,
    ) -> CreatedPayment:
        provider_payment_id = f"mock_{uuid.uuid4().hex}"
        payment_url = f"{self._public_base_url}/payments/mock-checkout/{provider_payment_id}"
        raw_response = json.dumps(
            {
                "provider_payment_id": provider_payment_id,
                "order_number": order_number,
                "amount": amount,
                "description": description,
            },
            ensure_ascii=False,
        )
        return CreatedPayment(
            provider_payment_id=provider_payment_id,
            payment_url=payment_url,
            raw_response=raw_response,
        )

    async def get_status(self, provider_payment_id: str) -> PaymentStatusResult:
        # У тестового провайдера нет собственного стейта — источник истины это
        # запись Payment в нашей БД, статус в неё пишется через parse_webhook.
        return PaymentStatusResult(
            provider_payment_id=provider_payment_id,
            is_succeeded=False,
            is_canceled=False,
            amount=0,
            raw_response="{}",
        )

    def parse_webhook(
        self, body: bytes, headers: dict[str, str], remote_ip: str | None
    ) -> PaymentStatusResult | None:
        payload = json.loads(body.decode("utf-8"))
        provider_payment_id = payload.get("provider_payment_id")
        status = payload.get("status")
        amount = int(payload.get("amount", 0))
        if not provider_payment_id or status not in ("succeeded", "canceled"):
            return None
        return PaymentStatusResult(
            provider_payment_id=provider_payment_id,
            is_succeeded=status == "succeeded",
            is_canceled=status == "canceled",
            amount=amount,
            raw_response=json.dumps(payload, ensure_ascii=False),
        )
