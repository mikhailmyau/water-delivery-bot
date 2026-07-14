"""Административные inline-клавиатуры."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks.admin import AdminCallback
from app.database.models.order import DeliveryStatus, Order
from app.database.models.promo_code import PromoCode


def build_admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📦 Заказы", callback_data=AdminCallback(section="orders", action="list").pack()
        ),
        InlineKeyboardButton(
            text="💰 Цены", callback_data=AdminCallback(section="price", action="menu").pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🚚 Доставка",
            callback_data=AdminCallback(section="delivery", action="menu").pack(),
        ),
        InlineKeyboardButton(
            text="🎁 Промокоды", callback_data=AdminCallback(section="promo", action="menu").pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📢 Рассылка",
            callback_data=AdminCallback(section="broadcast", action="start").pack(),
        ),
        InlineKeyboardButton(
            text="📈 Аналитика",
            callback_data=AdminCallback(section="analytics", action="menu").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Статистика", callback_data=AdminCallback(section="stats", action="menu").pack()
        ),
        InlineKeyboardButton(
            text="📝 Логи", callback_data=AdminCallback(section="logs", action="menu").pack()
        ),
    )
    return builder.as_markup()


def build_admin_orders_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Последние заказы",
            callback_data=AdminCallback(section="orders", action="recent").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔎 Поиск по номеру",
            callback_data=AdminCallback(section="orders", action="search").pack(),
        ),
        InlineKeyboardButton(
            text="Фильтр: неоплаченные",
            callback_data=AdminCallback(section="orders", action="filter_unpaid").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📤 Экспорт CSV",
            callback_data=AdminCallback(section="orders", action="export").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="menu", action="home").pack()
        )
    )
    return builder.as_markup()


def build_admin_orders_list_keyboard(orders: list[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        builder.row(
            InlineKeyboardButton(
                text=f"#{order.order_number} — {order.city}, {order.volume} л",
                callback_data=AdminCallback(
                    section="orders", action="open", param=str(order.id)
                ).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="orders", action="menu").pack()
        )
    )
    return builder.as_markup()


_DELIVERY_STATUS_LABELS: dict[DeliveryStatus, str] = {
    DeliveryStatus.CREATED: "Создан",
    DeliveryStatus.WAITING_PAYMENT: "Ожидает оплаты",
    DeliveryStatus.PAID: "Оплачен",
    DeliveryStatus.PROCESSING: "В обработке",
    DeliveryStatus.DELIVERING: "В доставке",
    DeliveryStatus.DELIVERED: "Доставлен",
    DeliveryStatus.CANCELLED: "Отменён",
}


def build_admin_order_detail_keyboard(order: Order) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    next_statuses = _next_delivery_statuses(order.delivery_status)
    for status in next_statuses:
        builder.row(
            InlineKeyboardButton(
                text=f"➡ {_DELIVERY_STATUS_LABELS[status]}",
                callback_data=AdminCallback(
                    section="orders", action="set_status", param=f"{order.id}:{status.value}"
                ).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="✉ Написать клиенту",
            callback_data=AdminCallback(
                section="orders", action="message", param=str(order.id)
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=AdminCallback(
                section="orders", action="delete", param=str(order.id)
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="orders", action="recent").pack()
        )
    )
    return builder.as_markup()


def _next_delivery_statuses(current: DeliveryStatus) -> list[DeliveryStatus]:
    order_flow = [
        DeliveryStatus.PAID,
        DeliveryStatus.PROCESSING,
        DeliveryStatus.DELIVERING,
        DeliveryStatus.DELIVERED,
    ]
    if current in order_flow:
        idx = order_flow.index(current)
        return order_flow[idx + 1 : idx + 2] + [DeliveryStatus.CANCELLED]
    if current == DeliveryStatus.CREATED:
        return [DeliveryStatus.CANCELLED]
    return []


def build_admin_price_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Изменить цену", callback_data=AdminCallback(section="price", action="edit").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="menu", action="home").pack()
        )
    )
    return builder.as_markup()


def build_admin_delivery_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Изменить стоимость",
            callback_data=AdminCallback(section="delivery", action="edit_price").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить бесплатную доставку",
            callback_data=AdminCallback(section="delivery", action="edit_free_from").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Изменить сроки",
            callback_data=AdminCallback(section="delivery", action="edit_days").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="menu", action="home").pack()
        )
    )
    return builder.as_markup()


def build_admin_promo_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Создать", callback_data=AdminCallback(section="promo", action="create").pack()
        ),
        InlineKeyboardButton(
            text="Список", callback_data=AdminCallback(section="promo", action="list").pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="menu", action="home").pack()
        )
    )
    return builder.as_markup()


def build_admin_promo_discount_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Фиксированная сумма",
            callback_data=AdminCallback(section="promo", action="type_fixed").pack(),
        ),
        InlineKeyboardButton(
            text="Процент",
            callback_data=AdminCallback(section="promo", action="type_percent").pack(),
        ),
    )
    return builder.as_markup()


def build_admin_promo_list_keyboard(promos: list[PromoCode]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for promo in promos:
        mark = "✅" if promo.is_active else "🚫"
        builder.row(
            InlineKeyboardButton(
                text=f"{mark} {promo.code}",
                callback_data=AdminCallback(
                    section="promo", action="open", param=str(promo.id)
                ).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="promo", action="menu").pack()
        )
    )
    return builder.as_markup()


def build_admin_promo_detail_keyboard(promo: PromoCode) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "🚫 Деактивировать" if promo.is_active else "✅ Активировать"
    builder.row(
        InlineKeyboardButton(
            text=toggle_text,
            callback_data=AdminCallback(
                section="promo", action="toggle", param=str(promo.id)
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=AdminCallback(
                section="promo", action="delete", param=str(promo.id)
            ).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="promo", action="list").pack()
        )
    )
    return builder.as_markup()


def build_admin_broadcast_preview_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Отправить",
            callback_data=AdminCallback(section="broadcast", action="send").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Заново",
            callback_data=AdminCallback(section="broadcast", action="restart").pack(),
        ),
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=AdminCallback(section="broadcast", action="cancel").pack(),
        ),
    )
    return builder.as_markup()


def build_admin_stats_period_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Сегодня",
            callback_data=AdminCallback(section="stats", action="period", param="today").pack(),
        ),
        InlineKeyboardButton(
            text="Неделя",
            callback_data=AdminCallback(section="stats", action="period", param="week").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Месяц",
            callback_data=AdminCallback(section="stats", action="period", param="month").pack(),
        ),
        InlineKeyboardButton(
            text="Всё время",
            callback_data=AdminCallback(section="stats", action="period", param="all").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="menu", action="home").pack()
        )
    )
    return builder.as_markup()


def build_admin_logs_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="ERROR",
            callback_data=AdminCallback(section="logs", action="level", param="ERROR").pack(),
        ),
        InlineKeyboardButton(
            text="WARNING",
            callback_data=AdminCallback(section="logs", action="level", param="WARNING").pack(),
        ),
        InlineKeyboardButton(
            text="INFO",
            callback_data=AdminCallback(section="logs", action="level", param="INFO").pack(),
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="menu", action="home").pack()
        )
    )
    return builder.as_markup()
