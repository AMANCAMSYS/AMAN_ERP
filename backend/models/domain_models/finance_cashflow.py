from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class PaymentVoucher(ModelBase):
    __tablename__ = "payment_vouchers"
    __table_args__ = (UniqueConstraint("voucher_number", name="payment_vouchers_voucher_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    voucher_number: Mapped[str] = mapped_column(String(50), nullable=False)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    voucher_type: Mapped[str] = mapped_column(String(20), nullable=False)
    voucher_date: Mapped[Date] = mapped_column(Date, nullable=False)
    party_type: Mapped[str] = mapped_column(String(20), nullable=False)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id", ondelete="SET NULL"))
    treasury_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    check_number: Mapped[str | None] = mapped_column(String(50))
    check_date: Mapped[Date | None] = mapped_column(Date)
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(3), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    status: Mapped[str | None] = mapped_column(String(20), default="posted")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payment(ModelBase):
    __tablename__ = "payments"
    __table_args__ = (UniqueConstraint("payment_number", name="payments_payment_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_number: Mapped[str | None] = mapped_column(String(50))
    payment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    payment_date: Mapped[Date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), default=1)
    payment_method: Mapped[str | None] = mapped_column(String(50))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id", ondelete="SET NULL"))
    reference: Mapped[str | None] = mapped_column(String(100))
    check_number: Mapped[str | None] = mapped_column(String(50))
    check_date: Mapped[Date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentAllocation(ModelBase):
    __tablename__ = "payment_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    voucher_id: Mapped[int | None] = mapped_column(ForeignKey("payment_vouchers.id", ondelete="CASCADE"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    allocated_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


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


class RecurringJournalLine(ModelBase):
    __tablename__ = "recurring_journal_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("recurring_journal_templates.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    debit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    credit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    description: Mapped[str | None] = mapped_column(Text)
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id", ondelete="SET NULL"))


class RecurringJournalTemplate(ModelBase):
    __tablename__ = "recurring_journal_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(100))
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date | None] = mapped_column(Date)
    next_run_date: Mapped[Date] = mapped_column(Date, nullable=False)
    last_run_date: Mapped[Date | None] = mapped_column(Date)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    auto_post: Mapped[bool | None] = mapped_column(Boolean, default=False)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    run_count: Mapped[int | None] = mapped_column(Integer, default=0)
    max_runs: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "PaymentVoucher",
    "Payment",
    "PaymentAllocation",
    "PartyTransaction",
    "RecurringJournalLine",
    "RecurringJournalTemplate",
]
