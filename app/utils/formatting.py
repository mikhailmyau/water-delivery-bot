"""Форматирование сообщений и карточек. Единый источник текста для handlers и сервисов."""

from __future__ import annotations

from app.database.models.order import Order
from app.database.models.settings import BotSettings
from app.utils.money import format_price


def format_catalog_card(settings: BotSettings) -> str:
    return (
        "━━━━━━━━━━━━━━\n"
        "💧 Питьевая вода\n"
        "━━━━━━━━━━━━━━\n"
        "✔ Высокое качество\n"
        "✔ Доставка по России\n"
        "✔ Быстрое оформление\n"
        "━━━━━━━━━━━━━━\n"
        f"Цена: {format_price(settings.price_per_liter)} / литр\n"
        f"Минимум: 120 л\n"
        f"Максимум: 200 л"
    )


def format_volume_calculation(
    volume: int,
    price_per_liter: int,
    product_price: int,
    delivery_price: int,
    is_free_delivery: bool,
    total_price: int,
) -> str:
    delivery_line = "Бесплатно" if is_free_delivery else format_price(delivery_price)
    return (
        "Вы выбрали:\n"
        f"{volume} литров\n\n"
        f"Цена: {format_price(price_per_liter)} / литр\n"
        f"Стоимость: {format_price(product_price)}\n"
        f"Доставка: {delivery_line}\n\n"
        f"Итого: {format_price(total_price)}"
    )


def format_order_card(order: Order, *, editable: bool = True) -> str:
    delivery_line = "Бесплатно" if order.delivery_price == 0 else format_price(order.delivery_price)
    lines = [
        "━━━━━━━━━━━━━━",
        "Ваш заказ" if editable else f"Заказ #{order.order_number}",
        "━━━━━━━━━━━━━━",
        f"📍 {order.city}",
        f"🏠 {order.street}, {order.house}",
        f"💧 {order.volume} литров",
        f"💰 Стоимость: {format_price(order.price_per_liter * order.volume)}",
        f"🚚 Доставка: {delivery_line}",
    ]
    if order.discount:
        lines.append(f"🎁 Скидка: -{format_price(order.discount)}")
    lines += [
        "━━━━━━━━━━━━━━",
        "ИТОГО",
        format_price(order.total_price),
        "━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)


def format_payment_success(order: Order, delivery_days: str) -> str:
    return (
        "━━━━━━━━━━━━━━\n"
        "Спасибо!\n"
        "Оплата успешно получена.\n\n"
        f"Номер заказа: #{order.order_number}\n"
        "Статус: Оплачен\n"
        f"Средний срок доставки: {delivery_days}\n"
        "━━━━━━━━━━━━━━\n"
        "Мы сообщим, когда заказ перейдёт к доставке."
    )


def format_admin_new_order_card(order: Order) -> str:
    user = order.user
    username = f"@{user.username}" if user and user.username else "—"
    status_line = "✅ ОПЛАЧЕН" if order.payment_status.value == "success" else "⏳ ОЖИДАЕТ ОПЛАТЫ"
    lines = [
        "━━━━━━━━━━━━━━",
        "НОВЫЙ ЗАКАЗ",
        "━━━━━━━━━━━━━━",
        f"Заказ #{order.order_number}",
        f"Имя: {user.full_name if user else '—'}",
        f"Telegram ID: {user.telegram_id if user else '—'}",
        f"Username: {username}",
        f"Город: {order.city}",
        f"Адрес: {order.street}, {order.house}",
        f"Объём: {order.volume} л",
        f"Цена за литр: {format_price(order.price_per_liter)}",
        f"Стоимость доставки: {format_price(order.delivery_price)}",
    ]
    if order.promo_code_id:
        lines.append(f"Промокод: -{format_price(order.discount)}")
    lines += [
        f"Итог: {format_price(order.total_price)}",
        "━━━━━━━━━━━━━━",
        status_line,
    ]
    return "\n".join(lines)


def format_reminder_message(*, second: bool) -> str:
    if second:
        return (
            "━━━━━━━━━━━━━━\n"
            "Мы сохранили ваш заказ. Он ещё доступен.\n\n"
            "Если он вам актуален — завершите оформление.\n"
            "━━━━━━━━━━━━━━"
        )
    return (
        "━━━━━━━━━━━━━━\n"
        "Вы почти завершили оформление.\n"
        "Ваш заказ всё ещё ожидает оплату.\n\n"
        "Если хотите продолжить — нажмите кнопку ниже.\n"
        "━━━━━━━━━━━━━━"
    )
