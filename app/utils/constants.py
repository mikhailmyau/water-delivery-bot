"""Бизнес-константы проекта. Никаких магических чисел в коде — только здесь."""

from __future__ import annotations

from app.config import BASE_DIR

LOG_FILE_PATH = BASE_DIR / "logs" / "app.log"

# Вода доставляется бутылями по 20 л. Свободный ввод объёма запрещён — только
# счётчик бутылей в интерфейсе (см. app/handlers/catalog.py).
BOTTLE_VOLUME_LITERS = 20
MIN_BOTTLES = 2  # 40 л — минимальный заказ (везём одной ходкой курьера/такси)
MAX_BOTTLES = 10  # 200 л — максимальный заказ за раз
MIN_VOLUME_LITERS = MIN_BOTTLES * BOTTLE_VOLUME_LITERS
MAX_VOLUME_LITERS = MAX_BOTTLES * BOTTLE_VOLUME_LITERS

# Валидация оформления заказа
MIN_CITY_LENGTH = 2
MIN_ADDRESS_LENGTH = 5

# Антифлуд
START_THROTTLE_SECONDS = 1.0

# Через сколько часов после первого /start без единого заказа отправить
# разовое напоминание со спецпредложением (см. app/scheduler/jobs.py).
FIRST_ORDER_NUDGE_DELAY_HOURS = 6

# Ограничение "последних заказов" в админ-панели
ADMIN_RECENT_ORDERS_LIMIT = 20

# Ретраи обращения к платёжному API (секунды между попытками)
PAYMENT_RETRY_DELAYS_SECONDS: tuple[int, ...] = (1, 2, 5, 10)

# Валюта
CURRENCY_CODE = "RUB"
