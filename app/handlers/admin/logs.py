"""Просмотр логов приложения (/logs)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.callbacks.admin import AdminCallback
from app.filters.is_admin import IsAdmin
from app.keyboards.admin import build_admin_logs_menu_keyboard
from app.utils.constants import LOG_FILE_PATH

router = Router(name="admin_logs")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

_MAX_LINES = 20
_MAX_MESSAGE_LENGTH = 3500


def _read_last_lines(level: str, limit: int = _MAX_LINES) -> list[str]:
    if not LOG_FILE_PATH.exists():
        return []
    matched: list[str] = []
    with LOG_FILE_PATH.open("r", encoding="utf-8", errors="ignore") as log_file:
        for line in log_file:
            if f" {level} " in line:
                matched.append(line.rstrip("\n"))
    return matched[-limit:]


@router.message(Command("logs"))
async def handle_logs_command(message: Message) -> None:
    await message.answer("Выберите уровень логов:", reply_markup=build_admin_logs_menu_keyboard())


@router.callback_query(AdminCallback.filter((F.section == "logs") & (F.action == "menu")))
async def handle_logs_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text("Выберите уровень логов:", reply_markup=build_admin_logs_menu_keyboard())


@router.callback_query(AdminCallback.filter((F.section == "logs") & (F.action == "level")))
async def handle_logs_level(callback: CallbackQuery, callback_data: AdminCallback) -> None:
    lines = _read_last_lines(callback_data.param)
    text = "\n".join(lines) if lines else "Записей этого уровня не найдено."
    if len(text) > _MAX_MESSAGE_LENGTH:
        text = text[-_MAX_MESSAGE_LENGTH:]
    # Внутри code-блока MarkdownV2 экранировать нужно только \ и `.
    escaped = text.replace("\\", "\\\\").replace("`", "\\`")
    await callback.answer()
    if callback.message is not None:
        await callback.message.edit_text(
            f"```\n{escaped}\n```", reply_markup=build_admin_logs_menu_keyboard(), parse_mode="MarkdownV2"
        )
