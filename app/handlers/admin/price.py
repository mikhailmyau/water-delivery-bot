"""Управление ценой товара (/price)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.admin import AdminCallback
from app.database.models.user import User
from app.database.repositories.admin_audit_log_repository import AdminAuditLogRepository
from app.filters.is_admin import IsAdmin
from app.keyboards.admin import build_admin_price_menu_keyboard
from app.services.price_service import PriceService
from app.states.admin_states import AdminPriceStates
from app.utils.money import format_price, rubles_to_kopecks
from app.utils.validators import parse_positive_amount

router = Router(name="admin_price")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _render_price_menu(session: AsyncSession) -> str:
    price_service = PriceService(session)
    price_per_liter = await price_service.get_price_per_liter()
    return f"━━━━━━━━━━━━━━\nТекущая цена\n{format_price(price_per_liter)} / литр\n━━━━━━━━━━━━━━"


@router.message(Command("price"))
async def handle_price_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await message.answer(
        await _render_price_menu(session), reply_markup=build_admin_price_menu_keyboard()
    )


@router.callback_query(AdminCallback.filter((F.section == "price") & (F.action == "menu")))
async def handle_price_menu(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            await _render_price_menu(session), reply_markup=build_admin_price_menu_keyboard()
        )


@router.callback_query(AdminCallback.filter((F.section == "price") & (F.action == "edit")))
async def handle_price_edit_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminPriceStates.waiting_price)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("Введите новую цену за литр (в рублях).")


@router.message(AdminPriceStates.waiting_price)
async def handle_price_value(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    value, error = parse_positive_amount(message.text or "")
    if error is not None or value is None:
        await message.answer(error or "Введите корректное числовое значение.")
        return

    price_service = PriceService(session)
    old_price = await price_service.get_price_per_liter()
    new_price = rubles_to_kopecks(value)
    await price_service.set_price_per_liter(new_price)

    audit_repo = AdminAuditLogRepository(session)
    await audit_repo.add(user.telegram_id, "price_changed", str(old_price), str(new_price))

    await state.clear()
    confirmation_text = (
        "━━━━━━━━━━━━━━\n"
        "Цена успешно обновлена.\n\n"
        f"Новая стоимость: {format_price(new_price)}\n"
        "━━━━━━━━━━━━━━"
    )
    await message.answer(confirmation_text, reply_markup=build_admin_price_menu_keyboard())
