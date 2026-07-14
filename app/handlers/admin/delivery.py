"""Управление параметрами доставки (/delivery)."""

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
from app.keyboards.admin import build_admin_delivery_menu_keyboard
from app.services.delivery_service import DeliveryService
from app.services.settings_service import SettingsService
from app.states.admin_states import AdminDeliveryStates
from app.utils.money import format_price, rubles_to_kopecks
from app.utils.validators import parse_non_negative_int, parse_positive_amount

router = Router(name="admin_delivery")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _render_delivery_menu(session: AsyncSession) -> str:
    settings = await SettingsService(session).get()
    return (
        "━━━━━━━━━━━━━━\n"
        f"Стоимость доставки\n{format_price(settings.delivery_price)}\n\n"
        f"Бесплатная доставка\nот {settings.free_delivery_from_liters} л\n\n"
        f"Обычная доставка\n{settings.delivery_days}\n\n"
        f"Срочная\n{settings.express_delivery_days}\n"
        "━━━━━━━━━━━━━━"
    )


@router.message(Command("delivery"))
async def handle_delivery_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await message.answer(
        await _render_delivery_menu(session), reply_markup=build_admin_delivery_menu_keyboard()
    )


@router.callback_query(AdminCallback.filter((F.section == "delivery") & (F.action == "menu")))
async def handle_delivery_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(
            await _render_delivery_menu(session), reply_markup=build_admin_delivery_menu_keyboard()
        )


@router.callback_query(AdminCallback.filter((F.section == "delivery") & (F.action == "edit_price")))
async def handle_edit_delivery_price(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminDeliveryStates.waiting_delivery_price)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Введите новую стоимость доставки (в рублях).")


@router.callback_query(AdminCallback.filter((F.section == "delivery") & (F.action == "edit_free_from")))
async def handle_edit_free_from(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminDeliveryStates.waiting_free_delivery_from)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Введите объём (в литрах), от которого доставка бесплатна.")


@router.callback_query(AdminCallback.filter((F.section == "delivery") & (F.action == "edit_days")))
async def handle_edit_days(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminDeliveryStates.waiting_delivery_days)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Введите срок обычной доставки (например: до 5 дней).")


@router.message(AdminDeliveryStates.waiting_delivery_price)
async def handle_delivery_price_value(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    value, error = parse_positive_amount(message.text or "")
    if error:
        await message.answer(error)
        return
    new_price = rubles_to_kopecks(value)
    delivery_service = DeliveryService(session)
    await delivery_service.update_settings(delivery_price=new_price)
    await AdminAuditLogRepository(session).add(
        user.telegram_id, "delivery_price_changed", None, str(new_price)
    )
    await state.clear()
    await message.answer(
        f"Стоимость доставки обновлена: {format_price(new_price)}",
        reply_markup=build_admin_delivery_menu_keyboard(),
    )


@router.message(AdminDeliveryStates.waiting_free_delivery_from)
async def handle_free_from_value(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    value, error = parse_non_negative_int(message.text or "")
    if error:
        await message.answer(error)
        return
    delivery_service = DeliveryService(session)
    await delivery_service.update_settings(free_delivery_from_liters=value)
    await AdminAuditLogRepository(session).add(
        user.telegram_id, "free_delivery_from_changed", None, str(value)
    )
    await state.clear()
    await message.answer(
        f"Бесплатная доставка теперь действует от {value} л.",
        reply_markup=build_admin_delivery_menu_keyboard(),
    )


@router.message(AdminDeliveryStates.waiting_delivery_days)
async def handle_delivery_days_value(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Введите срок текстом, например: до 5 дней.")
        return
    await state.update_data(delivery_days=text)
    await state.set_state(AdminDeliveryStates.waiting_express_days)
    await message.answer("Введите срок срочной доставки (например: 1–3 дня).")


@router.message(AdminDeliveryStates.waiting_express_days)
async def handle_express_days_value(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Введите срок текстом, например: 1–3 дня.")
        return
    data = await state.get_data()
    delivery_service = DeliveryService(session)
    await delivery_service.update_settings(
        delivery_days=data.get("delivery_days"), express_delivery_days=text
    )
    await AdminAuditLogRepository(session).add(
        user.telegram_id, "delivery_days_changed", None, f"{data.get('delivery_days')} / {text}"
    )
    await state.clear()
    await message.answer("Сроки доставки обновлены.", reply_markup=build_admin_delivery_menu_keyboard())
