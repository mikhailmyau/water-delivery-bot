"""Обработчик команды /start и возврата в главное меню."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.main_menu import MenuCallback
from app.database.models.user import User
from app.keyboards.user import build_main_menu_keyboard
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.settings_service import SettingsService

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(
    message: Message, state: FSMContext, session: AsyncSession, user: User
) -> None:
    await state.clear()
    settings_service = SettingsService(session)
    bot_settings = await settings_service.get()
    analytics_service = AnalyticsService(session)
    await analytics_service.track(AnalyticsEvents.BOT_STARTED, user_id=user.id)

    if bot_settings.banner_file_id:
        await message.answer_photo(
            bot_settings.banner_file_id,
            caption=bot_settings.welcome_text,
            reply_markup=build_main_menu_keyboard(),
        )
    else:
        await message.answer(bot_settings.welcome_text, reply_markup=build_main_menu_keyboard())


@router.callback_query(MenuCallback.filter(F.action == "home"))
async def handle_back_to_menu(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    settings_service = SettingsService(session)
    bot_settings = await settings_service.get()
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    try:
        await callback.message.edit_text(
            bot_settings.welcome_text, reply_markup=build_main_menu_keyboard()
        )
    except (
        Exception
    ):  # noqa: BLE001 — сообщение могло быть с фото, edit_text для такого не работает
        await callback.message.answer(
            bot_settings.welcome_text, reply_markup=build_main_menu_keyboard()
        )
