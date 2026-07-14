"""Фабрика платёжных провайдеров — единственное место, где выбирается конкретный шлюз."""

from __future__ import annotations

from app.config import settings
from app.payments.base import PaymentProvider
from app.payments.mock_provider import MockPaymentProvider
from app.payments.yookassa_provider import YooKassaPaymentProvider

_provider_instance: PaymentProvider | None = None


def get_payment_provider() -> PaymentProvider:
    """Возвращает singleton-инстанс провайдера, выбранного в PAYMENT_PROVIDER."""
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    if settings.payment_provider == "yookassa":
        if not settings.payment_api_key or not settings.payment_secret:
            raise RuntimeError(
                "PAYMENT_PROVIDER=yookassa требует заполненных PAYMENT_API_KEY и PAYMENT_SECRET"
            )
        _provider_instance = YooKassaPaymentProvider(
            shop_id=settings.payment_api_key,
            secret_key=settings.payment_secret,
            verify_ip=not settings.debug,
        )
    else:
        _provider_instance = MockPaymentProvider(
            public_base_url=settings.public_base_url,
            webhook_path=settings.payment_webhook_path,
        )
    return _provider_instance
