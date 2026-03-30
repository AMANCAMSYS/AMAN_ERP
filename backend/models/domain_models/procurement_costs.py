from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class LandedCost(ModelBase):
    __tablename__ = "landed_costs"
    __table_args__ = (UniqueConstraint("lc_number", name="landed_costs_lc_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lc_number: Mapped[str] = mapped_column(String(50), nullable=False)
    lc_date: Mapped[Date] = mapped_column(Date, nullable=False)
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"))
    grn_id: Mapped[int | None] = mapped_column(Integer)
    reference: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    total_amount: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    allocation_method: Mapped[str | None] = mapped_column(String(30), default="by_value")
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    notes: Mapped[str | None] = mapped_column(Text)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LandedCostItem(ModelBase):
    __tablename__ = "landed_cost_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    landed_cost_id: Mapped[int] = mapped_column(ForeignKey("landed_costs.id", ondelete="CASCADE"), nullable=False)
    cost_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    invoice_ref: Mapped[str | None] = mapped_column(String(100))
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


class PurchaseAgreementLine(ModelBase):
    __tablename__ = "purchase_agreement_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agreement_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_agreements.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[float | None] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[float | None] = mapped_column(Numeric(15, 2))
    delivered_qty: Mapped[float | None] = mapped_column(Numeric(12, 3), default=0)


class PurchaseAgreement(ModelBase):
    __tablename__ = "purchase_agreements"
    __table_args__ = (UniqueConstraint("agreement_number", name="purchase_agreements_agreement_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agreement_number: Mapped[str | None] = mapped_column(String(50))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    agreement_type: Mapped[str | None] = mapped_column(String(30), default="blanket")
    title: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    total_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    consumed_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    status: Mapped[str | None] = mapped_column(String(30), default="draft")
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "LandedCost",
    "LandedCostItem",
    "PendingPayable",
    "PurchaseAgreementLine",
    "PurchaseAgreement",
]
