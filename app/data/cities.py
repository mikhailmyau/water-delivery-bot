"""Справочник городов доставки и грубая оценка срока по удалённости от склада.

Склад один, в Москве. Точного расчёта маршрута/расстояния бот не делает —
вместо этого у каждого города есть "уровень" (`tier_days`), одна из трёх
величин, которые видит покупатель: 1 / 3 / 5 дней. Разметка сделана вручную,
по географии (Центральная Россия — 1 день, остальная Европейская часть и
Урал — 3 дня, Сибирь/Дальний Восток/Крайний Север/Калининград — 5 дней).
Это справочные, а не расчётные данные: если логистика поменяется, тариф
конкретного города меняется одной строкой ниже.

Как добавить город:
    Допишите `CityEntry(id=..., name="...", tier_days=...)` в конец CITIES.
    `id` — просто следующее свободное число, не переиспользуйте старые id
    (на них могут ссылаться уже открытые у пользователей клавиатуры).
"""

from __future__ import annotations

from dataclasses import dataclass

TIER_LABELS: dict[int, str] = {
    1: "до 1 дня",
    3: "до 3 дней",
    5: "до 5 дней",
}

# Тариф, который присваивается городу, введённому вручную (не найден в списке).
# Намеренно самый осторожный — лучше приятно удивить, чем не успеть к обещанному сроку.
FALLBACK_TIER_DAYS = 5


@dataclass(frozen=True, slots=True)
class CityEntry:
    """Один город в справочнике доставки."""

    id: int
    name: str
    tier_days: int
    """1, 3 или 5 — см. TIER_LABELS."""


CITIES: tuple[CityEntry, ...] = (
    # --- до 1 дня: Москва, область и соседние регионы ЦФО ---
    CityEntry(1, "Москва", 1),
    CityEntry(2, "Балашиха", 1),
    CityEntry(3, "Химки", 1),
    CityEntry(4, "Подольск", 1),
    CityEntry(5, "Королёв", 1),
    CityEntry(6, "Мытищи", 1),
    CityEntry(7, "Люберцы", 1),
    CityEntry(8, "Одинцово", 1),
    CityEntry(9, "Красногорск", 1),
    CityEntry(10, "Домодедово", 1),
    CityEntry(11, "Электросталь", 1),
    CityEntry(12, "Коломна", 1),
    CityEntry(13, "Серпухов", 1),
    CityEntry(14, "Ногинск", 1),
    CityEntry(15, "Раменское", 1),
    CityEntry(16, "Жуковский", 1),
    CityEntry(17, "Пушкино", 1),
    CityEntry(18, "Щёлково", 1),
    CityEntry(19, "Долгопрудный", 1),
    CityEntry(20, "Реутов", 1),
    CityEntry(21, "Видное", 1),
    CityEntry(22, "Сергиев Посад", 1),
    CityEntry(23, "Орехово-Зуево", 1),
    CityEntry(24, "Ступино", 1),
    CityEntry(25, "Наро-Фоминск", 1),
    CityEntry(26, "Воскресенск", 1),
    CityEntry(27, "Клин", 1),
    CityEntry(28, "Дмитров", 1),
    CityEntry(29, "Егорьевск", 1),
    CityEntry(30, "Кашира", 1),
    CityEntry(31, "Тула", 1),
    CityEntry(32, "Новомосковск", 1),
    CityEntry(33, "Калуга", 1),
    CityEntry(34, "Обнинск", 1),
    CityEntry(35, "Рязань", 1),
    CityEntry(36, "Владимир", 1),
    CityEntry(37, "Ковров", 1),
    CityEntry(38, "Муром", 1),
    CityEntry(39, "Александров", 1),
    CityEntry(40, "Тверь", 1),
    CityEntry(41, "Ржев", 1),
    CityEntry(42, "Ярославль", 1),
    CityEntry(43, "Рыбинск", 1),
    CityEntry(44, "Углич", 1),
    CityEntry(45, "Переславль-Залесский", 1),
    CityEntry(46, "Иваново", 1),
    CityEntry(47, "Кинешма", 1),
    CityEntry(48, "Шуя", 1),
    CityEntry(49, "Смоленск", 1),
    CityEntry(50, "Вязьма", 1),
    CityEntry(51, "Кострома", 1),
    CityEntry(52, "Орёл", 1),
    CityEntry(53, "Брянск", 1),
    # --- до 3 дней: остальная Европейская часть России, Урал ---
    CityEntry(54, "Санкт-Петербург", 3),
    CityEntry(55, "Гатчина", 3),
    CityEntry(56, "Выборг", 3),
    CityEntry(57, "Великий Новгород", 3),
    CityEntry(58, "Псков", 3),
    CityEntry(59, "Вологда", 3),
    CityEntry(60, "Череповец", 3),
    CityEntry(61, "Петрозаводск", 3),
    CityEntry(62, "Архангельск", 3),
    CityEntry(63, "Северодвинск", 3),
    CityEntry(64, "Сыктывкар", 3),
    CityEntry(65, "Ухта", 3),
    CityEntry(66, "Воронеж", 3),
    CityEntry(67, "Липецк", 3),
    CityEntry(68, "Тамбов", 3),
    CityEntry(69, "Курск", 3),
    CityEntry(70, "Белгород", 3),
    CityEntry(71, "Старый Оскол", 3),
    CityEntry(72, "Елец", 3),
    CityEntry(73, "Пенза", 3),
    CityEntry(74, "Саранск", 3),
    CityEntry(75, "Нижний Новгород", 3),
    CityEntry(76, "Дзержинск", 3),
    CityEntry(77, "Арзамас", 3),
    CityEntry(78, "Чебоксары", 3),
    CityEntry(79, "Новочебоксарск", 3),
    CityEntry(80, "Йошкар-Ола", 3),
    CityEntry(81, "Киров", 3),
    CityEntry(82, "Ижевск", 3),
    CityEntry(83, "Глазов", 3),
    CityEntry(84, "Казань", 3),
    CityEntry(85, "Набережные Челны", 3),
    CityEntry(86, "Нижнекамск", 3),
    CityEntry(87, "Альметьевск", 3),
    CityEntry(88, "Ульяновск", 3),
    CityEntry(89, "Димитровград", 3),
    CityEntry(90, "Самара", 3),
    CityEntry(91, "Тольятти", 3),
    CityEntry(92, "Сызрань", 3),
    CityEntry(93, "Саратов", 3),
    CityEntry(94, "Энгельс", 3),
    CityEntry(95, "Балаково", 3),
    CityEntry(96, "Волгоград", 3),
    CityEntry(97, "Волжский", 3),
    CityEntry(98, "Астрахань", 3),
    CityEntry(99, "Ростов-на-Дону", 3),
    CityEntry(100, "Таганрог", 3),
    CityEntry(101, "Шахты", 3),
    CityEntry(102, "Новочеркасск", 3),
    CityEntry(103, "Волгодонск", 3),
    CityEntry(104, "Краснодар", 3),
    CityEntry(105, "Сочи", 3),
    CityEntry(106, "Новороссийск", 3),
    CityEntry(107, "Армавир", 3),
    CityEntry(108, "Анапа", 3),
    CityEntry(109, "Ставрополь", 3),
    CityEntry(110, "Пятигорск", 3),
    CityEntry(111, "Кисловодск", 3),
    CityEntry(112, "Ессентуки", 3),
    CityEntry(113, "Невинномысск", 3),
    CityEntry(114, "Майкоп", 3),
    CityEntry(115, "Нальчик", 3),
    CityEntry(116, "Владикавказ", 3),
    CityEntry(117, "Грозный", 3),
    CityEntry(118, "Махачкала", 3),
    CityEntry(119, "Черкесск", 3),
    CityEntry(120, "Пермь", 3),
    CityEntry(121, "Березники", 3),
    CityEntry(122, "Соликамск", 3),
    CityEntry(123, "Екатеринбург", 3),
    CityEntry(124, "Нижний Тагил", 3),
    CityEntry(125, "Каменск-Уральский", 3),
    CityEntry(126, "Первоуральск", 3),
    CityEntry(127, "Челябинск", 3),
    CityEntry(128, "Магнитогорск", 3),
    CityEntry(129, "Златоуст", 3),
    CityEntry(130, "Миасс", 3),
    CityEntry(131, "Уфа", 3),
    CityEntry(132, "Стерлитамак", 3),
    CityEntry(133, "Салават", 3),
    CityEntry(134, "Нефтекамск", 3),
    CityEntry(135, "Оренбург", 3),
    CityEntry(136, "Орск", 3),
    CityEntry(137, "Курган", 3),
    CityEntry(138, "Тюмень", 3),
    CityEntry(139, "Тобольск", 3),
    CityEntry(140, "Ишим", 3),
    # --- до 5 дней: Сибирь, Дальний Восток, Крайний Север, Калининград ---
    CityEntry(141, "Калининград", 5),
    CityEntry(142, "Мурманск", 5),
    CityEntry(143, "Апатиты", 5),
    CityEntry(144, "Норильск", 5),
    CityEntry(145, "Воркута", 5),
    CityEntry(146, "Нарьян-Мар", 5),
    CityEntry(147, "Салехард", 5),
    CityEntry(148, "Ноябрьск", 5),
    CityEntry(149, "Ханты-Мансийск", 5),
    CityEntry(150, "Сургут", 5),
    CityEntry(151, "Нижневартовск", 5),
    CityEntry(152, "Омск", 5),
    CityEntry(153, "Новосибирск", 5),
    CityEntry(154, "Бердск", 5),
    CityEntry(155, "Искитим", 5),
    CityEntry(156, "Томск", 5),
    CityEntry(157, "Северск", 5),
    CityEntry(158, "Кемерово", 5),
    CityEntry(159, "Новокузнецк", 5),
    CityEntry(160, "Ленинск-Кузнецкий", 5),
    CityEntry(161, "Прокопьевск", 5),
    CityEntry(162, "Барнаул", 5),
    CityEntry(163, "Бийск", 5),
    CityEntry(164, "Рубцовск", 5),
    CityEntry(165, "Горно-Алтайск", 5),
    CityEntry(166, "Красноярск", 5),
    CityEntry(167, "Ачинск", 5),
    CityEntry(168, "Абакан", 5),
    CityEntry(169, "Кызыл", 5),
    CityEntry(170, "Иркутск", 5),
    CityEntry(171, "Ангарск", 5),
    CityEntry(172, "Братск", 5),
    CityEntry(173, "Усть-Илимск", 5),
    CityEntry(174, "Улан-Удэ", 5),
    CityEntry(175, "Чита", 5),
    CityEntry(176, "Якутск", 5),
    CityEntry(177, "Нерюнгри", 5),
    CityEntry(178, "Благовещенск", 5),
    CityEntry(179, "Хабаровск", 5),
    CityEntry(180, "Комсомольск-на-Амуре", 5),
    CityEntry(181, "Владивосток", 5),
    CityEntry(182, "Находка", 5),
    CityEntry(183, "Уссурийск", 5),
    CityEntry(184, "Артём", 5),
    CityEntry(185, "Южно-Сахалинск", 5),
    CityEntry(186, "Петропавловск-Камчатский", 5),
    CityEntry(187, "Магадан", 5),
    CityEntry(188, "Биробиджан", 5),
)

_BY_ID: dict[int, CityEntry] = {city.id: city for city in CITIES}


def get_city_by_id(city_id: int) -> CityEntry | None:
    return _BY_ID.get(city_id)


def available_letters() -> list[str]:
    """Буквы, с которых начинается хотя бы один город — для клавиатуры-алфавита."""
    return sorted({city.name[0].upper() for city in CITIES})


def cities_by_letter(letter: str) -> list[CityEntry]:
    letter = letter.upper()
    return sorted(
        (city for city in CITIES if city.name[0].upper() == letter),
        key=lambda city: city.name,
    )


def estimate_label(tier_days: int) -> str:
    return TIER_LABELS.get(tier_days, TIER_LABELS[FALLBACK_TIER_DAYS])
