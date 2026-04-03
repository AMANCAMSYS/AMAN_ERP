from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class ApiKey(ModelBase):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    permissions: Mapped[list | None] = mapped_column(JSONB, default=list)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer, default=60)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(Integer)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text)


class AuditLog(ModelBase):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    username: Mapped[str | None] = mapped_column(String(100))
    action: Mapped[str | None] = mapped_column(String(100))
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[str | None] = mapped_column(String(50))
    details: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BackupHistory(ModelBase):
    __tablename__ = "backup_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backup_type: Mapped[str | None] = mapped_column(String(20), default="manual")
    file_name: Mapped[str | None] = mapped_column(String(300))
    file_size: Mapped[int | None] = mapped_column(BigInteger, default=0)
    file_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text)
    tables_included: Mapped[int | None] = mapped_column(Integer, default=0)
    rows_exported: Mapped[int | None] = mapped_column(BigInteger, default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class CustomReport(ModelBase):
    __tablename__ = "custom_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailTemplate(ModelBase):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    variables: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckStatusLog(ModelBase):
    __tablename__ = "check_status_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    check_type: Mapped[str] = mapped_column(String(20), nullable=False)
    check_id: Mapped[int] = mapped_column(Integer, nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(30))
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    changed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FinancialReport(ModelBase):
    __tablename__ = "financial_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_period: Mapped[str | None] = mapped_column(String(50))
    generated_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    parameters: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    data: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentType(ModelBase):
    __tablename__ = "document_types"
    __table_args__ = (UniqueConstraint("type_code", name="document_types_type_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_code: Mapped[str | None] = mapped_column(String(50))
    type_name: Mapped[str] = mapped_column(String(255), nullable=False)
    type_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    allowed_extensions: Mapped[str | None] = mapped_column(String(255), default="pdf,jpg,png,doc,docx,xls,xlsx")
    max_size: Mapped[int | None] = mapped_column(Integer, default=10485760)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentTemplate(ModelBase):
    __tablename__ = "document_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    template_content: Mapped[str | None] = mapped_column(Text)
    variables: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "ApiKey",
    "AuditLog",
    "BackupHistory",
    "CheckStatusLog",
    "CustomReport",
    "DocumentTemplate",
    "DocumentType",
    "EmailTemplate",
    "FinancialReport",
]
