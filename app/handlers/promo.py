"""Ввод и проверка промокода."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.main_menu import MenuCallback
from app.callbacks.order import PromoCallback
from app.database.models.promo_code import DiscountType
from app.database.models.user import User
from app.keyboards.user import build_main_menu_keyboard, build_promo_prompt_keyboard
from app.middlewares.throttling import RateLimiter
from app.services.promo_service import PromoService
from app.states.promo_states import PromoStates
from app.utils.constants import PROMO_CHECK_LIMIT, PROMO_CHECK_WINDOW_SECONDS

router = Router(name="promo")

_promo_rate_limiter = RateLimiter()


@router.callback_query(MenuCallback.filter(F.action == "promo"))
async def handle_open_promo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PromoStates.waiting_code)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "Введите промокод.", reply_markup=build_promo_prompt_keyboard()
        )


@router.callback_query(PromoCallback.filter(F.action == "skip"))
async def handle_skip_promo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("Главное меню:", reply_markup=build_main_menu_keyboard())


@router.message(PromoStates.waiting_code)
async def handle_promo_input(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    if not _promo_rate_limiter.allow(
        f"promo:{user.telegram_id}", PROMO_CHECK_LIMIT, PROMO_CHECK_WINDOW_SECONDS
    ):
        await message.answer("Слишком много попыток. Попробуйте немного позже.")
        return

    promo_service = PromoService(session)
    code = (message.text or "").strip()
    result = await promo_service.validate(code)

    if not result.is_valid:
        await message.answer(f"━━━━━━━━━━━━━━\n{result.error_message}\n━━━━━━━━━━━━━━")
        return

    promo = result.promo
    assert (
        promo is not None
    )  # noqa: S101 — гарантировано инвариантом PromoValidationResult.is_valid
    await state.update_data(promo_code_id=promo.id)
    await state.set_state(None)

    discount_text = (
        f"{promo.discount_value}%"
        if promo.discount_type == DiscountType.PERCENT
        else f"{promo.discount_value / 100:.0f} ₽"
    )
    await message.answer(
        "━━━━━━━━━━━━━━\n"
        "Промокод применён.\n\n"
        f"Скидка: {discount_text}\n"
        "Скидка будет учтена при оформлении заказа.\n"
        "━━━━━━━━━━━━━━",
        reply_markup=build_main_menu_keyboard(),
    )
