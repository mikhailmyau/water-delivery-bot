"""Управление заказами в административной панели."""

from __future__ import annotations

import csv
import io

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.admin import AdminCallback
from app.database.models.order import DeliveryStatus, Order
from app.database.models.user import User
from app.database.repositories.admin_audit_log_repository import AdminAuditLogRepository
from app.database.repositories.order_repository import OrderRepository
from app.filters.is_admin import IsAdmin
from app.keyboards.admin import (
    build_admin_order_detail_keyboard,
    build_admin_orders_list_keyboard,
    build_admin_orders_menu_keyboard,
)
from app.services.notification_service import NotificationService
from app.services.stats_service import StatsService
from app.states.admin_states import AdminOrderStates
from app.utils.money import format_price

router = Router(name="admin_orders")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _format_order_detail(order: Order) -> str:
    username = f"@{order.user.username}" if order.user and order.user.username else "—"
    lines = [
        "━━━━━━━━━━━━━━",
        f"Заказ #{order.order_number}",
        "━━━━━━━━━━━━━━",
        f"ID: {order.user.telegram_id if order.user else '—'}",
        f"Username: {username}",
        f"Город: {order.city}",
        f"Адрес: {order.street}, {order.house}",
        f"Объём: {order.volume} л",
        f"Стоимость: {format_price(order.price_per_liter * order.volume)}",
        f"Доставка: {format_price(order.delivery_price)}",
    ]
    if order.discount:
        lines.append(f"Скидка: {format_price(order.discount)}")
    lines += [
        f"Итог: {format_price(order.total_price)}",
        f"Статус оплаты: {order.payment_status.value}",
        f"Статус доставки: {order.delivery_status.value}",
        f"Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}",
        "━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)


async def _render_orders_menu(session: AsyncSession) -> str:
    stats = await StatsService(session).get_today_summary()
    return (
        "━━━━━━━━━━━━━━\n"
        "📦 Заказы\n"
        "Сегодня\n"
        "━━━━━━━━━━━━━━\n"
        f"Создано: {stats.orders_created}\n"
        f"Оплачено: {stats.orders_paid}\n"
        f"Ожидают оплаты: {stats.orders_unpaid}\n"
        f"Отменено: {stats.orders_cancelled}\n"
        f"Оборот: {format_price(stats.revenue)}\n"
        f"Средний чек: {format_price(stats.average_check)}\n"
        "━━━━━━━━━━━━━━"
    )


@router.message(Command("orders"))
async def handle_orders_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await message.answer(await _render_orders_menu(session), reply_markup=build_admin_orders_menu_keyboard())


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "menu")))
async def handle_orders_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(
            await _render_orders_menu(session), reply_markup=build_admin_orders_menu_keyboard()
        )


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "recent")))
async def handle_orders_recent(callback: CallbackQuery, session: AsyncSession) -> None:
    orders = await OrderRepository(session).list_recent()
    await callback.answer()
    if callback.message is None:
        return
    if not orders:
        await callback.message.edit_text("Заказов пока нет.", reply_markup=build_admin_orders_menu_keyboard())
        return
    await callback.message.edit_text("Последние заказы:", reply_markup=build_admin_orders_list_keyboard(orders))


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "filter_unpaid")))
async def handle_orders_unpaid(callback: CallbackQuery, session: AsyncSession) -> None:
    orders = await OrderRepository(session).list_unpaid()
    await callback.answer()
    if callback.message is None:
        return
    if not orders:
        await callback.message.edit_text(
            "Неоплаченных заказов нет.", reply_markup=build_admin_orders_menu_keyboard()
        )
        return
    await callback.message.edit_text(
        "Неоплаченные заказы:", reply_markup=build_admin_orders_list_keyboard(orders)
    )


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "open")))
async def handle_order_open(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession
) -> None:
    order = await OrderRepository(session).get_by_id(int(callback_data.param), with_relations=True)
    await callback.answer()
    if callback.message is None or order is None:
        return
    await callback.message.edit_text(
        _format_order_detail(order), reply_markup=build_admin_order_detail_keyboard(order)
    )


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "set_status")))
async def handle_order_set_status(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession, user: User
) -> None:
    order_id_str, status_value = callback_data.param.split(":")
    order_repo = OrderRepository(session)
    order = await order_repo.get_by_id(int(order_id_str), with_relations=True)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    old_status = order.delivery_status.value
    await order_repo.set_delivery_status(order, DeliveryStatus(status_value))
    await AdminAuditLogRepository(session).add(
        user.telegram_id, "order_status_changed", old_status, status_value
    )

    notification_service = NotificationService(callback.bot)
    await notification_service.send_to_user(
        order.user.telegram_id,
        f"Статус вашего заказа #{order.order_number} изменён: {status_value}.",
    )

    await callback.answer("Статус обновлён.")
    if callback.message is not None:
        await callback.message.edit_text(
            _format_order_detail(order), reply_markup=build_admin_order_detail_keyboard(order)
        )


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "message")))
async def handle_order_message_prompt(
    callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext
) -> None:
    await state.set_state(AdminOrderStates.waiting_client_message)
    await state.update_data(target_order_id=int(callback_data.param))
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Введите текст сообщения для клиента.")


@router.message(AdminOrderStates.waiting_client_message)
async def handle_order_message_send(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    order = await OrderRepository(session).get_by_id(data["target_order_id"], with_relations=True)
    await state.clear()
    if order is None or order.user is None:
        await message.answer("Заказ не найден.")
        return
    notification_service = NotificationService(message.bot)
    delivered = await notification_service.send_to_user(
        order.user.telegram_id, f"Сообщение от службы поддержки:\n\n{message.text}"
    )
    await message.answer(
        "Сообщение отправлено." if delivered else "Не удалось отправить: пользователь недоступен."
    )


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "delete")))
async def handle_order_delete(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession, user: User
) -> None:
    order_repo = OrderRepository(session)
    order = await order_repo.get_by_id(int(callback_data.param))
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return
    order_number = order.order_number
    await order_repo.delete(order)
    await AdminAuditLogRepository(session).add(user.telegram_id, "order_deleted", order_number, None)
    await callback.answer("Заказ удалён.")
    if callback.message is not None:
        await callback.message.edit_text(
            await _render_orders_menu(session), reply_markup=build_admin_orders_menu_keyboard()
        )


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "search")))
async def handle_order_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminOrderStates.waiting_search_number)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Введите номер заказа (например: 000123).")


@router.message(AdminOrderStates.waiting_search_number)
async def handle_order_search_input(message: Message, state: FSMContext, session: AsyncSession) -> None:
    order_number = (message.text or "").strip().lstrip("#")
    order = await OrderRepository(session).get_by_number(order_number.zfill(6))
    await state.clear()
    if order is None:
        await message.answer("Заказ с таким номером не найден.", reply_markup=build_admin_orders_menu_keyboard())
        return
    order = await OrderRepository(session).get_by_id(order.id, with_relations=True)
    await message.answer(
        _format_order_detail(order), reply_markup=build_admin_order_detail_keyboard(order)
    )


@router.callback_query(AdminCallback.filter((F.section == "orders") & (F.action == "export")))
async def handle_order_export(callback: CallbackQuery, session: AsyncSession) -> None:
    orders = await OrderRepository(session).list_recent(limit=500)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["order_number", "created_at", "city", "street", "house", "volume", "total_price_rub", "payment_status", "delivery_status"]
    )
    for order in orders:
        writer.writerow(
            [
                order.order_number,
                order.created_at.isoformat(),
                order.city,
                order.street,
                order.house,
                order.volume,
                f"{order.total_price / 100:.2f}",
                order.payment_status.value,
                order.delivery_status.value,
            ]
        )
    document = BufferedInputFile(buffer.getvalue().encode("utf-8-sig"), filename="orders.csv")
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer_document(document, caption=f"Экспорт заказов: {len(orders)} шт.")
