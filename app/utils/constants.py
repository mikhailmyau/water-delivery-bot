"""Бизнес-константы проекта. Никаких магических чисел в коде — только здесь."""

from __future__ import annotations

from app.config import BASE_DIR

LOG_FILE_PATH = BASE_DIR / "logs" / "app.log"

# Объём заказа (в литрах). Свободный ввод объёма запрещён ТЗ — только выбор из списка.
MIN_VOLUME_LITERS = 120
MAX_VOLUME_LITERS = 200
VOLUME_STEP_LITERS = 20
AVAILABLE_VOLUMES_LITERS: tuple[int, ...] = tuple(
    range(MIN_VOLUME_LITERS, MAX_VOLUME_LITERS + VOLUME_STEP_LITERS, VOLUME_STEP_LITERS)
)

# Валидация оформления заказа
MIN_CITY_LENGTH = 2
MIN_ADDRESS_LENGTH = 5

# Антифлуд
START_THROTTLE_SECONDS = 1.0
PROMO_CHECK_LIMIT = 3
PROMO_CHECK_WINDOW_SECONDS = 60

# Ограничение "последних заказов" в админ-панели
ADMIN_RECENT_ORDERS_LIMIT = 20

# Ретраи обращения к платёжному API (секунды между попытками)
PAYMENT_RETRY_DELAYS_SECONDS: tuple[int, ...] = (1, 2, 5, 10)

# Валюта
CURRENCY_CODE = "RUB"
