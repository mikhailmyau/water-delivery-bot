"""Пошаговое оформление заказа и карточка заказа."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.main_menu import MenuCallback
from app.callbacks.order import OrderCallback
from app.database.models.promo_code import PromoCode
from app.database.models.user import User
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.promo_code_repository import PromoCodeRepository
from app.keyboards.user import build_main_menu_keyboard, build_order_preview_keyboard
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.settings_service import SettingsService
from app.states.order_states import OrderStates
from app.utils.formatting import format_admin_new_order_card, format_order_card
from app.utils.money import format_price
from app.utils.validators import validate_address, validate_city, validate_house

router = Router(name="order")


@router.message(OrderStates.waiting_city)
async def handle_city_input(message: Message, state: FSMContext) -> None:
    result = validate_city(message.text or "")
    if not result.is_valid:
        await message.answer(result.error_message)
        return
    await state.update_data(city=(message.text or "").strip())
    await state.set_state(OrderStates.waiting_address)
    await message.answer("Введите улицу.")


@router.message(OrderStates.waiting_address)
async def handle_address_input(message: Message, state: FSMContext) -> None:
    result = validate_address(message.text or "")
    if not result.is_valid:
        await message.answer(result.error_message)
        return
    await state.update_data(street=(message.text or "").strip())
    await state.set_state(OrderStates.waiting_house)
    await message.answer("Введите номер дома.")


@router.message(OrderStates.waiting_house)
async def handle_house_input(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    result = validate_house(message.text or "")
    if not result.is_valid:
        await message.answer(result.error_message)
        return
    house = (message.text or "").strip()
    data = await state.get_data()

    order_service = OrderService(session)
    order_repo = OrderRepository(session)
    editing_order_id = data.get("editing_order_id")

    if editing_order_id:
        order = await order_repo.get_by_id(editing_order_id, with_relations=True)
        if order is None:
            await message.answer("Заказ не найден. Начните оформление заново.")
            await state.clear()
            await message.answer("Главное меню:", reply_markup=build_main_menu_keyboard())
            return
        await order_repo.update_address(order, data["city"], data["street"], house)
    else:
        promo = await _get_promo_from_state(session, data)
        order = await order_service.create_order(
            user, data["city"], data["street"], house, data["volume"], promo
        )
        order.user = user
        notification_service = NotificationService(message.bot)
        await notification_service.send_to_admin_group(format_admin_new_order_card(order))

    await state.update_data(order_id=order.id, editing_order_id=None)
    await state.set_state(OrderStates.waiting_confirmation)
    await message.answer(format_order_card(order), reply_markup=build_order_preview_keyboard(order.id))


@router.callback_query(OrderCallback.filter(F.action == "edit_address"))
async def handle_edit_address(
    callback: CallbackQuery, callback_data: OrderCallback, state: FSMContext
) -> None:
    await state.update_data(editing_order_id=callback_data.order_id)
    await state.set_state(OrderStates.waiting_city)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Введите город.")


@router.callback_query(OrderCallback.filter(F.action == "back"))
async def handle_order_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Главное меню:", reply_markup=build_main_menu_keyboard())


@router.callback_query(MenuCallback.filter(F.action == "delivery"))
async def handle_delivery_info(callback: CallbackQuery, session: AsyncSession) -> None:
    settings_service = SettingsService(session)
    bot_settings = await settings_service.get()
    text = (
        "━━━━━━━━━━━━━━\n"
        "🚚 Доставка\n"
        "━━━━━━━━━━━━━━\n"
        f"Стоимость: {format_price(bot_settings.delivery_price)}\n"
        f"Бесплатная доставка: от {bot_settings.free_delivery_from_liters} л\n"
        f"Обычная доставка: {bot_settings.delivery_days}\n"
        f"Срочная доставка: {bot_settings.express_delivery_days}\n"
        "━━━━━━━━━━━━━━"
    )
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=build_main_menu_keyboard())


async def _get_promo_from_state(session: AsyncSession, data: dict) -> PromoCode | None:
    promo_code_id = data.get("promo_code_id")
    if not promo_code_id:
        return None
    return await PromoCodeRepository(session).get_by_id(promo_code_id)
