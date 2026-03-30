from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class OpportunityActivity(ModelBase):
    __tablename__ = "opportunity_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("sales_opportunities.id", ondelete="CASCADE"))
    activity_type: Mapped[str | None] = mapped_column(String(30))
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[DateTime | None] = mapped_column(DateTime)
    completed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime)


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


class PartyTransaction(ModelBase):
    __tablename__ = "party_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100))
    transaction_date: Mapped[Date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    debit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    credit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("payment_vouchers.id", ondelete="SET NULL"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordHistory(ModelBase):
    __tablename__ = "password_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentAllocation(ModelBase):
    __tablename__ = "payment_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    voucher_id: Mapped[int | None] = mapped_column(ForeignKey("payment_vouchers.id", ondelete="CASCADE"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    allocated_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())