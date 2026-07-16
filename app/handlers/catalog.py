"""Первый шаг заказа: вид воды и объём с мгновенным пересчётом цены.

Объём выбирается готовой кнопкой (40/60/.../200 л), не вводится и не
считается +/- — так короче и привычнее для покупателя (аналог выбора
размера в интернет-магазине).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.catalog import CatalogCallback, VolumeCallback, WaterTypeCallback
from app.callbacks.main_menu import MenuCallback
from app.database.models.user import User
from app.database.models.water_type import WaterType
from app.keyboards.user import build_volume_keyboard, build_water_type_keyboard
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.order_service import OrderService
from app.services.price_service import PriceService
from app.utils.constants import BOTTLE_VOLUME_LITERS
from app.utils.formatting import (
    format_volume_calculation,
    format_water_type_prompt,
    format_water_type_selected_prompt,
)

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
    await state.update_data(water_type=water_type.value)
    price_per_liter = await PriceService(session).get_price_per_liter(water_type)

    analytics_service = AnalyticsService(session)
    await analytics_service.track(
        AnalyticsEvents.VOLUME_SELECTED, user_id=user.id, metadata={"water_type": water_type.value}
    )

    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        format_water_type_selected_prompt(water_type, price_per_liter),
        reply_markup=build_volume_keyboard(),
    )


@router.callback_query(VolumeCallback.filter())
async def handle_volume_selected(
    callback: CallbackQuery,
    callback_data: VolumeCallback,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    water_type_value = data.get("water_type")
    if water_type_value is None:
        await callback.answer("Сначала выберите вид воды.", show_alert=True)
        return
    water_type = WaterType(water_type_value)
    bottles = callback_data.liters // BOTTLE_VOLUME_LITERS
    await state.update_data(bottles=bottles)

    calculation = await OrderService(session).calculate(water_type, bottles)

    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        format_volume_calculation(
            water_type, calculation.volume, calculation.price_per_liter, calculation.total_price
        ),
        reply_markup=build_volume_keyboard(callback_data.liters),
    )


@router.callback_query(CatalogCallback.filter(F.action == "back"))
async def handle_back_to_type(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    prices = await PriceService(session).get_all_prices()
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    await callback.message.edit_text(
        format_water_type_prompt(prices), reply_markup=build_water_type_keyboard(prices)
    )
