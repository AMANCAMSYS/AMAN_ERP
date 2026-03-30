from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase

class SupplierBalance(ModelBase):
    __tablename__ = "supplier_balances"
    __table_args__ = (UniqueConstraint("supplier_id", name="supplier_balances_supplier_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    currency: Mapped[str | None] = mapped_column(String(3))
    total_payable: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
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


class SupplierBankAccount(ModelBase):
    __tablename__ = "supplier_bank_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"))
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_name_en: Mapped[str | None] = mapped_column(String(255))
    account_number: Mapped[str | None] = mapped_column(String(50))
    iban: Mapped[str | None] = mapped_column(String(50))
    swift_code: Mapped[str | None] = mapped_column(String(20))
    branch_name: Mapped[str | None] = mapped_column(String(255))
    branch_code: Mapped[str | None] = mapped_column(String(50))
    account_holder: Mapped[str | None] = mapped_column(String(255))
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierContact(ModelBase):
    __tablename__ = "supplier_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"))
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name_en: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(100))
    department: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    is_primary: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierGroup(ModelBase):
    __tablename__ = "supplier_groups"
    __table_args__ = (UniqueConstraint("group_code", name="supplier_groups_group_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_code: Mapped[str | None] = mapped_column(String(50))
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_groups.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    discount_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    effect_type: Mapped[str | None] = mapped_column(String(20), default="discount")
    application_scope: Mapped[str | None] = mapped_column(String(20), default="total")
    payment_days: Mapped[int | None] = mapped_column(Integer, default=30)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierPayment(ModelBase):
    __tablename__ = "supplier_payments"
    __table_args__ = (UniqueConstraint("payment_number", name="supplier_payments_payment_number_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_number: Mapped[str | None] = mapped_column(String(50))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    payment_date: Mapped[Date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), default=1)
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id", ondelete="SET NULL"))
    reference: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierRating(ModelBase):
    __tablename__ = "supplier_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    po_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id", ondelete="SET NULL"))
    quality_score: Mapped[float | None] = mapped_column(Numeric(3, 1), default=0)
    delivery_score: Mapped[float | None] = mapped_column(Numeric(3, 1), default=0)
    price_score: Mapped[float | None] = mapped_column(Numeric(3, 1), default=0)
    service_score: Mapped[float | None] = mapped_column(Numeric(3, 1), default=0)
    overall_score: Mapped[float | None] = mapped_column(Numeric(3, 1), default=0)
    comments: Mapped[str | None] = mapped_column(Text)
    rated_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    rated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierTransaction(ModelBase):
    __tablename__ = "supplier_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100))
    transaction_date: Mapped[Date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    debit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    credit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_payments.id", ondelete="SET NULL"))
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Supplier(ModelBase):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("supplier_code", name="suppliers_supplier_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supplier_code: Mapped[str | None] = mapped_column(String(50))
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_name_en: Mapped[str | None] = mapped_column(String(255))
    tax_number: Mapped[str | None] = mapped_column(String(50))
    commercial_register: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    fax: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    supplier_group_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_groups.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    payment_terms: Mapped[str | None] = mapped_column(String(100))
    credit_limit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    current_balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    tax_exempt: Mapped[bool | None] = mapped_column(Boolean, default=False)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskDependency(ModelBase):
    __tablename__ = "task_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_task_id: Mapped[int] = mapped_column(ForeignKey("project_tasks.id", ondelete="CASCADE"), nullable=False)
    dependency_type: Mapped[str | None] = mapped_column(String(20), default="finish_to_start")
    lag_days: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaxCalendar(ModelBase):
    __tablename__ = "tax_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_type: Mapped[str | None] = mapped_column(String(50))
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    reminder_days: Mapped[dict | list | None] = mapped_column(JSONB, default=lambda: [7, 3, 1])
    is_recurring: Mapped[bool | None] = mapped_column(Boolean, default=False)
    recurrence_months: Mapped[int | None] = mapped_column(Integer, default=3)
    is_completed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    recurrence_pattern: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(String(20))


class TrainingParticipant(ModelBase):
    __tablename__ = "training_participants"
    __table_args__ = (UniqueConstraint("training_id", "employee_id", name="training_participants_training_id_employee_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    training_id: Mapped[int | None] = mapped_column(ForeignKey("training_programs.id", ondelete="CASCADE"))
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    attendance_status: Mapped[str | None] = mapped_column(String(20), default="registered")
    certificate_issued: Mapped[bool | None] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TrainingProgram(ModelBase):
    __tablename__ = "training_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    trainer: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    max_participants: Mapped[int | None] = mapped_column(Integer)
    cost: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="planned")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User2FASetting(ModelBase):
    __tablename__ = "user_2fa_settings"
    __table_args__ = (UniqueConstraint("user_id", name="user_2fa_settings_user_id_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    secret_key: Mapped[str | None] = mapped_column(String(100))
    is_enabled: Mapped[bool | None] = mapped_column(Boolean, default=False)
    backup_codes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    backup_codes_used: Mapped[int | None] = mapped_column(Integer)


class UserSession(ModelBase):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    token_hash: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(Text)
    login_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)


class WebhookLog(ModelBase):
    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    webhook_id: Mapped[int | None] = mapped_column(ForeignKey("webhooks.id", ondelete="CASCADE"))
    event: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict | list | None] = mapped_column(JSONB)
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    success: Mapped[bool | None] = mapped_column(Boolean, default=False)
    attempt: Mapped[int | None] = mapped_column(Integer, default=1)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    error_message: Mapped[str | None] = mapped_column(Text)


class Webhook(ModelBase):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str | None] = mapped_column(String(255))
    events: Mapped[dict | list] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    retry_count: Mapped[int | None] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, default=10)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WhtRate(ModelBase):
    __tablename__ = "wht_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(100))
    rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), default="general")
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WhtTransaction(ModelBase):
    __tablename__ = "wht_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int | None] = mapped_column(Integer)
    payment_id: Mapped[int | None] = mapped_column(Integer)
    supplier_id: Mapped[int | None] = mapped_column(Integer)
    wht_rate_id: Mapped[int | None] = mapped_column(ForeignKey("wht_rates.id"))
    gross_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    wht_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    wht_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    net_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    certificate_number: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    journal_entry_id: Mapped[int | None] = mapped_column(Integer)
    period_date: Mapped[Date | None] = mapped_column(Date)


class WorkCenter(ModelBase):
    __tablename__ = "work_centers"
    __table_args__ = (UniqueConstraint("code", name="work_centers_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50))
    capacity_per_day: Mapped[float | None] = mapped_column(Numeric(5, 2), default=8.0)
    cost_per_hour: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    location: Mapped[str | None] = mapped_column(String(100))
    cost_center_id: Mapped[int | None] = mapped_column(ForeignKey("cost_centers.id"))
    default_expense_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
