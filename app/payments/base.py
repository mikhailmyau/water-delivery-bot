"""Абстрактный платёжный провайдер.

Любой платёжный сервис подключается реализацией этого интерфейса — без единой
правки в бизнес-логике (services, handlers). См. ТЗ, глава «Платёжная система».
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreatedPayment:
    """Результат создания платежа у провайдера."""

    provider_payment_id: str
    payment_url: str
    raw_response: str


@dataclass(frozen=True, slots=True)
class PaymentStatusResult:
    """Статус платежа, полученный от провайдера (через опрос или webhook)."""

    provider_payment_id: str
    is_succeeded: bool
    is_canceled: bool
    amount: int
    """Сумма в копейках, подтверждённая провайдером."""

    raw_response: str


class PaymentProvider(ABC):
    """Общий интерфейс для всех платёжных провайдеров."""

    name: str

    @abstractmethod
    async def create_payment(
        self,
        *,
        order_id: int,
        order_number: str,
        amount: int,
        description: str,
        return_url: str,
    ) -> CreatedPayment:
        """Создаёт платёж у провайдера и возвращает ссылку на оплату."""

    @abstractmethod
    async def get_status(self, provider_payment_id: str) -> PaymentStatusResult:
        """Запрашивает актуальный статус платежа напрямую у провайдера."""

    @abstractmethod
    def parse_webhook(
        self, body: bytes, headers: dict[str, str], remote_ip: str | None
    ) -> PaymentStatusResult | None:
        """Разбирает и проверяет webhook-уведомление. None — если событие нужно игнорировать."""
