"""Состояния сценария ввода промокода."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PromoStates(StatesGroup):
    """Ожидание ввода промокода пользователем."""

    waiting_code = State()
