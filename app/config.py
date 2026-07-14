"""Конфигурация приложения. Все секреты и параметры окружения читаются из .env."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Настройки, читаемые из переменных окружения (.env)."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    admin_ids: Annotated[list[int], NoDecode] = Field(default_factory=list, alias="ADMIN_IDS")
    admin_group_id: int | None = Field(default=None, alias="ADMIN_GROUP_ID")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./storage/db.sqlite3",
        alias="DATABASE_URL",
    )

    payment_provider: str = Field(default="mock", alias="PAYMENT_PROVIDER")
    payment_api_key: str | None = Field(default=None, alias="PAYMENT_API_KEY")
    payment_secret: str | None = Field(default=None, alias="PAYMENT_SECRET")

    public_base_url: str = Field(default="http://localhost:8080", alias="PUBLIC_BASE_URL")
    payment_webhook_host: str = Field(default="0.0.0.0", alias="PAYMENT_WEBHOOK_HOST")
    payment_webhook_port: int = Field(default=8080, alias="PAYMENT_WEBHOOK_PORT")
    payment_webhook_path: str = Field(default="/payments/webhook", alias="PAYMENT_WEBHOOK_PATH")

    reminder_first_delay_minutes: int = Field(default=30, alias="REMINDER_FIRST_DELAY_MINUTES")
    reminder_second_delay_minutes: int = Field(default=180, alias="REMINDER_SECOND_DELAY_MINUTES")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    debug: bool = Field(default=False, alias="DEBUG")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return [int(value)]

    @field_validator("admin_group_id", mode="before")
    @classmethod
    def _parse_admin_group_id(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        return int(value)


settings = Settings()
