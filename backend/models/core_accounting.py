from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class CompanyUser(ModelBase):
    __tablename__ = "company_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(50), default="user")
    permissions: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    last_login: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Branch(ModelBase):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_name_en: Mapped[str | None] = mapped_column(String(255))
    branch_type: Mapped[str | None] = mapped_column(String(50), default="branch")
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    country_code: Mapped[str | None] = mapped_column(String(5))
    default_currency: Mapped[str | None] = mapped_column(String(3))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Account(ModelBase):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    account_code: Mapped[str | None] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    is_header: Mapped[bool | None] = mapped_column(Boolean, default=False)
    balance: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    balance_currency: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JournalEntry(ModelBase):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    entry_date: Mapped[Date] = mapped_column(Date, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1.0)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    source: Mapped[str | None] = mapped_column(String(100))
    source_id: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    posted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JournalLine(ModelBase):
    __tablename__ = "journal_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    journal_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    debit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    credit: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    cost_center_id: Mapped[int | None] = mapped_column(Integer)
    amount_currency: Mapped[float | None] = mapped_column(Numeric(18, 4), default=0)
    currency: Mapped[str | None] = mapped_column(String(3))
    description: Mapped[str | None] = mapped_column(Text)
    is_reconciled: Mapped[bool | None] = mapped_column(Boolean, default=False)
    reconciliation_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
