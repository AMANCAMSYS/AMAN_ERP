from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class LeaveCarryover(ModelBase):
    __tablename__ = "leave_carryover"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type",
            "year",
            name="leave_carryover_employee_id_leave_type_year_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    entitled_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    used_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    carried_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    expired_days: Mapped[float | None] = mapped_column(Numeric(6, 1), default=0)
    max_carryover: Mapped[float | None] = mapped_column(Numeric(6, 1), default=5)
    calculated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OvertimeRequest(ModelBase):
    __tablename__ = "overtime_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    request_date: Mapped[Date] = mapped_column(Date, nullable=False)
    overtime_date: Mapped[Date] = mapped_column(Date, nullable=False)
    hours: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    overtime_type: Mapped[str | None] = mapped_column(String(20), default="normal")
    multiplier: Mapped[float | None] = mapped_column(Numeric(4, 2), default=1.5)
    calculated_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PerformanceReview(ModelBase):
    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    review_period: Mapped[str] = mapped_column(String(50), nullable=False)
    review_date: Mapped[Date] = mapped_column(Date, nullable=False)
    review_type: Mapped[str | None] = mapped_column(String(30), default="annual")
    overall_rating: Mapped[float | None] = mapped_column(Numeric(3, 1), default=0)
    strengths: Mapped[str | None] = mapped_column(Text)
    weaknesses: Mapped[str | None] = mapped_column(Text)
    goals: Mapped[str | None] = mapped_column(Text)
    self_rating: Mapped[float | None] = mapped_column(Numeric(3, 1))
    self_comments: Mapped[str | None] = mapped_column(Text)
    manager_comments: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "LeaveCarryover",
    "OvertimeRequest",
    "PerformanceReview",
]
