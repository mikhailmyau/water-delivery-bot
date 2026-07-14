"""Настройка логирования: консоль для разработки, файл — всегда.

Логируется всё: ошибки, платежи, авторизации, заказы, изменения цен,
промокоды, ошибки API (ТЗ, глава 23). Формат строки: дата, время, уровень,
логгер, сообщение — поле логгера обычно и есть «кто» и «какое действие».
"""

from __future__ import annotations

import logging
import logging.handlers

from app.config import settings
from app.utils.constants import LOG_FILE_PATH

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Библиотеки логируют очень многословно на DEBUG — приглушаем их отдельно.
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
