"""Главное меню администратора (/admin)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.callbacks.admin import AdminCallback
from app.filters.is_admin import IsAdmin
from app.keyboards.admin import build_admin_main_menu_keyboard

router = Router(name="admin_menu")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

_MENU_TEXT = "━━━━━━━━━━━━━━━━━━━━━━\n⚙ Панель управления\n━━━━━━━━━━━━━━━━━━━━━━"


@router.message(Command("admin"))
async def handle_admin_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_MENU_TEXT, reply_markup=build_admin_main_menu_keyboard())


@router.callback_query(AdminCallback.filter(F.section == "menu"))
async def handle_admin_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(_MENU_TEXT, reply_markup=build_admin_main_menu_keyboard())
