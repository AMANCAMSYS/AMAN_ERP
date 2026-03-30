from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class CustomerTransaction(ModelBase):
    __tablename__ = "customer_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100))
    transaction_date: Mapped[Date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    debit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    credit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    receipt_id: Mapped[int | None] = mapped_column(ForeignKey("customer_receipts.id", ondelete="SET NULL"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerReceipt(ModelBase):
    __tablename__ = "customer_receipts"
    __table_args__ = (UniqueConstraint("receipt_number", name="customer_receipts_receipt_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_number: Mapped[str | None] = mapped_column(String(50))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    receipt_date: Mapped[Date] = mapped_column(Date, nullable=False)
    receipt_method: Mapped[str | None] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), default=None)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), default=1)
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id", ondelete="SET NULL"))
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerBalance(ModelBase):
    __tablename__ = "customer_balances"
    __table_args__ = (UniqueConstraint("customer_id", name="customer_balances_customer_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    currency: Mapped[str | None] = mapped_column(String(3), default=None)
    total_receivable: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total_paid: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    outstanding_balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    overdue_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    aging_30: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    aging_60: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    aging_90: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    aging_120: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    aging_120_plus: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    last_payment_date: Mapped[Date | None] = mapped_column(Date)
    last_invoice_date: Mapped[Date | None] = mapped_column(Date)
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliveryOrder(ModelBase):
    __tablename__ = "delivery_orders"
    __table_args__ = (UniqueConstraint("delivery_number", name="delivery_orders_delivery_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_number: Mapped[str] = mapped_column(String(50), nullable=False)
    delivery_date: Mapped[Date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    sales_order_id: Mapped[int | None] = mapped_column(ForeignKey("sales_orders.id"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    status: Mapped[str | None] = mapped_column(String(30), default="draft")
    shipping_method: Mapped[str | None] = mapped_column(String(100))
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    driver_name: Mapped[str | None] = mapped_column(String(100))
    driver_phone: Mapped[str | None] = mapped_column(String(50))
    vehicle_number: Mapped[str | None] = mapped_column(String(50))
    delivery_address: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    total_items: Mapped[int | None] = mapped_column(Integer, default=0)
    total_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    shipped_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliveryOrderLine(ModelBase):
    __tablename__ = "delivery_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    delivery_order_id: Mapped[int] = mapped_column(ForeignKey("delivery_orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    so_line_id: Mapped[int | None] = mapped_column(ForeignKey("sales_order_lines.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)
    ordered_qty: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    delivered_qty: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    unit: Mapped[str | None] = mapped_column(String(50))
    batch_number: Mapped[str | None] = mapped_column(String(100))
    serial_numbers: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
