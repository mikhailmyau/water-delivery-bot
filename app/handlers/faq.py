"""Раздел FAQ: вопросы раскрываются редактированием текущего сообщения."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.faq import FaqCallback
from app.callbacks.main_menu import MenuCallback
from app.content import (
    REVIEWS_GROUP_URL,
    SUPPLY_CHANNEL_URL,
    WATER_TYPE_DESCRIPTIONS,
    WATER_TYPE_LABELS,
)
from app.database.models.user import User
from app.database.models.water_type import WaterType
from app.keyboards.user import build_faq_answer_keyboard, build_faq_list_keyboard
from app.services.analytics_service import AnalyticsEvents, AnalyticsService
from app.utils.constants import MAX_BOTTLES, MAX_VOLUME_LITERS, MIN_BOTTLES, MIN_VOLUME_LITERS

router = Router(name="faq")

_FAQ_ITEMS: list[tuple[int, str, str]] = [
    (
        1,
        "Сколько занимает доставка?",
        "От 1 часа до 5 дней в зависимости от вашего города — точный срок вы "
        "увидите при оформлении заказа, сразу после выбора города.",
    ),
    (
        2,
        "Сколько стоит доставка?",
        "Доставка курьером/такси до двери уже включена в цену воды — "
        "доплачивать за неё не нужно.",
    ),
    (
        3,
        "Какой минимальный и максимальный заказ?",
        f"От {MIN_BOTTLES} бутылей ({MIN_VOLUME_LITERS} л) до {MAX_BOTTLES} "
        f"бутылей ({MAX_VOLUME_LITERS} л) за один заказ.",
    ),
    (
        4,
        "Какие виды воды у вас есть?",
        "\n".join(
            f"{WATER_TYPE_LABELS[wt]} — {WATER_TYPE_DESCRIPTIONS[wt]}"
            for wt in (WaterType.SLM, WaterType.SRM, WaterType.GAZ)
        ),
    ),
    (
        5,
        "Какие способы оплаты?",
        "Оплата картой онлайн — сразу после оформления заказа, по защищённой ссылке.",
    ),
    (
        6,
        "Как изменить заказ?",
        "На карточке заказа до оплаты доступна кнопка «Изменить адрес». "
        "Для изменения вида воды или объёма — оформите новый заказ.",
    ),
    (
        7,
        "Как отменить заказ?",
        "На карточке неоплаченного заказа есть кнопка «Отменить заказ».",
    ),
    (
        8,
        "Есть ли отзывы и информация о поставках?",
        f"Да — канал с поставками: {SUPPLY_CHANNEL_URL}\nОтзывы клиентов: {REVIEWS_GROUP_URL}",
    ),
    (
        9,
        "Что делать, если возникла проблема?",
        "Напишите нам в поддержку — мы отвечаем быстро и решаем любые вопросы.",
    ),
]


@router.callback_query(MenuCallback.filter(F.action == "faq"))
async def handle_open_faq(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    analytics_service = AnalyticsService(session)
    await analytics_service.track(AnalyticsEvents.FAQ_OPENED, user_id=user.id)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "❓ Часто задаваемые вопросы",
            reply_markup=build_faq_list_keyboard(
                [(item_id, title) for item_id, title, _ in _FAQ_ITEMS]
            ),
        )


@router.callback_query(FaqCallback.filter(F.action == "open"))
async def handle_open_question(callback: CallbackQuery, callback_data: FaqCallback) -> None:
    match = next((item for item in _FAQ_ITEMS if item[0] == callback_data.question_id), None)
    await callback.answer()
    if not isinstance(callback.message, Message) or match is None:
        return
    _, title, answer = match
    await callback.message.edit_text(
        f"{title}\n\n{answer}", reply_markup=build_faq_answer_keyboard()
    )


@router.callback_query(FaqCallback.filter(F.action == "back"))
async def handle_faq_back(callback: CallbackQuery) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "❓ Часто задаваемые вопросы",
            reply_markup=build_faq_list_keyboard(
                [(item_id, title) for item_id, title, _ in _FAQ_ITEMS]
            ),
        )
