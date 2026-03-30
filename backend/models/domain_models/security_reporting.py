from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class Role(ModelBase):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("role_name", name="roles_role_name_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role_name_ar: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    permissions: Mapped[dict | list | None] = mapped_column(JSONB, default=list)
    is_system_role: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScheduledReport(ModelBase):
    __tablename__ = "scheduled_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_name: Mapped[str | None] = mapped_column(String(255))
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_config: Mapped[dict | list | None] = mapped_column(JSONB, default=dict)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    recipients: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str | None] = mapped_column(String(10), default="pdf")
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    next_run_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str | None] = mapped_column(String(20), default="pending")
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SecurityEvent(ModelBase):
    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str | None] = mapped_column(String(20), default="info")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict | list | None] = mapped_column(JSONB, default=dict)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SharedReport(ModelBase):
    __tablename__ = "shared_reports"
    __table_args__ = (UniqueConstraint("report_type", "report_id", "shared_with", name="shared_reports_report_type_report_id_shared_with_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False)
    report_id: Mapped[int] = mapped_column(Integer, nullable=False)
    shared_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    shared_with: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    permission: Mapped[str | None] = mapped_column(String(20), default="view")
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User2FASetting(ModelBase):
    __tablename__ = "user_2fa_settings"
    __table_args__ = (UniqueConstraint("user_id", name="user_2fa_settings_user_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    secret_key: Mapped[str | None] = mapped_column(String(100))
    is_enabled: Mapped[bool | None] = mapped_column(Boolean, default=False)
    backup_codes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    backup_codes_used: Mapped[int | None] = mapped_column(Integer)


class UserSession(ModelBase):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    token_hash: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)
    login_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)


class WebhookLog(ModelBase):
    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    webhook_id: Mapped[int | None] = mapped_column(ForeignKey("webhooks.id", ondelete="CASCADE"))
    event: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict | list | None] = mapped_column(JSONB)
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    success: Mapped[bool | None] = mapped_column(Boolean, default=False)
    attempt: Mapped[int | None] = mapped_column(Integer, default=1)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    error_message: Mapped[str | None] = mapped_column(Text)


class Webhook(ModelBase):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str | None] = mapped_column(String(255))
    events: Mapped[dict | list] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    retry_count: Mapped[int | None] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, default=10)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "Role",
    "ScheduledReport",
    "SecurityEvent",
    "SharedReport",
    "User2FASetting",
    "UserSession",
    "WebhookLog",
    "Webhook",
]
