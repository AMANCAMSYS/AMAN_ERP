from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class UserBranch(ModelBase):
    __tablename__ = "user_branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="CASCADE"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PartyGroup(ModelBase):
    __tablename__ = "party_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    group_name: Mapped[str] = mapped_column(String(255), nullable=False)
    group_name_en: Mapped[str | None] = mapped_column(String(255))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    discount_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    effect_type: Mapped[str | None] = mapped_column(String(20), default="discount")
    application_scope: Mapped[str | None] = mapped_column(String(20), default="total")
    payment_days: Mapped[int | None] = mapped_column(Integer, default=30)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Party(ModelBase):
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    party_type: Mapped[str | None] = mapped_column(String(20), default="individual")
    party_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    mobile: Mapped[str | None] = mapped_column(String(50))
    fax: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    tax_number: Mapped[str | None] = mapped_column(String(50))
    commercial_register: Mapped[str | None] = mapped_column(String(50))
    tax_exempt: Mapped[bool | None] = mapped_column(Boolean, default=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    is_customer: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_supplier: Mapped[bool | None] = mapped_column(Boolean, default=False)
    party_group_id: Mapped[int | None] = mapped_column(ForeignKey("party_groups.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    price_list_id: Mapped[int | None] = mapped_column(Integer)
    payment_terms: Mapped[str | None] = mapped_column(String(100))
    credit_limit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    current_balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="active")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class TreasuryAccount(ModelBase):
    __tablename__ = "treasury_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    current_balance: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), default=0)
    gl_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    bank_name: Mapped[str | None] = mapped_column(String(255))
    account_number: Mapped[str | None] = mapped_column(String(100))
    iban: Mapped[str | None] = mapped_column(String(100))
    allow_overdraft: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Warehouse(ModelBase):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    warehouse_name: Mapped[str] = mapped_column(String(255), nullable=False)
    warehouse_name_en: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Invoice(ModelBase):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    customer_id: Mapped[int | None] = mapped_column(Integer)
    supplier_id: Mapped[int | None] = mapped_column(Integer)
    invoice_date: Mapped[Date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Date | None] = mapped_column(Date)
    subtotal: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    effect_type: Mapped[str | None] = mapped_column(String(20), default="discount")
    effect_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    markup_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    paid_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    down_payment_method: Mapped[str | None] = mapped_column(String(20))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id", ondelete="SET NULL"))
    related_invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"))
    currency: Mapped[str | None] = mapped_column(String(3), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class InvoiceLine(ModelBase):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(String(500))
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), default=1)
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    tax_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), default=0)
    discount: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    markup: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    total: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompanySetting(ModelBase):
    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    setting_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    setting_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "CompanySetting",
    "Invoice",
    "InvoiceLine",
    "Party",
    "PartyGroup",
    "TreasuryAccount",
    "UserBranch",
    "Warehouse",
]
