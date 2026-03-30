from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


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


class PendingPayable(ModelBase):
    __tablename__ = "pending_payables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    invoice_number: Mapped[str | None] = mapped_column(String(50))
    due_date: Mapped[Date | None] = mapped_column(Date)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    paid_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    outstanding_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    days_overdue: Mapped[int | None] = mapped_column(Integer, default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PendingReceivable(ModelBase):
    __tablename__ = "pending_receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    invoice_number: Mapped[str | None] = mapped_column(String(50))
    due_date: Mapped[Date | None] = mapped_column(Date)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    paid_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    outstanding_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    days_overdue: Mapped[int | None] = mapped_column(Integer, default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


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


class PosKitchenOrder(ModelBase):
    __tablename__ = "pos_kitchen_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("pos_orders.id", ondelete="SET NULL"))
    order_line_id: Mapped[int | None] = mapped_column(ForeignKey("pos_order_lines.id", ondelete="SET NULL"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    product_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[float | None] = mapped_column(Numeric(12, 3))
    notes: Mapped[str | None] = mapped_column(Text)
    station: Mapped[str | None] = mapped_column(String(100), default="main")
    status: Mapped[str | None] = mapped_column(String(30), default="pending")
    priority: Mapped[int | None] = mapped_column(Integer, default=0)
    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    ready_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    served_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"))


class PosLoyaltyPoint(ModelBase):
    __tablename__ = "pos_loyalty_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("pos_loyalty_programs.id"))
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id", ondelete="SET NULL"))
    points_earned: Mapped[float | None] = mapped_column(Numeric(12, 2), default=0)
    points_redeemed: Mapped[float | None] = mapped_column(Numeric(12, 2), default=0)
    balance: Mapped[float | None] = mapped_column(Numeric(12, 2), default=0)
    tier: Mapped[str | None] = mapped_column(String(50), default="standard")
    last_activity_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosLoyaltyProgram(ModelBase):
    __tablename__ = "pos_loyalty_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    points_per_unit: Mapped[float | None] = mapped_column(Numeric(10, 4), default=1)
    currency_per_point: Mapped[float | None] = mapped_column(Numeric(10, 4), default=0.01)
    min_points_redeem: Mapped[int | None] = mapped_column(Integer, default=100)
    tier_rules: Mapped[list | None] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosLoyaltyTransaction(ModelBase):
    __tablename__ = "pos_loyalty_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loyalty_id: Mapped[int | None] = mapped_column(ForeignKey("pos_loyalty_points.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("pos_orders.id", ondelete="SET NULL"))
    txn_type: Mapped[str] = mapped_column(String(20), nullable=False)
    points: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosOrderLine(ModelBase):
    __tablename__ = "pos_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("pos_orders.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    description: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    original_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    discount_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    subtotal: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    notes: Mapped[str | None] = mapped_column(Text)