"""Административные inline-клавиатуры."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks.admin import AdminCallback
from app.content import WATER_TYPE_LABELS, WATER_TYPE_ORDER
from app.database.models.order import DeliveryStatus, Order
from app.database.models.water_type import WaterType
from app.utils.money import format_price


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


def build_admin_price_menu_keyboard(prices: dict[WaterType, int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for water_type in WATER_TYPE_ORDER:
        label = WATER_TYPE_LABELS[water_type]
        builder.row(
            InlineKeyboardButton(
                text=f"✏️ {label} — {format_price(prices[water_type])}/л",
                callback_data=AdminCallback(
                    section="price", action="edit", param=water_type.value
                ).pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=AdminCallback(section="menu", action="home").pack()
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
