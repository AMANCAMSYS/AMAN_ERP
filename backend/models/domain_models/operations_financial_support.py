from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func, text as sa_text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import ModelBase


class CheckReceivable(ModelBase):
    __tablename__ = "checks_receivable"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    check_number: Mapped[str] = mapped_column(String(50), nullable=False)
    drawer_name: Mapped[str | None] = mapped_column(String(200))
    bank_name: Mapped[str | None] = mapped_column(String(200))
    branch_name: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    issue_date: Mapped[Date | None] = mapped_column(Date)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    collection_date: Mapped[Date | None] = mapped_column(Date)
    bounce_date: Mapped[Date | None] = mapped_column(Date)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    treasury_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    receipt_id: Mapped[int | None] = mapped_column(Integer)
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    collection_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    bounce_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    status: Mapped[str | None] = mapped_column(String(30), default="pending")
    bounce_reason: Mapped[str | None] = mapped_column(Text)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), server_default=sa_text("1.0"))
    re_presentation_date: Mapped[Date | None] = mapped_column(Date)
    re_presentation_count: Mapped[int | None] = mapped_column(Integer, server_default=sa_text("0"))
    re_presentation_journal_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CheckPayable(ModelBase):
    __tablename__ = "checks_payable"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    check_number: Mapped[str] = mapped_column(String(50), nullable=False)
    beneficiary_name: Mapped[str | None] = mapped_column(String(200))
    bank_name: Mapped[str | None] = mapped_column(String(200))
    branch_name: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    issue_date: Mapped[Date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    clearance_date: Mapped[Date | None] = mapped_column(Date)
    bounce_date: Mapped[Date | None] = mapped_column(Date)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    treasury_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    payment_voucher_id: Mapped[int | None] = mapped_column(Integer)
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    clearance_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    bounce_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    status: Mapped[str | None] = mapped_column(String(30), default="issued")
    bounce_reason: Mapped[str | None] = mapped_column(Text)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), server_default=sa_text("1.0"))
    re_presentation_date: Mapped[Date | None] = mapped_column(Date)
    re_presentation_count: Mapped[int | None] = mapped_column(Integer, server_default=sa_text("0"))
    re_presentation_journal_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NoteReceivable(ModelBase):
    __tablename__ = "notes_receivable"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    note_number: Mapped[str] = mapped_column(String(50), nullable=False)
    drawer_name: Mapped[str | None] = mapped_column(String(200))
    bank_name: Mapped[str | None] = mapped_column(String(200))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    issue_date: Mapped[Date | None] = mapped_column(Date)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[Date | None] = mapped_column(Date)
    collection_date: Mapped[Date | None] = mapped_column(Date)
    protest_date: Mapped[Date | None] = mapped_column(Date)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    treasury_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    collection_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    protest_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="pending")
    protest_reason: Mapped[str | None] = mapped_column(Text)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), server_default=sa_text("1.0"))
    notes: Mapped[str | None] = mapped_column(Text)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NotePayable(ModelBase):
    __tablename__ = "notes_payable"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    note_number: Mapped[str] = mapped_column(String(50), nullable=False)
    beneficiary_name: Mapped[str | None] = mapped_column(String(200))
    bank_name: Mapped[str | None] = mapped_column(String(200))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), default="SAR")
    issue_date: Mapped[Date | None] = mapped_column(Date)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[Date | None] = mapped_column(Date)
    payment_date: Mapped[Date | None] = mapped_column(Date)
    protest_date: Mapped[Date | None] = mapped_column(Date)
    party_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    treasury_account_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    payment_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    protest_journal_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    status: Mapped[str | None] = mapped_column(String(20), default="issued")
    protest_reason: Mapped[str | None] = mapped_column(Text)
    exchange_rate: Mapped[float | None] = mapped_column(Numeric(18, 6), server_default=sa_text("1.0"))
    notes: Mapped[str | None] = mapped_column(Text)
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Expense(ModelBase):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    expense_date: Mapped[Date] = mapped_column(Date, nullable=False)
    expense_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50), default="general")
    payment_method: Mapped[str | None] = mapped_column(String(50), default="cash")
    treasury_id: Mapped[int | None] = mapped_column(ForeignKey("treasury_accounts.id"))
    expense_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    cost_center_id: Mapped[int | None] = mapped_column(Integer)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    journal_entry_id: Mapped[int | None] = mapped_column(ForeignKey("journal_entries.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("branches.id"))
    approval_status: Mapped[str | None] = mapped_column(String(20), default="pending")
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    approval_notes: Mapped[str | None] = mapped_column(Text)
    receipt_number: Mapped[str | None] = mapped_column(String(100))
    vendor_name: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ServiceRequest(ModelBase):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), default="maintenance")
    priority: Mapped[str | None] = mapped_column(String(50), default="medium")
    status: Mapped[str | None] = mapped_column(String(50), default="pending")
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id", ondelete="SET NULL"))
    asset_id: Mapped[int | None] = mapped_column(Integer)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    assigned_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    estimated_hours: Mapped[float | None] = mapped_column(Numeric(8, 2))
    actual_hours: Mapped[float | None] = mapped_column(Numeric(8, 2))
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    actual_cost: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    scheduled_date: Mapped[Date | None] = mapped_column(Date)
    completion_date: Mapped[Date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class ServiceRequestCost(ModelBase):
    __tablename__ = "service_request_costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_request_id: Mapped[int | None] = mapped_column(ForeignKey("service_requests.id", ondelete="CASCADE"))
    cost_type: Mapped[str | None] = mapped_column(String(50), default="other")
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float | None] = mapped_column(Numeric(10, 4), default=1)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    total_cost: Mapped[float | None] = mapped_column(Numeric(15, 2), default=0)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Document(ModelBase):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100), default="general")
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(Text)
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    tags: Mapped[str | None] = mapped_column(Text)
    access_level: Mapped[str | None] = mapped_column(String(50), default="company")
    related_module: Mapped[str | None] = mapped_column(String(100))
    related_id: Mapped[int | None] = mapped_column(Integer)
    current_version: Mapped[int | None] = mapped_column(Integer, default=1)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentVersion(ModelBase):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(Text)
    file_size: Mapped[int | None] = mapped_column(Integer)
    change_notes: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("company_users.id", ondelete="SET NULL"))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupportTicket(ModelBase):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_number: Mapped[str | None] = mapped_column(String(30), unique=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("parties.id"))
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_email: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str | None] = mapped_column(String(20), default="open")
    priority: Mapped[str | None] = mapped_column(String(20), default="medium")
    category: Mapped[str | None] = mapped_column(String(50))
    assigned_to: Mapped[int | None] = mapped_column(Integer)
    branch_id: Mapped[int | None] = mapped_column(Integer)
    sla_hours: Mapped[int | None] = mapped_column(Integer, default=24)
    resolution: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=sa_text("1"))


class TicketComment(ModelBase):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"))
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool | None] = mapped_column(Boolean, default=False)
    attachment_url: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


__all__ = [
    "CheckPayable",
    "CheckReceivable",
    "Document",
    "DocumentVersion",
    "Expense",
    "NotePayable",
    "NoteReceivable",
    "ServiceRequest",
    "ServiceRequestCost",
    "SupportTicket",
    "TicketComment",
]
