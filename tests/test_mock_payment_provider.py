"""Тесты MockPaymentProvider (через мок, без реальной сети)."""

from __future__ import annotations

import json

import pytest

from app.payments.mock_provider import MockPaymentProvider

pytestmark = pytest.mark.asyncio


@pytest.fixture
def provider() -> MockPaymentProvider:
    return MockPaymentProvider(
        public_base_url="http://localhost:8080", webhook_path="/payments/webhook"
    )


async def test_create_payment_returns_checkout_url(provider):
    created = await provider.create_payment(
        order_id=1,
        order_number="000001",
        amount=12480_00,
        description="Заказ",
        return_url="http://x",
    )
    assert created.provider_payment_id.startswith("mock_")
    assert created.provider_payment_id in created.payment_url
    assert created.payment_url.startswith("http://localhost:8080/payments/mock-checkout/")


async def test_parse_webhook_succeeded(provider):
    body = json.dumps(
        {"provider_payment_id": "mock_abc", "status": "succeeded", "amount": 1000}
    ).encode()
    result = provider.parse_webhook(body, {}, "127.0.0.1")
    assert result is not None
    assert result.is_succeeded is True
    assert result.amount == 1000


async def test_parse_webhook_canceled(provider):
    body = json.dumps(
        {"provider_payment_id": "mock_abc", "status": "canceled", "amount": 0}
    ).encode()
    result = provider.parse_webhook(body, {}, None)
    assert result is not None
    assert result.is_canceled is True


async def test_parse_webhook_ignores_unknown_status(provider):
    body = json.dumps(
        {"provider_payment_id": "mock_abc", "status": "pending", "amount": 0}
    ).encode()
    result = provider.parse_webhook(body, {}, None)
    assert result is None
