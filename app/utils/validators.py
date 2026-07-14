"""Валидация пользовательского ввода. Никогда не бросают технические исключения наружу."""

from __future__ import annotations

from app.utils.constants import AVAILABLE_VOLUMES_LITERS, MIN_ADDRESS_LENGTH, MIN_CITY_LENGTH


class ValidationResult:
    """Результат проверки ввода: успех или дружелюбное сообщение об ошибке."""

    __slots__ = ("is_valid", "error_message")

    def __init__(self, is_valid: bool, error_message: str = "") -> None:
        self.is_valid = is_valid
        self.error_message = error_message

    @classmethod
    def ok(cls) -> ValidationResult:
        return cls(True)

    @classmethod
    def error(cls, message: str) -> ValidationResult:
        return cls(False, message)


def validate_city(value: str) -> ValidationResult:
    value = value.strip()
    if len(value) < MIN_CITY_LENGTH:
        return ValidationResult.error(
            "Похоже, в названии города есть неточность. Проверьте его ещё раз."
        )
    return ValidationResult.ok()


def validate_address(value: str) -> ValidationResult:
    value = value.strip()
    if len(value) < MIN_ADDRESS_LENGTH:
        return ValidationResult.error("Похоже, в адресе есть неточность. Проверьте его ещё раз.")
    return ValidationResult.ok()


def validate_house(value: str) -> ValidationResult:
    value = value.strip()
    if not value:
        return ValidationResult.error("Похоже, номер дома не указан. Проверьте его ещё раз.")
    return ValidationResult.ok()


def validate_volume(volume: int) -> ValidationResult:
    if volume not in AVAILABLE_VOLUMES_LITERS:
        return ValidationResult.error("Такой объём недоступен. Выберите один из предложенных.")
    return ValidationResult.ok()


def parse_positive_amount(raw_value: str) -> tuple[float | None, str | None]:
    """Парсит введённое администратором денежное значение. Возвращает (значение, ошибка)."""
    normalized = raw_value.strip().replace(",", ".")
    try:
        value = float(normalized)
    except ValueError:
        return None, "Введите корректное числовое значение."
    if value <= 0:
        return None, "Значение должно быть больше нуля."
    if value > 10_000_000:
        return None, "Значение слишком большое. Проверьте, пожалуйста, ввод."
    return value, None


def parse_non_negative_int(raw_value: str) -> tuple[int | None, str | None]:
    """Парсит введённое администратором целое неотрицательное число (например, объём в литрах)."""
    normalized = raw_value.strip()
    if not normalized.isdigit():
        return None, "Введите корректное числовое значение."
    value = int(normalized)
    if value > 1_000_000:
        return None, "Значение слишком большое. Проверьте, пожалуйста, ввод."
    return value, None
