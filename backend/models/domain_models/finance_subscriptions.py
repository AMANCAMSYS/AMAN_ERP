"""Subscription billing models."""

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import AuditMixin, ModelBase, SoftDeleteMixin


class SubscriptionPlan(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    billing_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="'monthly'"
    )  # monthly, quarterly, annual
    base_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="'SAR'")
    trial_period_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    auto_renewal: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class SubscriptionEnrollment(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "subscription_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("parties.id", ondelete="RESTRICT"), nullable=False
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False
    )
    enrollment_date: Mapped[object] = mapped_column(Date, nullable=False)
    trial_end_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    next_billing_date: Mapped[object] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="'active'"
    )  # trial, active, paused, cancelled, at_risk
    cancelled_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_payment_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )


class SubscriptionInvoice(ModelBase, AuditMixin, SoftDeleteMixin):
    __tablename__ = "subscription_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("subscription_enrollments.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    billing_period_start: Mapped[object] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[object] = mapped_column(Date, nullable=False)
    is_prorated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    proration_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


__all__ = [
    "SubscriptionPlan",
    "SubscriptionEnrollment",
    "SubscriptionInvoice",
]
