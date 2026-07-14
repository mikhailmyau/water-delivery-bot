"""Боевой платёжный провайдер — ЮKassa (https://yookassa.ru/developers/api).

Реализует полноценный REST-вызов создания платежа, опрос статуса и разбор
webhook-уведомлений. Для подключения достаточно указать PAYMENT_API_KEY
(shopId) и PAYMENT_SECRET (secretKey) в .env — код проекта менять не нужно.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid

import aiohttp

from app.payments.base import CreatedPayment, PaymentProvider, PaymentStatusResult
from app.payments.exceptions import PaymentProviderError
from app.utils.constants import CURRENCY_CODE, PAYMENT_RETRY_DELAYS_SECONDS

logger = logging.getLogger("app.payments.yookassa")


class _RetryableError(Exception):
    """Временная ошибка платёжного API (5xx) — стоит повторить запрос."""


_API_BASE_URL = "https://api.yookassa.ru/v3"

# Официальный список подсетей уведомлений ЮKassa
# (https://yookassa.ru/developers/using-api/webhooks#ip). Используется как
# дополнительная проверка подлинности webhook в дополнение к валидации тела запроса.
TRUSTED_WEBHOOK_IP_PREFIXES: tuple[str, ...] = (
    "185.71.76.",
    "185.71.77.",
    "77.75.153.",
    "77.75.156.11",
    "77.75.156.35",
    "77.75.154.",
    "2a02:5180:",
)


class YooKassaPaymentProvider(PaymentProvider):
    """Интеграция с платёжным API ЮKassa."""

    name = "yookassa"

    def __init__(self, shop_id: str, secret_key: str, *, verify_ip: bool = True) -> None:
        self._shop_id = shop_id
        self._secret_key = secret_key
        self._verify_ip = verify_ip
        auth = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()
        self._auth_header = f"Basic {auth}"

    async def create_payment(
        self,
        *,
        order_id: int,
        order_number: str,
        amount: int,
        description: str,
        return_url: str,
    ) -> CreatedPayment:
        payload = {
            "amount": {"value": self._kopecks_to_amount_str(amount), "currency": CURRENCY_CODE},
            "capture": True,
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": description,
            "metadata": {"order_id": order_id, "order_number": order_number},
        }
        response = await self._request(
            "POST",
            f"{_API_BASE_URL}/payments",
            json_body=payload,
            idempotence_key=str(uuid.uuid4()),
        )
        confirmation = response.get("confirmation", {})
        return CreatedPayment(
            provider_payment_id=response["id"],
            payment_url=confirmation.get("confirmation_url", return_url),
            raw_response=json.dumps(response, ensure_ascii=False),
        )

    async def get_status(self, provider_payment_id: str) -> PaymentStatusResult:
        response = await self._request("GET", f"{_API_BASE_URL}/payments/{provider_payment_id}")
        return self._to_status_result(response)

    def parse_webhook(
        self, body: bytes, headers: dict[str, str], remote_ip: str | None
    ) -> PaymentStatusResult | None:
        if self._verify_ip and remote_ip is not None and not self._is_trusted_ip(remote_ip):
            logger.warning("Rejected YooKassa webhook from untrusted IP %s", remote_ip)
            return None

        payload = json.loads(body.decode("utf-8"))
        event = payload.get("event")
        payment_object = payload.get("object", {})
        if event not in ("payment.succeeded", "payment.canceled"):
            return None
        result = self._to_status_result(payment_object)
        return result

    def _to_status_result(self, payment_object: dict) -> PaymentStatusResult:
        status = payment_object.get("status")
        amount_value = payment_object.get("amount", {}).get("value", "0")
        return PaymentStatusResult(
            provider_payment_id=payment_object["id"],
            is_succeeded=status == "succeeded",
            is_canceled=status == "canceled",
            amount=self._amount_str_to_kopecks(amount_value),
            raw_response=json.dumps(payment_object, ensure_ascii=False),
        )

    def _is_trusted_ip(self, remote_ip: str) -> bool:
        return any(remote_ip.startswith(prefix) for prefix in TRUSTED_WEBHOOK_IP_PREFIXES)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: dict | None = None,
        idempotence_key: str | None = None,
    ) -> dict:
        headers = {"Authorization": self._auth_header, "Content-Type": "application/json"}
        if idempotence_key:
            headers["Idempotence-Key"] = idempotence_key

        last_error: Exception | None = None
        for delay in (0, *PAYMENT_RETRY_DELAYS_SECONDS):
            if delay:
                await asyncio.sleep(delay)
            try:
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.request(
                        method,
                        url,
                        headers=headers,
                        json=json_body,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as response:
                        data = await response.json()
                        if 400 <= response.status < 500:
                            # Ошибка на стороне запроса (неверные данные, авторизация) —
                            # повторять бессмысленно.
                            raise PaymentProviderError(f"YooKassa {response.status}: {data}")
                        if response.status >= 500:
                            raise _RetryableError(f"YooKassa {response.status}: {data}")
                        return data
            except _RetryableError as exc:
                last_error = exc
                logger.warning("YooKassa request failed, will retry: %s", exc)
            except aiohttp.ClientError as exc:
                last_error = exc
                logger.warning("YooKassa request failed, will retry: %s", exc)

        raise PaymentProviderError(
            f"YooKassa API unavailable after {len(PAYMENT_RETRY_DELAYS_SECONDS)} retries"
        ) from last_error

    @staticmethod
    def _kopecks_to_amount_str(kopecks: int) -> str:
        return f"{kopecks / 100:.2f}"

    @staticmethod
    def _amount_str_to_kopecks(amount_str: str) -> int:
        return round(float(amount_str) * 100)
