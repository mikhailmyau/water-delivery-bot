"""Раздел поддержки."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.main_menu import MenuCallback
from app.database.models.user import User
from app.keyboards.user import build_support_keyboard
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.settings_service import SettingsService

router = Router(name="support")


@router.callback_query(MenuCallback.filter(F.action == "support"))
async def handle_open_support(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    settings_service = SettingsService(session)
    bot_settings = await settings_service.get()
    analytics_service = AnalyticsService(session)
    await analytics_service.track(AnalyticsEvents.SUPPORT_OPENED, user_id=user.id)

    text = "━━━━━━━━━━━━━━\nНужна помощь?\nНаш оператор поможет.\n━━━━━━━━━━━━━━"
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(text, reply_markup=build_support_keyboard(bot_settings.support_link))
