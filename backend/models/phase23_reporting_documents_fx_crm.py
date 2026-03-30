from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import ModelBase


class FinancialReport(ModelBase):
    __tablename__ = "financial_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_period: Mapped[str | None] = mapped_column(String(50))
    generated_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    parameters: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    data: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentType(ModelBase):
    __tablename__ = "document_types"
    __table_args__ = (UniqueConstraint("type_code", name="document_types_type_code_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_code: Mapped[str | None] = mapped_column(String(50))
    type_name: Mapped[str] = mapped_column(String(255), nullable=False)
    type_name_en: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    allowed_extensions: Mapped[str | None] = mapped_column(String(255), default="pdf,jpg,png,doc,docx,xls,xlsx")
    max_size: Mapped[int | None] = mapped_column(Integer, default=10485760)
    is_active: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentTemplate(ModelBase):
    __tablename__ = "document_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    template_content: Mapped[str | None] = mapped_column(Text)
    variables: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    is_default: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CurrencyTransaction(ModelBase):
    __tablename__ = "currency_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_id: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    amount_fc: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    amount_bc: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrmContact(ModelBase):
    __tablename__ = "crm_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100))
    job_title: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30))
    mobile: Mapped[str | None] = mapped_column(String(30))
    department: Mapped[str | None] = mapped_column(String(100))
    is_primary: Mapped[bool | None] = mapped_column(Boolean, default=False)
    is_decision_maker: Mapped[bool | None] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
