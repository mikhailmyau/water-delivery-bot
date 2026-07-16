"""Репозитории — единственная точка доступа к данным для сервисов."""

from app.database.repositories.admin_audit_log_repository import AdminAuditLogRepository
from app.database.repositories.analytics_repository import AnalyticsRepository
from app.database.repositories.order_repository import OrderRepository
from app.database.repositories.payment_repository import PaymentRepository
from app.database.repositories.settings_repository import SettingsRepository
from app.database.repositories.user_repository import UserRepository

__all__ = [
    "AdminAuditLogRepository",
    "AnalyticsRepository",
    "OrderRepository",
    "PaymentRepository",
    "SettingsRepository",
    "UserRepository",
]
