"""Пошаговое оформление заказа: город → улица → дом → подтверждение → оплата.

Город выбирается кнопками (алфавитный указатель по app/data/cities.py), а не
вводится текстом — это и удобнее для покупателя, и сразу даёт боту оценку
срока доставки. Свободный текстовый ввод остаётся только как запасной вариант
для города, которого нет в справочнике (см. handle_city_manual_*).
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.catalog import CatalogCallback
from app.callbacks.city import CityCallback
from app.callbacks.main_menu import MenuCallback
from app.callbacks.order import OrderCallback
from app.data.cities import (
    FALLBACK_TIER_DAYS,
    available_letters,
    cities_by_letter,
    estimate_label,
    get_city_by_id,
)
from app.database.models.user import User
from app.database.models.water_type import WaterType
from app.database.repositories.order_repository import OrderRepository
from app.keyboards.user import (
    build_city_letters_keyboard,
    build_city_list_keyboard,
    build_main_menu_keyboard,
    build_order_preview_keyboard,
)
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.states.order_states import OrderStates
from app.utils.formatting import (
    format_admin_new_order_card,
    format_delivery_info,
    format_order_card,
)
from app.utils.validators import validate_address, validate_city, validate_house

router = Router(name="order")

_STREET_PROMPT = "🏠 <i>Введите улицу (без номера дома).</i>"
_HOUSE_PROMPT = "🏠 <i>Введите номер дома.</i>"


@router.callback_query(CatalogCallback.filter(F.action == "continue"))
async def handle_continue_to_checkout(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("bottles"):
        await callback.answer("Сначала выберите объём.", show_alert=True)
        return

    await state.set_state(OrderStates.waiting_city)
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        "🏙 Выберите город доставки (по первой букве):",
        reply_markup=build_city_letters_keyboard(available_letters()),
    )


@router.callback_query(OrderStates.waiting_city, CityCallback.filter(F.action == "letter"))
async def handle_city_letter(callback: CallbackQuery, callback_data: CityCallback) -> None:
    cities = cities_by_letter(callback_data.value)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f"Города на «{callback_data.value.upper()}»:",
            reply_markup=build_city_list_keyboard(cities),
        )


@router.callback_query(OrderStates.waiting_city, CityCallback.filter(F.action == "letters"))
async def handle_city_back_to_letters(callback: CallbackQuery) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "🏙 Выберите город доставки (по первой букве):",
            reply_markup=build_city_letters_keyboard(available_letters()),
        )


@router.callback_query(OrderStates.waiting_city, CityCallback.filter(F.action == "manual"))
async def handle_city_manual_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(manual_city_mode=True)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("Введите название вашего города текстом.")


@router.callback_query(OrderStates.waiting_city, CityCallback.filter(F.action == "pick"))
async def handle_city_picked(
    callback: CallbackQuery, callback_data: CityCallback, state: FSMContext
) -> None:
    city = get_city_by_id(int(callback_data.value))
    if city is None:
        await callback.answer("Город не найден, попробуйте ещё раз.", show_alert=True)
        return
    await state.update_data(
        city=city.name,
        delivery_days_estimate=estimate_label(city.tier_days),
        city_matched=True,
        manual_city_mode=False,
    )
    await state.set_state(OrderStates.waiting_address)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(_STREET_PROMPT)


@router.message(OrderStates.waiting_city)
async def handle_city_manual_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("manual_city_mode"):
        await message.answer(
            "Пожалуйста, выберите город кнопкой выше — или нажмите «Не нашёл свой город»."
        )
        return
    result = validate_city(message.text or "")
    if not result.is_valid:
        await message.answer(result.error_message)
        return
    await state.update_data(
        city=(message.text or "").strip(),
        delivery_days_estimate=estimate_label(FALLBACK_TIER_DAYS),
        city_matched=False,
        manual_city_mode=False,
    )
    await state.set_state(OrderStates.waiting_address)
    await message.answer(_STREET_PROMPT)


@router.message(OrderStates.waiting_address)
async def handle_address_input(message: Message, state: FSMContext) -> None:
    result = validate_address(message.text or "")
    if not result.is_valid:
        await message.answer(result.error_message)
        return
    await state.update_data(street=(message.text or "").strip())
    await state.set_state(OrderStates.waiting_house)
    await message.answer(_HOUSE_PROMPT)


@router.message(OrderStates.waiting_house)
async def handle_house_input(
    message: Message, state: FSMContext, session: AsyncSession, user: User, bot: Bot
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
        await order_repo.update_address(
            order,
            data["city"],
            data["street"],
            house,
            data["delivery_days_estimate"],
            data["city_matched"],
        )
    else:
        order = await order_service.create_order(
            user,
            data["city"],
            data["street"],
            house,
            WaterType(data["water_type"]),
            data["bottles"],
            data["delivery_days_estimate"],
            data["city_matched"],
        )
        order.user = user
        notification_service = NotificationService(bot)
        await notification_service.send_to_admin_group(format_admin_new_order_card(order))

    await state.update_data(order_id=order.id, editing_order_id=None)
    await state.set_state(OrderStates.waiting_confirmation)
    await message.answer(
        format_order_card(order), reply_markup=build_order_preview_keyboard(order.id)
    )


@router.callback_query(OrderCallback.filter(F.action == "edit_address"))
async def handle_edit_address(
    callback: CallbackQuery, callback_data: OrderCallback, state: FSMContext
) -> None:
    await state.update_data(editing_order_id=callback_data.order_id)
    await state.set_state(OrderStates.waiting_city)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "🏙 Выберите новый город доставки:",
            reply_markup=build_city_letters_keyboard(available_letters()),
        )


@router.callback_query(OrderCallback.filter(F.action == "back"))
async def handle_order_back(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("Главное меню:", reply_markup=build_main_menu_keyboard())


@router.callback_query(MenuCallback.filter(F.action == "delivery"))
async def handle_delivery_info(callback: CallbackQuery) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            format_delivery_info(), reply_markup=build_main_menu_keyboard()
        )
