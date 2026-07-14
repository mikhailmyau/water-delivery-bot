"""Репозиторий журнала аудита администратора."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.admin_audit_log import AdminAuditLog
from app.database.repositories.base import BaseRepository


class AdminAuditLogRepository(BaseRepository):
    """Доступ к таблице admin_audit_log."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add(
        self,
        admin_telegram_id: int,
        action: str,
        old_value: str | None,
        new_value: str | None,
    ) -> AdminAuditLog:
        record = AdminAuditLog(
            admin_telegram_id=admin_telegram_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_recent(self, limit: int = 50) -> list[AdminAuditLog]:
        result = await self.session.execute(
            select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
