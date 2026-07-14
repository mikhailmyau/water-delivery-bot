"""Пользовательские inline-клавиатуры."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks.catalog import CatalogCallback, VolumeCallback
from app.callbacks.faq import FaqCallback
from app.callbacks.main_menu import MenuCallback
from app.callbacks.order import OrderCallback, PromoCallback
from app.utils.constants import AVAILABLE_VOLUMES_LITERS


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 Заказать воду", callback_data=MenuCallback(action="order").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💧 Каталог", callback_data=MenuCallback(action="catalog").pack()
        ),
        InlineKeyboardButton(
            text="🚚 Доставка", callback_data=MenuCallback(action="delivery").pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Промокод", callback_data=MenuCallback(action="promo").pack()),
        InlineKeyboardButton(text="❓ FAQ", callback_data=MenuCallback(action="faq").pack()),
    )
    builder.row(
        InlineKeyboardButton(
            text="📞 Поддержка", callback_data=MenuCallback(action="support").pack()
        )
    )
    return builder.as_markup()


def build_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅ Главное меню", callback_data=MenuCallback(action="home").pack()
        )
    )
    return builder.as_markup()


def build_catalog_keyboard(selected_volume: int | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    volume_buttons = [
        InlineKeyboardButton(
            text=f"• {volume} л •" if volume == selected_volume else f"{volume} л",
            callback_data=VolumeCallback(liters=volume).pack(),
        )
        for volume in AVAILABLE_VOLUMES_LITERS
    ]
    builder.row(*volume_buttons, width=5)
    if selected_volume is not None:
        builder.row(
            InlineKeyboardButton(
                text="Продолжить оформление",
                callback_data=CatalogCallback(action="continue").pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Главное меню", callback_data=MenuCallback(action="home").pack()
        )
    )
    return builder.as_markup()


def build_order_preview_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💳 Оплатить", callback_data=OrderCallback(action="pay", order_id=order_id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить адрес",
            callback_data=OrderCallback(action="edit_address", order_id=order_id).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Назад", callback_data=OrderCallback(action="back", order_id=order_id).pack()
        )
    )
    return builder.as_markup()


def build_payment_keyboard(order_id: int, payment_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url))
    builder.row(
        InlineKeyboardButton(
            text="🔄 Я оплатил(а)",
            callback_data=OrderCallback(action="check_payment", order_id=order_id).pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Отменить заказ",
            callback_data=OrderCallback(action="cancel", order_id=order_id).pack(),
        )
    )
    return builder.as_markup()


def build_reminder_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура напоминания о неоплаченном заказе.

    Использует callback, а не готовую ссылку — платёж создаётся в момент
    нажатия «Оплатить», поэтому напоминание не зависит от того, создавался
    ли платёж раньше и не истекла ли прежняя ссылка.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Оплатить", callback_data=OrderCallback(action="pay", order_id=order_id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Отменить заказ",
            callback_data=OrderCallback(action="cancel", order_id=order_id).pack(),
        )
    )
    return builder.as_markup()


def build_promo_prompt_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Пропустить", callback_data=PromoCallback(action="skip").pack())
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Главное меню", callback_data=MenuCallback(action="home").pack()
        )
    )
    return builder.as_markup()


def build_faq_list_keyboard(questions: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for question_id, title in questions:
        builder.row(
            InlineKeyboardButton(
                text=title, callback_data=FaqCallback(action="open", question_id=question_id).pack()
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Главное меню", callback_data=MenuCallback(action="home").pack()
        )
    )
    return builder.as_markup()


def build_faq_answer_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅ Ко всем вопросам", callback_data=FaqCallback(action="back").pack()
        )
    )
    return builder.as_markup()


def build_support_keyboard(support_link: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Написать оператору", url=support_link))
    builder.row(
        InlineKeyboardButton(
            text="⬅ Главное меню", callback_data=MenuCallback(action="home").pack()
        )
    )
    return builder.as_markup()
