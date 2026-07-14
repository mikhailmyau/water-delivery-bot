"""Управление промокодами (/promo)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.admin import AdminCallback
from app.database.models.promo_code import DiscountType
from app.database.models.user import User
from app.database.repositories.admin_audit_log_repository import AdminAuditLogRepository
from app.database.repositories.promo_code_repository import PromoCodeRepository
from app.filters.is_admin import IsAdmin
from app.keyboards.admin import (
    build_admin_promo_detail_keyboard,
    build_admin_promo_discount_type_keyboard,
    build_admin_promo_list_keyboard,
    build_admin_promo_menu_keyboard,
)
from app.states.admin_states import AdminPromoStates
from app.utils.money import format_price, rubles_to_kopecks
from app.utils.validators import parse_non_negative_int

router = Router(name="admin_promo")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _format_promo_detail(promo) -> str:
    discount = (
        f"{promo.discount_value}%"
        if promo.discount_type == DiscountType.PERCENT
        else format_price(promo.discount_value)
    )
    expires = promo.expires_at.strftime("%d.%m.%Y") if promo.expires_at else "бессрочно"
    limit = promo.usage_limit if promo.usage_limit is not None else "без ограничений"
    status = "Активен" if promo.is_active else "Отключён"
    return (
        "━━━━━━━━━━━━━━\n"
        f"Промокод {promo.code}\n"
        "━━━━━━━━━━━━━━\n"
        f"Скидка: {discount}\n"
        f"Использован: {promo.used_count} раз\n"
        f"Лимит: {limit}\n"
        f"Действует до: {expires}\n"
        f"Статус: {status}\n"
        "━━━━━━━━━━━━━━"
    )


@router.message(Command("promo"))
async def handle_promo_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "━━━━━━━━━━━━━━\nПромокоды\n━━━━━━━━━━━━━━", reply_markup=build_admin_promo_menu_keyboard()
    )


@router.callback_query(AdminCallback.filter((F.section == "promo") & (F.action == "menu")))
async def handle_promo_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(
            "━━━━━━━━━━━━━━\nПромокоды\n━━━━━━━━━━━━━━", reply_markup=build_admin_promo_menu_keyboard()
        )


@router.callback_query(AdminCallback.filter((F.section == "promo") & (F.action == "create")))
async def handle_promo_create_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminPromoStates.waiting_code)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Введите название промокода (например: WATER10).")


@router.message(AdminPromoStates.waiting_code)
async def handle_promo_code_input(message: Message, state: FSMContext, session: AsyncSession) -> None:
    code = (message.text or "").strip().upper()
    if not code or len(code) > 32:
        await message.answer("Введите короткое название промокода (до 32 символов).")
        return
    existing = await PromoCodeRepository(session).get_by_code(code)
    if existing is not None:
        await message.answer("Такой промокод уже существует. Введите другое название.")
        return
    await state.update_data(code=code)
    await state.set_state(AdminPromoStates.waiting_discount_type)
    await message.answer("Выберите тип скидки.", reply_markup=build_admin_promo_discount_type_keyboard())


@router.callback_query(
    AdminPromoStates.waiting_discount_type,
    AdminCallback.filter((F.section == "promo") & (F.action.in_(("type_fixed", "type_percent")))),
)
async def handle_promo_discount_type(
    callback: CallbackQuery, callback_data: AdminCallback, state: FSMContext
) -> None:
    discount_type = DiscountType.FIXED if callback_data.action == "type_fixed" else DiscountType.PERCENT
    await state.update_data(discount_type=discount_type.value)
    await state.set_state(AdminPromoStates.waiting_discount_value)
    await callback.answer()
    prompt = (
        "Введите размер скидки в рублях."
        if discount_type == DiscountType.FIXED
        else "Введите размер скидки в процентах (1–100)."
    )
    if callback.message is not None:
        await callback.message.edit_text(prompt)


@router.message(AdminPromoStates.waiting_discount_value)
async def handle_promo_discount_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    value, error = parse_non_negative_int(message.text or "")
    if error or value == 0:
        await message.answer(error or "Скидка должна быть больше нуля.")
        return
    if data["discount_type"] == DiscountType.PERCENT.value and value > 100:
        await message.answer("Процент скидки не может быть больше 100.")
        return
    discount_value = value if data["discount_type"] == DiscountType.PERCENT.value else rubles_to_kopecks(value)
    await state.update_data(discount_value=discount_value)
    await state.set_state(AdminPromoStates.waiting_usage_limit)
    await message.answer("Сколько раз можно использовать промокод? Введите 0 — без ограничений.")


@router.message(AdminPromoStates.waiting_usage_limit)
async def handle_promo_usage_limit(message: Message, state: FSMContext) -> None:
    value, error = parse_non_negative_int(message.text or "")
    if error:
        await message.answer(error)
        return
    await state.update_data(usage_limit=value or None)
    await state.set_state(AdminPromoStates.waiting_expiry_days)
    await message.answer("На сколько дней действует промокод? Введите 0 — бессрочно.")


@router.message(AdminPromoStates.waiting_expiry_days)
async def handle_promo_expiry(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    value, error = parse_non_negative_int(message.text or "")
    if error:
        await message.answer(error)
        return
    data = await state.get_data()
    expires_at = datetime.now(timezone.utc) + timedelta(days=value) if value else None

    promo = await PromoCodeRepository(session).create(
        code=data["code"],
        discount_type=DiscountType(data["discount_type"]),
        discount_value=data["discount_value"],
        usage_limit=data.get("usage_limit"),
        expires_at=expires_at,
    )
    await AdminAuditLogRepository(session).add(
        user.telegram_id, "promo_created", None, promo.code
    )
    await state.clear()
    await message.answer(_format_promo_detail(promo), reply_markup=build_admin_promo_detail_keyboard(promo))


@router.callback_query(AdminCallback.filter((F.section == "promo") & (F.action == "list")))
async def handle_promo_list(callback: CallbackQuery, session: AsyncSession) -> None:
    promos = await PromoCodeRepository(session).list_all()
    await callback.answer()
    if callback.message is None:
        return
    if not promos:
        await callback.message.edit_text(
            "Промокодов пока нет.", reply_markup=build_admin_promo_menu_keyboard()
        )
        return
    await callback.message.edit_text(
        "Выберите промокод:", reply_markup=build_admin_promo_list_keyboard(promos)
    )


@router.callback_query(AdminCallback.filter((F.section == "promo") & (F.action == "open")))
async def handle_promo_open(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession
) -> None:
    promo = await PromoCodeRepository(session).get_by_id(int(callback_data.param))
    await callback.answer()
    if callback.message is None or promo is None:
        return
    await callback.message.edit_text(_format_promo_detail(promo), reply_markup=build_admin_promo_detail_keyboard(promo))


@router.callback_query(AdminCallback.filter((F.section == "promo") & (F.action == "toggle")))
async def handle_promo_toggle(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession, user: User
) -> None:
    repo = PromoCodeRepository(session)
    promo = await repo.get_by_id(int(callback_data.param))
    if promo is None:
        await callback.answer("Промокод не найден.", show_alert=True)
        return
    await repo.set_active(promo, not promo.is_active)
    await AdminAuditLogRepository(session).add(
        user.telegram_id, "promo_toggled", str(not promo.is_active), str(promo.is_active)
    )
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(_format_promo_detail(promo), reply_markup=build_admin_promo_detail_keyboard(promo))


@router.callback_query(AdminCallback.filter((F.section == "promo") & (F.action == "delete")))
async def handle_promo_delete(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession, user: User
) -> None:
    repo = PromoCodeRepository(session)
    promo = await repo.get_by_id(int(callback_data.param))
    if promo is None:
        await callback.answer("Промокод не найден.", show_alert=True)
        return
    code = promo.code
    await repo.delete(promo)
    await AdminAuditLogRepository(session).add(user.telegram_id, "promo_deleted", code, None)
    await callback.answer("Промокод удалён.")
    promos = await repo.list_all()
    if callback.message is None:
        return
    if not promos:
        await callback.message.edit_text("Промокодов пока нет.", reply_markup=build_admin_promo_menu_keyboard())
        return
    await callback.message.edit_text("Выберите промокод:", reply_markup=build_admin_promo_list_keyboard(promos))
