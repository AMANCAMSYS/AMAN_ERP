from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase, AuditMixin, SoftDeleteMixin


class LeaveCarryover(AuditMixin, ModelBase):
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


class OvertimeRequest(AuditMixin, SoftDeleteMixin, ModelBase):
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


class PerformanceReview(AuditMixin, ModelBase):
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
    # US12 cycle-based fields
    cycle_id: Mapped[int | None] = mapped_column(ForeignKey("review_cycles.id", ondelete="SET NULL"))
    self_assessment: Mapped[dict | None] = mapped_column(JSONB)
    manager_assessment: Mapped[dict | None] = mapped_column(JSONB)
    composite_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    final_comments: Mapped[str | None] = mapped_column(Text)


class ReviewCycle(AuditMixin, ModelBase):
    """Review cycle defining the period and deadlines for performance reviews."""
    __tablename__ = "review_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    period_end: Mapped[Date] = mapped_column(Date, nullable=False)
    self_assessment_deadline: Mapped[Date | None] = mapped_column(Date)
    manager_review_deadline: Mapped[Date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    created_by: Mapped[int | None] = mapped_column(Integer)


class PerformanceGoal(AuditMixin, ModelBase):
    """Individual goal within a performance review with weight and target."""
    __tablename__ = "performance_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("performance_reviews.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    target: Mapped[str | None] = mapped_column(String(500))


__all__ = [
    "LeaveCarryover",
    "OvertimeRequest",
    "PerformanceReview",
    "ReviewCycle",
    "PerformanceGoal",
]
