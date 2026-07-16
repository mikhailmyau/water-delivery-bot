"""Оплата заказа: создание платежа, проверка статуса, отмена."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.order import OrderCallback
from app.database.models.order import PaymentStatus
from app.database.repositories.order_repository import OrderRepository
from app.keyboards.user import build_main_menu_keyboard, build_payment_keyboard
from app.payments.factory import get_payment_provider
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.utils.formatting import format_order_card, format_payment_success

logger = logging.getLogger("app.handlers.payment")

router = Router(name="payment")


@router.callback_query(OrderCallback.filter(F.action == "pay"))
async def handle_pay(
    callback: CallbackQuery, callback_data: OrderCallback, session: AsyncSession, bot: Bot
) -> None:
    order_repo = OrderRepository(session)
    order = await order_repo.get_by_id(callback_data.order_id, with_relations=True)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    if order.payment_status == PaymentStatus.SUCCESS:
        await callback.answer("Заказ уже оплачен.", show_alert=True)
        return

    payment_service = PaymentService(session, get_payment_provider(), bot)
    payment = await payment_service.create_payment_for_order(order)

    await callback.answer()
    if isinstance(callback.message, Message) and payment.payment_url is not None:
        await callback.message.edit_text(
            format_order_card(order),
            reply_markup=build_payment_keyboard(order.id, payment.payment_url),
        )


@router.callback_query(OrderCallback.filter(F.action == "check_payment"))
async def handle_check_payment(
    callback: CallbackQuery, callback_data: OrderCallback, session: AsyncSession
) -> None:
    order_repo = OrderRepository(session)
    order = await order_repo.get_by_id(callback_data.order_id, with_relations=True)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    if order.payment_status != PaymentStatus.SUCCESS:
        await callback.answer(
            "Оплата пока не подтверждена. Обычно это занимает не больше минуты.",
            show_alert=True,
        )
        return

    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            format_payment_success(order), reply_markup=build_main_menu_keyboard()
        )


@router.callback_query(OrderCallback.filter(F.action == "cancel"))
async def handle_cancel_order(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    order_repo = OrderRepository(session)
    order = await order_repo.get_by_id(callback_data.order_id)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await OrderService(session).cancel_order(order)
    await state.clear()
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "Заказ отменён. Если передумаете — мы всегда на связи.",
            reply_markup=build_main_menu_keyboard(),
        )
