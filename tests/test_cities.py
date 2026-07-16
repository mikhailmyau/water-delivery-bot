"""Тесты справочника городов доставки (app/data/cities.py)."""

from __future__ import annotations

from app.data.cities import (
    CITIES,
    FALLBACK_TIER_DAYS,
    available_letters,
    cities_by_letter,
    estimate_label,
    get_city_by_id,
)


def test_no_duplicate_ids():
    ids = [city.id for city in CITIES]
    assert len(ids) == len(set(ids))


def test_no_duplicate_names():
    names = [city.name for city in CITIES]
    assert len(names) == len(set(names))


def test_all_tiers_are_valid():
    assert {city.tier_days for city in CITIES} <= {1, 3, 5}


def test_moscow_is_next_day():
    moscow = next(city for city in CITIES if city.name == "Москва")
    assert moscow.tier_days == 1


def test_get_city_by_id_roundtrip():
    sample = CITIES[0]
    assert get_city_by_id(sample.id) is sample


def test_get_city_by_id_missing_returns_none():
    assert get_city_by_id(-1) is None


def test_available_letters_cover_all_cities():
    letters = available_letters()
    for city in CITIES:
        assert city.name[0].upper() in letters


def test_cities_by_letter_only_returns_matching_and_sorted():
    cities = cities_by_letter("м")
    assert all(city.name.upper().startswith("М") for city in cities)
    assert [city.name for city in cities] == sorted(city.name for city in cities)


def test_estimate_label_known_tiers():
    assert estimate_label(1) == "до 1 дня"
    assert estimate_label(3) == "до 3 дней"
    assert estimate_label(5) == "до 5 дней"


def test_estimate_label_fallback_for_unknown_tier():
    assert estimate_label(999) == estimate_label(FALLBACK_TIER_DAYS)
