"""
AMAN ERP - Generic Response Schemas
Reusable response models for common API patterns.
"""
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any


# ─── Generic Responses ───────────────────────────────────────────

class MessageResponse(BaseModel):
    """Standard message response: {"message": "..."}"""
    message: str


class MessageWithIdResponse(BaseModel):
    """Message + created/updated ID"""
    message: str
    id: Optional[int] = None


class DeleteResponse(BaseModel):
    """Standard delete confirmation"""
    message: str
    deleted: bool = True


class SuccessResponse(BaseModel):
    """Generic success with optional data"""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error format"""
    detail: str


# ─── Record Responses (single row from DB) ───────────────────────

class RecordResponse(BaseModel):
    """Single DB record returned as dict - passthrough model"""
    model_config = ConfigDict(extra="allow", from_attributes=True)


class RecordWithMessageResponse(BaseModel):
    """Record data + message"""
    message: str
    model_config = ConfigDict(extra="allow")


# ─── List / Paginated Responses ──────────────────────────────────

class PaginatedResponse(BaseModel):
    """Paginated list: items + total + page info"""
    items: List[Dict[str, Any]] = []
    total: int = 0
    page: int = 1
    page_size: int = 50


class ListResponse(BaseModel):
    """Simple list wrapper"""
    items: List[Dict[str, Any]] = []
    total: int = 0


# ─── Report Responses ────────────────────────────────────────────

class ReportResponse(BaseModel):
    """Generic report with metadata"""
    report_name: Optional[str] = None
    report_name_ar: Optional[str] = None
    period: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(extra="allow")


class DashboardWidgetResponse(BaseModel):
    """Single dashboard widget"""
    key: str
    value: Any
    label_ar: Optional[str] = None
    label_en: Optional[str] = None
    icon: Optional[str] = None
    target: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Financial Responses ─────────────────────────────────────────

class JournalEntryResponse(BaseModel):
    """Journal entry creation result"""
    message: str
    journal_entry_id: Optional[int] = None
    journal_entry_number: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class InvoiceResponse(BaseModel):
    """Invoice creation/update result"""
    message: str
    invoice_id: Optional[int] = None
    invoice_number: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class PaymentResponse(BaseModel):
    """Payment/voucher creation result"""
    message: str
    payment_id: Optional[int] = None
    payment_number: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class BalanceSummaryResponse(BaseModel):
    """Account/treasury balance summary"""
    total_balance: Decimal = Decimal("0")
    currency: Optional[str] = None
    model_config = ConfigDict(extra="allow")


# ─── Import / Export Responses ───────────────────────────────────

class ImportResultResponse(BaseModel):
    """Data import result"""
    success: bool = True
    imported: int = 0
    skipped: int = 0
    errors: List[str] = []
    message: Optional[str] = None


class ExportResponse(BaseModel):
    """Export metadata (actual file returned separately)"""
    filename: str
    format: str
    rows: int = 0


# ─── Auth / Security Responses ───────────────────────────────────

class TwoFactorSetupResponse(BaseModel):
    """2FA setup result"""
    secret: Optional[str] = None
    qr_uri: Optional[str] = None
    backup_codes: Optional[List[str]] = None
    message: Optional[str] = None


class SessionListResponse(BaseModel):
    """Active sessions list"""
    sessions: List[Dict[str, Any]] = []


class AuditLogResponse(BaseModel):
    """Audit log entry"""
    logs: List[Dict[str, Any]] = []
    total: int = 0
    page: int = 1
