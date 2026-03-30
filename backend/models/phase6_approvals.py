from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class ApprovalWorkflow(ModelBase):
    __tablename__ = "approval_workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    conditions: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    steps: Mapped[list | None] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApprovalRequest(ModelBase):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int | None] = mapped_column(ForeignKey("approval_workflows.id"))
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    description: Mapped[str | None] = mapped_column(Text)
    current_step: Mapped[int | None] = mapped_column(Integer, default=1)
    total_steps: Mapped[int | None] = mapped_column(Integer, default=1)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    action_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    action_notes: Mapped[str | None] = mapped_column(Text)
    current_approver_id: Mapped[int | None] = mapped_column(Integer)
    escalated_to: Mapped[int | None] = mapped_column(Integer)
    escalated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApprovalAction(ModelBase):
    __tablename__ = "approval_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int | None] = mapped_column(ForeignKey("approval_requests.id", ondelete="CASCADE"))
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    actioned_by: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    actioned_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
