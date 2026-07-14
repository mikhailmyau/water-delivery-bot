"""Тесты валидаторов пользовательского ввода."""

from __future__ import annotations

from app.utils.validators import (
    parse_non_negative_int,
    parse_positive_amount,
    validate_address,
    validate_city,
    validate_house,
    validate_volume,
)


def test_validate_city_too_short():
    result = validate_city("A")
    assert result.is_valid is False
    assert "неточность" in result.error_message


def test_validate_city_ok():
    assert validate_city("Москва").is_valid is True


def test_validate_address_too_short():
    assert validate_address("ул.").is_valid is False


def test_validate_address_ok():
    assert validate_address("Ленина 25").is_valid is True


def test_validate_house_empty():
    assert validate_house("   ").is_valid is False


def test_validate_volume_allowed():
    assert validate_volume(160).is_valid is True


def test_validate_volume_rejected():
    assert validate_volume(150).is_valid is False


def test_parse_positive_amount_valid():
    value, error = parse_positive_amount("78,5")
    assert error is None
    assert value == 78.5


def test_parse_positive_amount_rejects_zero():
    value, error = parse_positive_amount("0")
    assert value is None
    assert error is not None


def test_parse_positive_amount_rejects_letters():
    value, error = parse_positive_amount("abc")
    assert value is None
    assert error is not None


def test_parse_non_negative_int_valid():
    value, error = parse_non_negative_int("40")
    assert error is None
    assert value == 40


def test_parse_non_negative_int_rejects_negative_text():
    value, error = parse_non_negative_int("-5")
    assert value is None
    assert error is not None
