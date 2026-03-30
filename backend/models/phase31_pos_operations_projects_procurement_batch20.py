from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class PosOrderPayment(ModelBase):
    __tablename__ = "pos_order_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("pos_orders.id", ondelete="CASCADE"))
    method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosOrder(ModelBase):
    __tablename__ = "pos_orders"
    __table_args__ = (UniqueConstraint("order_number", name="pos_orders_order_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("pos_sessions.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    walk_in_customer_name: Mapped[str | None] = mapped_column(String(255))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    order_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount_type: Mapped[str | None] = mapped_column(String(20), default="amount")
    discount_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    paid_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    change_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    coupon_code: Mapped[str | None] = mapped_column(String(100))
    loyalty_points_earned: Mapped[float | None] = mapped_column(Numeric(12, 2))
    loyalty_points_redeemed: Mapped[float | None] = mapped_column(Numeric(12, 2))
    party_id: Mapped[int | None] = mapped_column(Integer)
    promotion_id: Mapped[int | None] = mapped_column(Integer)
    table_id: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime)


class PosPayment(ModelBase):
    __tablename__ = "pos_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("pos_orders.id", ondelete="CASCADE"))
    session_id: Mapped[int | None] = mapped_column(ForeignKey("pos_sessions.id"))
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosPromotion(ModelBase):
    __tablename__ = "pos_promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    promotion_type: Mapped[str] = mapped_column(String(50), nullable=False, default="percentage")
    value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    buy_qty: Mapped[int | None] = mapped_column(Integer)
    get_qty: Mapped[int | None] = mapped_column(Integer)
    coupon_code: Mapped[str | None] = mapped_column(String(100))
    applicable_products: Mapped[str | None] = mapped_column(Text)
    applicable_categories: Mapped[str | None] = mapped_column(Text)
    min_order_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    start_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosReturnItem(ModelBase):
    __tablename__ = "pos_return_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    return_id: Mapped[int | None] = mapped_column(ForeignKey("pos_returns.id", ondelete="CASCADE"))
    original_item_id: Mapped[int | None] = mapped_column(ForeignKey("pos_order_lines.id", ondelete="SET NULL"))
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosReturn(ModelBase):
    __tablename__ = "pos_returns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_order_id: Mapped[int | None] = mapped_column(ForeignKey("pos_orders.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    session_id: Mapped[int | None] = mapped_column(ForeignKey("pos_sessions.id"))
    refund_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    refund_method: Mapped[str | None] = mapped_column(String(50), default="cash")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PosSession(ModelBase):
    __tablename__ = "pos_sessions"
    __table_args__ = (UniqueConstraint("session_code", name="pos_sessions_session_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_code: Mapped[str | None] = mapped_column(String(50))
    pos_profile_id: Mapped[int | None] = mapped_column(Integer)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    opening_balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    closing_balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total_sales: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total_returns: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    cash_register_balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    difference: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="opened")
    opened_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    treasury_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime)


class PosTableOrder(ModelBase):
    __tablename__ = "pos_table_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int | None] = mapped_column(ForeignKey("pos_tables.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("pos_orders.id", ondelete="SET NULL"))
    seated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cleared_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    guests: Mapped[int | None] = mapped_column(Integer, default=1)
    waiter_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    status: Mapped[str | None] = mapped_column(String(20), default="seated")


class PosTable(ModelBase):
    __tablename__ = "pos_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_number: Mapped[str] = mapped_column(String(50), nullable=False)
    table_name: Mapped[str | None] = mapped_column(String(100))
    floor: Mapped[str | None] = mapped_column(String(50), default="main")
    capacity: Mapped[int | None] = mapped_column(Integer, default=4)
    status: Mapped[str | None] = mapped_column(String(20), default="available")
    shape: Mapped[str | None] = mapped_column(String(20), default="square")
    pos_x: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    pos_y: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PrintTemplate(ModelBase):
    __tablename__ = "print_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    html_template: Mapped[str] = mapped_column(Text, nullable=False)
    css_styles: Mapped[str | None] = mapped_column(Text)
    header_html: Mapped[str | None] = mapped_column(Text)
    footer_html: Mapped[str | None] = mapped_column(Text)
    paper_size: Mapped[str | None] = mapped_column(String(20), default="A4")
    orientation: Mapped[str | None] = mapped_column(String(20), default="portrait")
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductionOrderOperation(ModelBase):
    __tablename__ = "production_order_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    production_order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id", ondelete="CASCADE"))
    operation_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_operations.id"))
    work_center_id: Mapped[int | None] = mapped_column(ForeignKey("work_centers.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    worker_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    actual_setup_time: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    actual_run_time: Mapped[float | None] = mapped_column(Numeric(8, 2), default=0)
    completed_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    scrapped_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    planned_start_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    planned_end_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    start_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sequence: Mapped[int | None] = mapped_column(Integer)


class ProductionOrder(ModelBase):
    __tablename__ = "production_orders"
    __table_args__ = (UniqueConstraint("order_number", name="production_orders_order_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str | None] = mapped_column(String(50))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    bom_id: Mapped[int | None] = mapped_column(ForeignKey("bill_of_materials.id"))
    route_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturing_routes.id"))
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    produced_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    scrapped_quantity: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    start_date: Mapped[Date | None] = mapped_column(Date)
    due_date: Mapped[Date | None] = mapped_column(Date)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    destination_warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actual_material_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    actual_labor_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    actual_overhead_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    actual_total_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    standard_cost: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    variance_amount: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    variance_percentage: Mapped[float | None] = mapped_column(Numeric(8, 4), default=0)
    costing_status: Mapped[str | None] = mapped_column(String(20), default="pending")


class ProjectRisk(ModelBase):
    __tablename__ = "project_risks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    probability: Mapped[str | None] = mapped_column(String(20), default="medium")
    impact: Mapped[str | None] = mapped_column(String(20), default="medium")
    risk_score: Mapped[float | None] = mapped_column(Numeric(5, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(30), default="open")
    mitigation_plan: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    due_date: Mapped[Date | None] = mapped_column(Date)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProjectTimesheet(ModelBase):
    __tablename__ = "project_timesheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    task_id: Mapped[int | None] = mapped_column(ForeignKey("project_tasks.id"))
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    hours: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


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


class Receipt(ModelBase):
    __tablename__ = "receipts"
    __table_args__ = (UniqueConstraint("receipt_number", name="receipts_receipt_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    receipt_number: Mapped[str | None] = mapped_column(String(50))
    receipt_type: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    receipt_date: Mapped[Date] = mapped_column(Date, nullable=False)
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


class ReportTemplate(ModelBase):
    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    parameters: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    template_content: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
