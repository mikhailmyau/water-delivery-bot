"""Callback-данные административной панели.

Один универсальный формат (section/action/param) вместо десятка узкоспециальных
классов — панель большая, а действия внутри каждого раздела однотипны.
"""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class AdminCallback(CallbackData, prefix="adm"):
    """section: orders|price|broadcast|analytics|stats|logs|menu."""

    section: str
    action: str
    param: str = ""
