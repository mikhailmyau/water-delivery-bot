"""Раздел FAQ: вопросы раскрываются редактированием текущего сообщения."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.faq import FaqCallback
from app.callbacks.main_menu import MenuCallback
from app.database.models.user import User
from app.keyboards.user import build_faq_answer_keyboard, build_faq_list_keyboard
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.services.settings_service import SettingsService

router = Router(name="faq")


async def _build_faq_items(session: AsyncSession) -> list[tuple[int, str, str]]:
    settings_service = SettingsService(session)
    bot_settings = await settings_service.get()
    return [
        (1, "Сколько занимает доставка?", f"Обычная доставка — {bot_settings.delivery_days}. Срочная — {bot_settings.express_delivery_days}."),
        (2, "Какие способы оплаты?", "Оплата картой онлайн — сразу после оформления заказа, по защищённой ссылке."),
        (3, "Как изменить заказ?", "На карточке заказа до оплаты доступна кнопка «Изменить адрес». Для изменения объёма — оформите новый заказ."),
        (4, "Как отменить заказ?", "На карточке неоплаченного заказа есть кнопка «Отменить заказ»."),
        (5, "Что делать, если возникла проблема?", "Напишите нам в поддержку — мы отвечаем быстро и решаем любые вопросы."),
    ]


@router.callback_query(MenuCallback.filter(F.action == "faq"))
async def handle_open_faq(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    items = await _build_faq_items(session)
    analytics_service = AnalyticsService(session)
    await analytics_service.track(AnalyticsEvents.FAQ_OPENED, user_id=user.id)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(
            "❓ Часто задаваемые вопросы",
            reply_markup=build_faq_list_keyboard([(item_id, title) for item_id, title, _ in items]),
        )


@router.callback_query(FaqCallback.filter(F.action == "open"))
async def handle_open_question(
    callback: CallbackQuery, callback_data: FaqCallback, session: AsyncSession
) -> None:
    items = await _build_faq_items(session)
    match = next((item for item in items if item[0] == callback_data.question_id), None)
    await callback.answer()
    if callback.message is None or match is None:
        return
    _, title, answer = match
    await callback.message.edit_text(f"{title}\n\n{answer}", reply_markup=build_faq_answer_keyboard())


@router.callback_query(FaqCallback.filter(F.action == "back"))
async def handle_faq_back(callback: CallbackQuery, session: AsyncSession) -> None:
    items = await _build_faq_items(session)
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(
            "❓ Часто задаваемые вопросы",
            reply_markup=build_faq_list_keyboard([(item_id, title) for item_id, title, _ in items]),
        )
