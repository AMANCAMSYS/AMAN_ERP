from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class Currency(ModelBase):
    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    symbol: Mapped[str | None] = mapped_column(String(10))
    is_base: Mapped[bool | None] = mapped_column(Boolean, default=False)
    current_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), default=1)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExchangeRate(ModelBase):
    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("currency_id", "rate_date", name="exchange_rates_currency_id_rate_date_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    currency_id: Mapped[int | None] = mapped_column(ForeignKey("currencies.id", ondelete="CASCADE"))
    rate_date: Mapped[Date] = mapped_column(Date, nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), default="manual")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BankImportBatch(ModelBase):
    __tablename__ = "bank_import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_name: Mapped[str | None] = mapped_column(String(300))
    bank_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id", ondelete="SET NULL"))
    total_lines: Mapped[int | None] = mapped_column(Integer, default=0)
    imported_lines: Mapped[int | None] = mapped_column(Integer, default=0)
    matched_lines: Mapped[int | None] = mapped_column(Integer, default=0)
    total_debit: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    total_credit: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BankImportLine(ModelBase):
    __tablename__ = "bank_import_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("bank_import_batches.id", ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int | None] = mapped_column(Integer, default=0)
    transaction_date: Mapped[Date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(200))
    debit: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    credit: Mapped[float | None] = mapped_column(Numeric(15, 4), default=0)
    balance: Mapped[float | None] = mapped_column(Numeric(15, 4))
    status: Mapped[str | None] = mapped_column(String(20), default="unmatched")
    matched_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_transactions.id", ondelete="SET NULL"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
