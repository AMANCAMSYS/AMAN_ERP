from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class PurchaseOrder(ModelBase):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    supplier_id: Mapped[int | None] = mapped_column(Integer)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    order_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[Date | None] = mapped_column(Date)
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(3), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    effect_type: Mapped[str | None] = mapped_column(String(20), default="discount")
    effect_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    markup_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class PurchaseOrderLine(ModelBase):
    __tablename__ = "purchase_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    description: Mapped[str | None] = mapped_column(String(500))
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=1)
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    received_quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "PurchaseOrder",
    "PurchaseOrderLine",
]
