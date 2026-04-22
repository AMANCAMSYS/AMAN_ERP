from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, AuditMixin


class SelfServiceRequest(ModelBase, AuditMixin):
    __tablename__ = "self_service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="leave | profile_update | document_request"
    )
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft",
        comment="draft | pending | approved | rejected | completed",
    )
    approver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
