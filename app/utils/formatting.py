"""Форматирование сообщений и карточек. Единый источник текста для handlers и сервисов.

Бот работает в режиме ParseMode.HTML (см. app/loader.py), поэтому любой
пользовательский свободный текст (город/улица/дом, введённые вручную),
попадающий в сообщение, экранируется через `_esc` — иначе символы вроде
`<` или `&` в адресе сломают разметку и отправка сообщения упадёт с ошибкой
Telegram API.

Стиль оформления — по заданному образцу: короткие "карточки"-цитаты
(`<blockquote>`) для цен/итогов/ключевых фактов, обычный текст для связок
между ними. Каждый вызов `<blockquote>...</blockquote>` рендерится в
Telegram отдельным зелёным блоком, поэтому несколько таких блоков подряд в
одном сообщении выглядят как отдельные карточки — это сделано намеренно.
"""

from __future__ import annotations

from html import escape as _html_escape

from app.content import (
    REVIEWS_GROUP_URL,
    WATER_TYPE_LABELS,
    WATER_TYPE_ORDER,
)
from app.database.models.order import Order
from app.database.models.water_type import WaterType
from app.utils.constants import (
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


def format_water_types_quote(prices: dict[WaterType, int], *, compact_unit: bool = False) -> str:
    """`compact_unit=True` — короткая форма "77 ₽/л" (экран каталога),
    иначе — развёрнутая "77 ₽ за литр" (главный экран)."""
    lines = ["💧 <b>В НАЛИЧИИ С ДОСТАВКОЙ:</b>"]
    for water_type in WATER_TYPE_ORDER:
        label = WATER_TYPE_LABELS[water_type]
        price = format_price(prices[water_type])
        unit = "/л" if compact_unit else " за литр"
        lines.append(f"{label} — {price}{unit}")
    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def format_welcome_message(intro_text: str, prices: dict[WaterType, int]) -> str:
    """Главный экран: редактируемый вступительный абзац + всегда актуальные
    цены. Цены не "зашиты" в интро специально — если администратор поменяет
    их через /price, здесь мгновенно будут новые значения без правки текста."""
    water_block = format_water_types_quote(prices)
    reviews_block = f"<blockquote>💬 Отзывы наших клиентов: {REVIEWS_GROUP_URL}</blockquote>"
    return f"{intro_text}\n\n{water_block}\n\n{reviews_block}"


def format_delivery_info() -> str:
    """Экран кнопки «Доставка». Точный срок для конкретного города покупатель
    увидит только на оформлении заказа (там он его выбирает) — здесь только
    общая политика, без обращения к БД."""
    intro = "<i>🚚 Доставка в бутылях по всей России — курьером или такси прямо " "до двери.</i>"
    limits_block = (
        "<blockquote>"
        f"📈 Минимум — {MIN_BOTTLES} бутыли ({MIN_VOLUME_LITERS} л)\n"
        f"📉 Максимум — {MAX_BOTTLES} бутылей ({MAX_VOLUME_LITERS} л)"
        "</blockquote>"
    )
    included_block = (
        "<blockquote>✅ Стоимость доставки включена в цену воды — "
        "доплачивать за курьера не нужно!</blockquote>"
    )
    return f"{intro}\n\n{limits_block}\n\n{included_block}"


def format_water_type_prompt(prices: dict[WaterType, int]) -> str:
    return f"{format_water_types_quote(prices, compact_unit=True)}\n\nВыберите марку воды:"


def format_water_type_selected_prompt(water_type: WaterType, price_per_liter: int) -> str:
    label = WATER_TYPE_LABELS[water_type]
    price = format_price(price_per_liter)
    quote = f"<blockquote>💧 Вода: <b>{label}</b> — {price} за литр</blockquote>"
    return f"{quote}\n\nВыберите объём:"


def format_volume_calculation(
    water_type: WaterType, volume: int, price_per_liter: int, total_price: int
) -> str:
    label = WATER_TYPE_LABELS[water_type]
    lines = [
        f"💧 Вода: <b>{label}</b> — {format_price(price_per_liter)} за литр",
        f"🔢 Выбранный объём: {volume} литров",
        f"💰 Сумма к оплате: {format_price(total_price)}",
    ]
    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def format_order_card(order: Order) -> str:
    label = WATER_TYPE_LABELS[order.water_type]
    lines = [
        f"🛒 <b>ВАШ ЗАКАЗ №{order.order_number}</b>",
        "",
        f"🏙 Город: {_esc(order.city)}",
        f"🏠 Улица: {_esc(order.street)}, {_esc(order.house)}",
        "",
        "<b>Содержимое заказа:</b>",
        f"💧 {label} — {order.bottles} {pluralize_bottles(order.bottles)} ({order.volume} л)",
        f"🚚 Доставка: включена, срок — {order.delivery_days_estimate}",
        "",
        f"💰 К оплате: {format_price(order.total_price)}",
    ]
    return "<blockquote>" + "\n".join(lines) + "</blockquote>"


def format_payment_success(order: Order) -> str:
    lines = [
        "🎉 <b>Спасибо! Оплата успешно получена.</b>",
        "",
        f"Номер заказа: №{order.order_number}",
        "Статус: Оплачен",
        f"Ожидаемый срок доставки: {order.delivery_days_estimate}",
    ]
    return (
        "<blockquote>"
        + "\n".join(lines)
        + "</blockquote>"
        + "\n\nМы сообщим, когда заказ перейдёт к доставке."
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
        f"Заказ №{order.order_number}",
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


def format_order_cancelled_message() -> str:
    return "❌ Заказ отменён."
