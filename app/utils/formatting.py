"""Форматирование сообщений и карточек. Единый источник текста для handlers и сервисов.

Бот работает в режиме ParseMode.HTML (см. app/loader.py), поэтому любой
пользовательский свободный текст (город/улица/дом, введённые вручную),
попадающий в сообщение, экранируется через `_esc` — иначе символы вроде
`<` или `&` в адресе сломают разметку и отправка сообщения упадёт с ошибкой
Telegram API.
"""

from __future__ import annotations

from html import escape as _html_escape

from app.content import (
    GUARANTEES,
    REVIEWS_GROUP_URL,
    SOCIAL_PROOF_LINE,
    SUPPLY_CHANNEL_URL,
    WATER_TYPE_DESCRIPTIONS,
    WATER_TYPE_LABELS,
    WATER_TYPE_ORDER,
)
from app.database.models.order import Order
from app.database.models.water_type import WaterType
from app.utils.constants import (
    BOTTLE_VOLUME_LITERS,
    MAX_BOTTLES,
    MAX_VOLUME_LITERS,
    MIN_BOTTLES,
    MIN_VOLUME_LITERS,
)
from app.utils.money import format_price


def _esc(value: object) -> str:
    return _html_escape(str(value), quote=False)


def pluralize_bottles(count: int) -> str:
    """Склонение слова "бутыль" под число (2 бутыли, 5 бутылей, 21 бутыль...)."""
    if 11 <= count % 100 <= 14:
        return "бутылей"
    last_digit = count % 10
    if last_digit == 1:
        return "бутыль"
    if 2 <= last_digit <= 4:
        return "бутыли"
    return "бутылей"


def format_water_types_quote(prices: dict[WaterType, int]) -> str:
    lines = ["💧 <b>Виды воды</b>"]
    for water_type in WATER_TYPE_ORDER:
        label = WATER_TYPE_LABELS[water_type]
        description = WATER_TYPE_DESCRIPTIONS[water_type]
        price = format_price(prices[water_type])
        lines.append(f"<b>{label}</b> — {description} — {price}/л")
    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def _format_guarantees_block() -> str:
    lines = ["<b>Гарантии</b>"]
    lines += [f"✅ {item}" for item in GUARANTEES]
    return "\n".join(lines)


def format_welcome_message(intro_text: str, prices: dict[WaterType, int]) -> str:
    """Главный экран: редактируемый вступительный абзац + всегда актуальные
    цены, гарантии и ссылки. Цены не "зашиты" в интро специально — если
    администратор поменяет их через /price, здесь мгновенно будут новые
    значения без правки текста вручную."""
    lines = [
        intro_text,
        "",
        format_water_types_quote(prices),
        "",
        "🚚 Доставка по всей России уже включена в стоимость — от 1 часа до "
        "5 дней в зависимости от города.",
        f"📦 Заказ от {MIN_BOTTLES} бутылей ({MIN_VOLUME_LITERS} л) "
        f"до {MAX_BOTTLES} ({MAX_VOLUME_LITERS} л).",
        "",
        _format_guarantees_block(),
        "",
        f"⭐ {SOCIAL_PROOF_LINE}",
        f"📢 Канал с поставками: {SUPPLY_CHANNEL_URL}",
        f"💬 Отзывы наших клиентов: {REVIEWS_GROUP_URL}",
    ]
    return "\n".join(lines)


def format_delivery_info() -> str:
    """Экран кнопки «Доставка». Точный срок для конкретного города покупатель
    увидит только на оформлении заказа (там он его выбирает) — здесь только
    общая политика, без обращения к БД."""
    return (
        "━━━━━━━━━━━━━━\n"
        "🚚 <b>Доставка</b>\n"
        "━━━━━━━━━━━━━━\n"
        f"Возим по всей России — курьером или такси прямо до двери, "
        f"в бутылях по {BOTTLE_VOLUME_LITERS} л.\n\n"
        f"Минимальный заказ — {MIN_BOTTLES} бутыли ({MIN_VOLUME_LITERS} л), "
        f"максимальный — {MAX_BOTTLES} ({MAX_VOLUME_LITERS} л).\n\n"
        "Стоимость доставки уже включена в цену воды — доплачивать за "
        "курьера не нужно.\n\n"
        "Срок зависит от города:\n"
        "🟢 до 1 дня — Москва и Центральная Россия\n"
        "🟡 до 3 дней — большая часть России и Урал\n"
        "🔴 до 5 дней — Сибирь, Дальний Восток и отдалённые регионы\n\n"
        "Точный срок для вашего города вы увидите при оформлении заказа, "
        "как только укажете город доставки.\n"
        "━━━━━━━━━━━━━━"
    )


def format_water_type_prompt(prices: dict[WaterType, int]) -> str:
    return f"{format_water_types_quote(prices)}\n\nВыберите вид воды:"


def format_bottle_calculation(
    water_type: WaterType, bottles: int, price_per_liter: int, total_price: int
) -> str:
    label = WATER_TYPE_LABELS[water_type]
    volume = bottles * BOTTLE_VOLUME_LITERS
    lines = [
        f"💧 Вода: <b>{label}</b> ({format_price(price_per_liter)}/л)",
        f"🔢 {bottles} {pluralize_bottles(bottles)} по {BOTTLE_VOLUME_LITERS} л — {volume} л",
        "🚚 Доставка включена в стоимость",
        "",
        f"<b>Итого: {format_price(total_price)}</b>",
    ]
    return "\n".join(lines)


def format_order_card(order: Order, *, editable: bool = True) -> str:
    label = WATER_TYPE_LABELS[order.water_type]
    lines = [
        "━━━━━━━━━━━━━━",
        "Ваш заказ" if editable else f"Заказ #{order.order_number}",
        "━━━━━━━━━━━━━━",
        f"📍 {_esc(order.city)}",
        f"🏠 {_esc(order.street)}, {_esc(order.house)}",
        f"💧 {label} — {order.bottles} {pluralize_bottles(order.bottles)} ({order.volume} л)",
        f"🚚 Доставка: включена, срок — {order.delivery_days_estimate}",
        "━━━━━━━━━━━━━━",
        "ИТОГО",
        format_price(order.total_price),
        "━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)


def format_payment_success(order: Order) -> str:
    return (
        "━━━━━━━━━━━━━━\n"
        "🎉 Спасибо! Оплата успешно получена.\n\n"
        f"Номер заказа: #{order.order_number}\n"
        "Статус: Оплачен\n"
        f"Ожидаемый срок доставки: {order.delivery_days_estimate}\n"
        "━━━━━━━━━━━━━━\n"
        "Мы сообщим, когда заказ перейдёт к доставке."
    )


def format_admin_new_order_card(order: Order) -> str:
    user = order.user
    username = f"@{user.username}" if user and user.username else "—"
    label = WATER_TYPE_LABELS[order.water_type]
    status_line = "✅ ОПЛАЧЕН" if order.payment_status.value == "success" else "⏳ ОЖИДАЕТ ОПЛАТЫ"
    city_line = f"Город: {_esc(order.city)}"
    if not order.city_matched:
        city_line += " ⚠️ не из справочника — уточните срок вручную"
    lines = [
        "━━━━━━━━━━━━━━",
        "НОВЫЙ ЗАКАЗ",
        "━━━━━━━━━━━━━━",
        f"Заказ #{order.order_number}",
        f"Имя: {_esc(user.full_name) if user else '—'}",
        f"Telegram ID: {user.telegram_id if user else '—'}",
        f"Username: {username}",
        city_line,
        f"Адрес: {_esc(order.street)}, {_esc(order.house)}",
        f"Вода: {label} — {order.bottles} {pluralize_bottles(order.bottles)} ({order.volume} л)",
        f"Цена за литр: {format_price(order.price_per_liter)}",
        f"Обещанный срок доставки: {order.delivery_days_estimate}",
        f"Итог: {format_price(order.total_price)}",
        "━━━━━━━━━━━━━━",
        status_line,
    ]
    return "\n".join(lines)


def format_reminder_message(*, second: bool) -> str:
    if second:
        return (
            "━━━━━━━━━━━━━━\n"
            "💧 Мы сохранили ваш заказ, он ещё доступен.\n\n"
            "Если он вам актуален — завершите оформление, это займёт минуту.\n"
            "━━━━━━━━━━━━━━"
        )
    return (
        "━━━━━━━━━━━━━━\n"
        "⏳ Вы почти завершили оформление.\n"
        "Ваш заказ всё ещё ожидает оплаты.\n\n"
        "Если хотите продолжить — нажмите кнопку ниже.\n"
        "━━━━━━━━━━━━━━"
    )


def format_first_order_nudge() -> str:
    """Разовое сообщение тем, кто запустил бота, но за 6 часов так и не заказал
    (см. app/scheduler/jobs.py::send_first_order_nudges). Делаем акцент на то,
    что доставка и так бесплатна для любого заказа — это не выдумка ради
    письма, а реальное правило проекта (см. format_delivery_info)."""
    return (
        "👋 Вижу, вы заглянули к нам, но так и не оформили первый заказ.\n\n"
        "🚚 Доставка по всей России уже включена в стоимость воды — платите "
        "только за саму воду, никаких доплат курьеру или такси.\n\n"
        "Выберите вид воды и объём — оформление займёт меньше минуты 👇"
    )
