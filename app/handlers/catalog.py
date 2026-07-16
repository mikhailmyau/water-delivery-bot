"""Первый шаг заказа: вид воды и количество бутылей с мгновенным пересчётом цены.

Пользователь никогда не вводит объём вручную — только жмёт ➖/➕, счётчик
всегда в диапазоне [MIN_BOTTLES, MAX_BOTTLES] (см. app/utils/constants.py).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.catalog import BottleCallback, WaterTypeCallback
from app.callbacks.main_menu import MenuCallback
from app.database.models.user import User
from app.database.models.water_type import WaterType
from app.keyboards.user import build_bottle_stepper_keyboard, build_water_type_keyboard
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.order_service import OrderService
from app.services.price_service import PriceService
from app.utils.constants import MAX_BOTTLES, MIN_BOTTLES
from app.utils.formatting import format_bottle_calculation, format_water_type_prompt

router = Router(name="catalog")


@router.callback_query(MenuCallback.filter(F.action == "order"))
async def handle_open_order(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    await state.clear()
    prices = await PriceService(session).get_all_prices()
    analytics_service = AnalyticsService(session)
    await analytics_service.track(AnalyticsEvents.CATALOG_OPENED, user_id=user.id)
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        format_water_type_prompt(prices), reply_markup=build_water_type_keyboard(prices)
    )


@router.callback_query(WaterTypeCallback.filter())
async def handle_water_type_selected(
    callback: CallbackQuery,
    callback_data: WaterTypeCallback,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    water_type = WaterType(callback_data.code)
    await state.update_data(water_type=water_type.value, bottles=MIN_BOTTLES)

    calculation = await OrderService(session).calculate(water_type, MIN_BOTTLES)
    analytics_service = AnalyticsService(session)
    await analytics_service.track(
        AnalyticsEvents.VOLUME_SELECTED, user_id=user.id, metadata={"water_type": water_type.value}
    )

    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        format_bottle_calculation(
            water_type, MIN_BOTTLES, calculation.price_per_liter, calculation.total_price
        ),
        reply_markup=build_bottle_stepper_keyboard(),
    )


@router.callback_query(BottleCallback.filter(F.action.in_(("inc", "dec"))))
async def handle_bottle_step(
    callback: CallbackQuery, callback_data: BottleCallback, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    water_type_value = data.get("water_type")
    if water_type_value is None:
        await callback.answer("Сначала выберите вид воды.", show_alert=True)
        return
    water_type = WaterType(water_type_value)
    bottles = data.get("bottles", MIN_BOTTLES)

    if callback_data.action == "inc":
        if bottles >= MAX_BOTTLES:
            await callback.answer(f"Максимум — {MAX_BOTTLES} бутылей за заказ.", show_alert=True)
            return
        bottles += 1
    else:
        if bottles <= MIN_BOTTLES:
            await callback.answer(f"Минимальный заказ — {MIN_BOTTLES} бутыли.", show_alert=True)
            return
        bottles -= 1

    await state.update_data(bottles=bottles)
    calculation = await OrderService(session).calculate(water_type, bottles)

    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        format_bottle_calculation(
            water_type, bottles, calculation.price_per_liter, calculation.total_price
        ),
        reply_markup=build_bottle_stepper_keyboard(),
    )


@router.callback_query(BottleCallback.filter(F.action == "back"))
async def handle_bottle_back_to_type(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    prices = await PriceService(session).get_all_prices()
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        format_water_type_prompt(prices), reply_markup=build_water_type_keyboard(prices)
    )
