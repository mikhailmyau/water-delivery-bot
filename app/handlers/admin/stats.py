"""Статистика и воронка конверсии (/stats)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.admin import AdminCallback
from app.filters.is_admin import IsAdmin
from app.keyboards.admin import build_admin_stats_period_keyboard
from app.services.stats_service import PeriodStats, StatsService
from app.utils.money import format_price

router = Router(name="admin_stats")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

_PERIOD_LABELS = {"today": "Сегодня", "week": "Неделя", "month": "Месяц", "all": "Всё время"}


def _format_stats(period: str, stats: PeriodStats, funnel: dict[str, int]) -> str:
    return (
        "━━━━━━━━━━━━━━\n"
        f"📊 Статистика — {_PERIOD_LABELS.get(period, period)}\n"
        "━━━━━━━━━━━━━━\n"
        f"Новые пользователи: {stats.new_users}\n"
        f"Созданные заказы: {stats.orders_created}\n"
        f"Оплаченные: {stats.orders_paid}\n"
        f"Неоплаченные: {stats.orders_unpaid}\n"
        f"Конверсия: {stats.conversion_percent}%\n"
        f"Средний чек: {format_price(stats.average_check)}\n"
        f"Общий доход: {format_price(stats.revenue)}\n"
        "━━━━━━━━━━━━━━\n"
        "Воронка\n"
        "━━━━━━━━━━━━━━\n"
        f"Зашли в бота: {funnel['started']}\n"
        f"Открыли каталог: {funnel['catalog_opened']}\n"
        f"Выбрали объём: {funnel['volume_selected']}\n"
        f"Начали оформление: {funnel['order_started']}\n"
        f"Создали заказ: {funnel['order_created']}\n"
        f"Оплатили: {funnel['paid']}\n"
        "━━━━━━━━━━━━━━"
    )


async def _render(session: AsyncSession, period: str) -> str:
    stats_service = StatsService(session)
    stats = await stats_service.get_period_stats(period)
    funnel = await stats_service.get_funnel(period)
    return _format_stats(period, stats, funnel)


@router.message(Command("stats"))
async def handle_stats_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await message.answer(
        await _render(session, "today"), reply_markup=build_admin_stats_period_keyboard()
    )


@router.callback_query(
    AdminCallback.filter(
        ((F.section == "stats") & (F.action == "menu"))
        | ((F.section == "analytics") & (F.action == "menu"))
    )
)
async def handle_stats_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            await _render(session, "today"), reply_markup=build_admin_stats_period_keyboard()
        )


@router.callback_query(AdminCallback.filter((F.section == "stats") & (F.action == "period")))
async def handle_stats_period(
    callback: CallbackQuery, callback_data: AdminCallback, session: AsyncSession
) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            await _render(session, callback_data.param),
            reply_markup=build_admin_stats_period_keyboard(),
        )
