"""Массовая рассылка (/broadcast)."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.callbacks.admin import AdminCallback
from app.database.models.user import User
from app.database.repositories.admin_audit_log_repository import AdminAuditLogRepository
from app.filters.is_admin import IsAdmin
from app.keyboards.admin import (
    build_admin_broadcast_preview_keyboard,
    build_admin_main_menu_keyboard,
)
from app.services.broadcast_service import BroadcastContent, BroadcastContentType, BroadcastService
from app.states.admin_states import AdminBroadcastStates

router = Router(name="admin_broadcast")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _extract_content(message: Message) -> BroadcastContent | None:
    if message.photo:
        return BroadcastContent(
            BroadcastContentType.PHOTO, message.caption, message.photo[-1].file_id
        )
    if message.video:
        return BroadcastContent(BroadcastContentType.VIDEO, message.caption, message.video.file_id)
    if message.animation:
        return BroadcastContent(
            BroadcastContentType.ANIMATION, message.caption, message.animation.file_id
        )
    if message.document:
        return BroadcastContent(
            BroadcastContentType.DOCUMENT, message.caption, message.document.file_id
        )
    if message.text:
        return BroadcastContent(BroadcastContentType.TEXT, message.text, None)
    return None


async def _resend_preview(message: Message, content: BroadcastContent) -> None:
    keyboard = build_admin_broadcast_preview_keyboard()
    if content.content_type == BroadcastContentType.TEXT:
        await message.answer(content.text or "", reply_markup=keyboard)
        return

    # Для всех остальных типов file_id всегда заполнен — см. _extract_content.
    file_id = content.file_id
    assert file_id is not None
    if content.content_type == BroadcastContentType.PHOTO:
        await message.answer_photo(file_id, caption=content.text, reply_markup=keyboard)
    elif content.content_type == BroadcastContentType.VIDEO:
        await message.answer_video(file_id, caption=content.text, reply_markup=keyboard)
    elif content.content_type == BroadcastContentType.ANIMATION:
        await message.answer_animation(file_id, caption=content.text, reply_markup=keyboard)
    elif content.content_type == BroadcastContentType.DOCUMENT:
        await message.answer_document(file_id, caption=content.text, reply_markup=keyboard)


@router.message(Command("broadcast"))
async def handle_broadcast_command(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminBroadcastStates.waiting_content)
    await message.answer("Отправьте текст, фото, видео, GIF или документ для рассылки.")


@router.callback_query(AdminCallback.filter((F.section == "broadcast") & (F.action == "start")))
async def handle_broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminBroadcastStates.waiting_content)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            "Отправьте текст, фото, видео, GIF или документ для рассылки."
        )


@router.message(AdminBroadcastStates.waiting_content)
async def handle_broadcast_content(message: Message, state: FSMContext) -> None:
    content = _extract_content(message)
    if content is None:
        await message.answer(
            "Не удалось распознать содержимое. Отправьте текст, фото, видео, GIF или документ."
        )
        return
    await state.update_data(
        content_type=content.content_type.value,
        content_text=content.text,
        content_file_id=content.file_id,
    )
    await state.set_state(AdminBroadcastStates.waiting_confirmation)
    await message.answer("Так будет выглядеть рассылка:")
    await _resend_preview(message, content)


@router.callback_query(
    AdminBroadcastStates.waiting_confirmation,
    AdminCallback.filter((F.section == "broadcast") & (F.action == "restart")),
)
async def handle_broadcast_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminBroadcastStates.waiting_content)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            "Отправьте текст, фото, видео, GIF или документ для рассылки."
        )


@router.callback_query(
    AdminBroadcastStates.waiting_confirmation,
    AdminCallback.filter((F.section == "broadcast") & (F.action == "cancel")),
)
async def handle_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Рассылка отменена.")
    if isinstance(callback.message, Message):
        await callback.message.answer(
            "⚙ Панель управления", reply_markup=build_admin_main_menu_keyboard()
        )


@router.callback_query(
    AdminBroadcastStates.waiting_confirmation,
    AdminCallback.filter((F.section == "broadcast") & (F.action == "send")),
)
async def handle_broadcast_send(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, user: User, bot: Bot
) -> None:
    data = await state.get_data()
    content = BroadcastContent(
        BroadcastContentType(data["content_type"]),
        data.get("content_text"),
        data.get("content_file_id"),
    )
    await state.clear()
    await callback.answer("Рассылка запущена…")

    result = await BroadcastService(bot, session).send(content)
    await AdminAuditLogRepository(session).add(
        user.telegram_id,
        "broadcast_sent",
        None,
        f"sent={result.sent} blocked={result.blocked} failed={result.failed}",
    )

    if isinstance(callback.message, Message):
        await callback.message.answer(
            "━━━━━━━━━━━━━━\n"
            "Рассылка завершена.\n\n"
            f"Доставлено: {result.sent}\n"
            f"Заблокировали бота: {result.blocked}\n"
            f"Ошибок: {result.failed}\n"
            "━━━━━━━━━━━━━━",
            reply_markup=build_admin_main_menu_keyboard(),
        )
