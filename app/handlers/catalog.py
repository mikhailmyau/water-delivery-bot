"""Каталог: выбор объёма и мгновенный пересчёт стоимости."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.catalog import CatalogCallback, VolumeCallback
from app.callbacks.main_menu import MenuCallback
from app.database.models.promo_code import PromoCode
from app.database.models.user import User
from app.database.repositories.promo_code_repository import PromoCodeRepository
from app.keyboards.user import build_catalog_keyboard
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.order_service import OrderService
from app.services.settings_service import SettingsService
from app.states.order_states import OrderStates
from app.utils.formatting import format_catalog_card, format_volume_calculation

router = Router(name="catalog")


@router.callback_query(MenuCallback.filter(F.action.in_(("catalog", "order"))))
async def handle_open_catalog(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    data = await state.get_data()
    settings_service = SettingsService(session)
    bot_settings = await settings_service.get()
    analytics_service = AnalyticsService(session)
    await analytics_service.track(AnalyticsEvents.CATALOG_OPENED, user_id=user.id)
    await callback.answer()
    if callback.message is None:
        return
    await callback.message.edit_text(
        format_catalog_card(bot_settings),
        reply_markup=build_catalog_keyboard(data.get("volume")),
    )


@router.callback_query(VolumeCallback.filter())
async def handle_volume_selected(
    callback: CallbackQuery,
    callback_data: VolumeCallback,
    state: FSMContext,
    session: AsyncSession,
    user: User,
) -> None:
    await state.update_data(volume=callback_data.liters)
    data = await state.get_data()

    order_service = OrderService(session)
    promo = await _get_promo_from_state(session, data)
    calculation = await order_service.calculate(callback_data.liters, promo)

    analytics_service = AnalyticsService(session)
    await analytics_service.track(
        AnalyticsEvents.VOLUME_SELECTED, user_id=user.id, metadata={"volume": callback_data.liters}
    )

    await callback.answer()
    if callback.message is None:
        return
    await callback.message.edit_text(
        format_volume_calculation(
            calculation.volume,
            calculation.price_per_liter,
            calculation.product_price,
            calculation.delivery_price,
            calculation.is_free_delivery,
            calculation.total_price,
        ),
        reply_markup=build_catalog_keyboard(callback_data.liters),
    )


@router.callback_query(CatalogCallback.filter(F.action == "continue"))
async def handle_continue_to_checkout(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User
) -> None:
    data = await state.get_data()
    if not data.get("volume"):
        await callback.answer("Сначала выберите объём.", show_alert=True)
        return

    analytics_service = AnalyticsService(session)
    await analytics_service.track(AnalyticsEvents.ORDER_STARTED, user_id=user.id)

    await state.set_state(OrderStates.waiting_city)
    await callback.answer()
    if callback.message is None:
        return
    await callback.message.edit_text("Введите город.")


async def _get_promo_from_state(session: AsyncSession, data: dict) -> PromoCode | None:
    promo_code_id = data.get("promo_code_id")
    if not promo_code_id:
        return None
    return await PromoCodeRepository(session).get_by_id(promo_code_id)
