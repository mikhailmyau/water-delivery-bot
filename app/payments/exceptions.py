"""Исключения платёжного слоя."""

from __future__ import annotations


class PaymentProviderError(Exception):
    """Платёжный провайдер вернул ошибку или недоступен после всех повторов."""
