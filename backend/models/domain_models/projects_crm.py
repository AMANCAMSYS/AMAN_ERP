from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class TimesheetEntry(ModelBase):
    """Timesheet entry for project time tracking (US17)."""

    __tablename__ = "timesheet_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("project_tasks.id"), nullable=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    hours: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    is_billable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    billing_rate: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"), nullable=True)


class ResourceAllocation(ModelBase):
    """Resource allocation for project resource planning (US18)."""

    __tablename__ = "resource_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    allocation_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"), nullable=True)
