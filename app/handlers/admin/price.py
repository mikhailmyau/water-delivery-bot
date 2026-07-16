"""Управление ценой воды (/price) — отдельная цена за литр для каждого из трёх видов."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.admin import AdminCallback
from app.content import WATER_TYPE_LABELS
from app.database.models.user import User
from app.database.models.water_type import WaterType
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
    prices = await PriceService(session).get_all_prices()
    lines = ["━━━━━━━━━━━━━━", "Текущие цены"]
    lines += [
        f"{WATER_TYPE_LABELS[wt]} — {format_price(price)} / литр" for wt, price in prices.items()
    ]
    lines.append("━━━━━━━━━━━━━━")
    return "\n".join(lines)


@router.message(Command("price"))
async def handle_price_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    prices = await PriceService(session).get_all_prices()
    await message.answer(
        await _render_price_menu(session), reply_markup=build_admin_price_menu_keyboard(prices)
    )


@router.callback_query(AdminCallback.filter((F.section == "price") & (F.action == "menu")))
async def handle_price_menu(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    prices = await PriceService(session).get_all_prices()
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            await _render_price_menu(session), reply_markup=build_admin_price_menu_keyboard(prices)
        )


@router.callback_query(AdminCallback.filter((F.section == "price") & (F.action == "edit")))
async def handle_price_edit_prompt(
    callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext
) -> None:
    water_type = WaterType(callback_data.param)
    await state.update_data(editing_water_type=water_type.value)
    await state.set_state(AdminPriceStates.waiting_price)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f"Введите новую цену за литр для {WATER_TYPE_LABELS[water_type]} (в рублях)."
        )


@router.message(AdminPriceStates.waiting_price)
async def handle_price_value(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    value, error = parse_positive_amount(message.text or "")
    if error is not None or value is None:
        await message.answer(error or "Введите корректное числовое значение.")
        return

    data = await state.get_data()
    water_type = WaterType(data["editing_water_type"])

    price_service = PriceService(session)
    old_price = await price_service.get_price_per_liter(water_type)
    new_price = rubles_to_kopecks(value)
    await price_service.set_price_per_liter(water_type, new_price)

    audit_repo = AdminAuditLogRepository(session)
    await audit_repo.add(
        user.telegram_id, f"price_changed_{water_type.value}", str(old_price), str(new_price)
    )

    await state.clear()
    prices = await price_service.get_all_prices()
    confirmation_text = (
        "━━━━━━━━━━━━━━\n"
        "Цена успешно обновлена.\n\n"
        f"{WATER_TYPE_LABELS[water_type]}: {format_price(new_price)}\n"
        "━━━━━━━━━━━━━━"
    )
    await message.answer(confirmation_text, reply_markup=build_admin_price_menu_keyboard(prices))
