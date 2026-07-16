"""Пользовательские inline-клавиатуры."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks.catalog import BottleCallback, WaterTypeCallback
from app.callbacks.city import CityCallback
from app.callbacks.faq import FaqCallback
from app.callbacks.main_menu import MenuCallback
from app.callbacks.order import OrderCallback
from app.content import WATER_TYPE_LABELS, WATER_TYPE_ORDER
from app.data.cities import CityEntry
from app.database.models.water_type import WaterType
from app.utils.money import format_price


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 Заказать воду", callback_data=MenuCallback(action="order").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🚚 Доставка", callback_data=MenuCallback(action="delivery").pack()
        ),
        InlineKeyboardButton(text="❓ FAQ", callback_data=MenuCallback(action="faq").pack()),
    )
    builder.row(
        InlineKeyboardButton(
            text="📞 Поддержка", callback_data=MenuCallback(action="support").pack()
        )
    )
    return builder.as_markup()


def build_water_type_keyboard(
    prices: dict[WaterType, int], selected: WaterType | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for water_type in WATER_TYPE_ORDER:
        label = WATER_TYPE_LABELS[water_type]
        price_text = format_price(prices[water_type])
        text = (
            f"• {label} — {price_text}/л •"
            if water_type == selected
            else f"{label} — {price_text}/л"
        )
        builder.row(
            InlineKeyboardButton(
                text=text, callback_data=WaterTypeCallback(code=water_type.value).pack()
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Главное меню", callback_data=MenuCallback(action="home").pack()
        )
    )
    return builder.as_markup()


def build_bottle_stepper_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➖", callback_data=BottleCallback(action="dec").pack()),
        InlineKeyboardButton(text="➕", callback_data=BottleCallback(action="inc").pack()),
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Продолжить оформление", callback_data=BottleCallback(action="continue").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅ Назад", callback_data=BottleCallback(action="back").pack())
    )
    return builder.as_markup()


def build_city_letters_keyboard(letters: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    letter_buttons = [
        InlineKeyboardButton(
            text=letter, callback_data=CityCallback(action="letter", value=letter).pack()
        )
        for letter in letters
    ]
    builder.row(*letter_buttons, width=7)
    builder.row(
        InlineKeyboardButton(
            text="✏️ Не нашёл свой город", callback_data=CityCallback(action="manual").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅ Главное меню", callback_data=MenuCallback(action="home").pack()
        )
    )
    return builder.as_markup()


def build_city_list_keyboard(cities: list[CityEntry]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    city_buttons = [
        InlineKeyboardButton(
            text=city.name, callback_data=CityCallback(action="pick", value=str(city.id)).pack()
        )
        for city in cities
    ]
    builder.row(*city_buttons, width=2)
    builder.row(
        InlineKeyboardButton(
            text="⬅ Все буквы", callback_data=CityCallback(action="letters").pack()
        ),
        InlineKeyboardButton(
            text="✏️ Свой город", callback_data=CityCallback(action="manual").pack()
        ),
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


def build_first_order_nudge_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 Заказать воду", callback_data=MenuCallback(action="order").pack()
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
