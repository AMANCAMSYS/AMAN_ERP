from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class RequestForQuotation(ModelBase):
    __tablename__ = "request_for_quotations"
    __table_args__ = (UniqueConstraint("rfq_number", name="request_for_quotations_rfq_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfq_number: Mapped[str | None] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(30), default="draft")
    deadline: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RfqLine(ModelBase):
    __tablename__ = "rfq_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfq_id: Mapped[int | None] = mapped_column(ForeignKey("request_for_quotations.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50))
    specifications: Mapped[str | None] = mapped_column(Text)


class RfqResponse(ModelBase):
    __tablename__ = "rfq_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rfq_id: Mapped[int | None] = mapped_column(ForeignKey("request_for_quotations.id", ondelete="CASCADE"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    unit_price: Mapped[float | None] = mapped_column(Numeric(15, 2))
    total_price: Mapped[float | None] = mapped_column(Numeric(15, 2))
    delivery_days: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    is_selected: Mapped[bool | None] = mapped_column(Boolean, default=False)
    submitted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalesCommission(ModelBase):
    __tablename__ = "sales_commissions"
    __table_args__ = (UniqueConstraint("invoice_id", "salesperson_id", name="sales_commissions_invoice_id_salesperson_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    salesperson_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    salesperson_name: Mapped[str | None] = mapped_column(String(255))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    invoice_number: Mapped[str | None] = mapped_column(String(100))
    invoice_date: Mapped[Date | None] = mapped_column(Date)
    invoice_total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    commission_rate: Mapped[float | None] = mapped_column(Numeric(10, 4), default=0)
    commission_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(30), default="pending")
    paid_date: Mapped[Date | None] = mapped_column(Date)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalesOpportunity(ModelBase):
    __tablename__ = "sales_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_email: Mapped[str | None] = mapped_column(String(150))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    stage: Mapped[str | None] = mapped_column(String(30), default="lead")
    probability: Mapped[int | None] = mapped_column(Integer, default=10)
    expected_value: Mapped[float | None] = mapped_column(Numeric(18, 2), default=0)
    expected_close_date: Mapped[Date | None] = mapped_column(Date)
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    source: Mapped[str | None] = mapped_column(String(50))
    assigned_to: Mapped[int | None] = mapped_column(Integer)
    branch_id: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    lost_reason: Mapped[str | None] = mapped_column(Text)
    won_quotation_id: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalesOrderLine(ModelBase):
    __tablename__ = "sales_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    so_id: Mapped[int | None] = mapped_column(ForeignKey("sales_orders.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)


class SalesOrder(ModelBase):
    __tablename__ = "sales_orders"
    __table_args__ = (UniqueConstraint("so_number", name="sales_orders_so_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    so_number: Mapped[str] = mapped_column(String(50), nullable=False)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    quotation_id: Mapped[int | None] = mapped_column(ForeignKey("sales_quotations.id"))
    order_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Date | None] = mapped_column(Date)
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(3), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_quotation_id: Mapped[int | None] = mapped_column(Integer)


class SalesQuotationLine(ModelBase):
    __tablename__ = "sales_quotation_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sq_id: Mapped[int | None] = mapped_column(ForeignKey("sales_quotations.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)


class SalesQuotation(ModelBase):
    __tablename__ = "sales_quotations"
    __table_args__ = (UniqueConstraint("sq_number", name="sales_quotations_sq_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sq_number: Mapped[str] = mapped_column(String(50), nullable=False)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    quotation_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Date | None] = mapped_column(Date)
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    terms_conditions: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(3), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversion_date: Mapped[DateTime | None] = mapped_column(DateTime)
    converted_to_order_id: Mapped[int | None] = mapped_column(Integer)


class SalesReturnLine(ModelBase):
    __tablename__ = "sales_return_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    return_id: Mapped[int | None] = mapped_column(ForeignKey("sales_returns.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)


class SalesReturn(ModelBase):
    __tablename__ = "sales_returns"
    __table_args__ = (UniqueConstraint("return_number", name="sales_returns_return_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    return_number: Mapped[str] = mapped_column(String(50), nullable=False)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    return_date: Mapped[Date] = mapped_column(Date, nullable=False)
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    refund_method: Mapped[str | None] = mapped_column(String(20))
    refund_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id", ondelete="SET NULL"))
    treasury_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    check_number: Mapped[str | None] = mapped_column(String(50))
    check_date: Mapped[Date | None] = mapped_column(Date)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), default=1.0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    currency: Mapped[str | None] = mapped_column(String(10))


class SalesTarget(ModelBase):
    __tablename__ = "sales_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month_number: Mapped[int] = mapped_column(Integer, nullable=False)
    target_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    salesperson_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "RequestForQuotation",
    "RfqLine",
    "RfqResponse",
    "SalesCommission",
    "SalesOpportunity",
    "SalesOrderLine",
    "SalesOrder",
    "SalesQuotationLine",
    "SalesQuotation",
    "SalesReturnLine",
    "SalesReturn",
    "SalesTarget",
]
