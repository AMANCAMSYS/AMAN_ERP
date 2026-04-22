"""
AMAN ERP - External API Router
API-001: API Key management
API-002: Webhooks CRUD + logs
ZATCA: QR code + signing endpoints
TAX-001: Withholding Tax (WHT)
"""

from fastapi import APIRouter, Depends, HTTPException
from utils.i18n import http_error
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel
import hashlib
import secrets
import json
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
from utils.audit import log_activity
from utils.zatca import (
    verify_invoice_signature,
    generate_rsa_keypair, process_invoice_for_zatca
)
from utils.webhooks import WEBHOOK_EVENTS, validate_webhook_url, encrypt_webhook_secret

router = APIRouter(prefix="/external", tags=["التكامل الخارجي"])
logger = logging.getLogger(__name__)

_D2 = Decimal('0.01')
def _dec(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal('0')


# ======================== Schemas ========================

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = []
    rate_limit_per_minute: int = 60
    expires_in_days: Optional[int] = None
    notes: Optional[str] = None

class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str]
    retry_count: int = 3
    timeout_seconds: int = 10

class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    retry_count: Optional[int] = None
    timeout_seconds: Optional[int] = None

class WHTRateCreate(BaseModel):
    name: str
    name_ar: Optional[str] = None
    rate: float
    category: str = "general"
    description: Optional[str] = None

class WHTTransactionCreate(BaseModel):
    invoice_id: Optional[int] = None
    payment_id: Optional[int] = None
    supplier_id: int
    wht_rate_id: int
    gross_amount: float


# ======================== API-001: API Keys ========================

@router.get("/api-keys", dependencies=[Depends(require_permission("admin"))])
def list_api_keys(current_user=Depends(get_current_user)):
    """List all API keys (without revealing the actual key)."""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT id, name, key_prefix, permissions, rate_limit_per_minute,
                   is_active, expires_at, last_used_at, usage_count, created_at, notes
            FROM api_keys ORDER BY created_at DESC
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/api-keys", status_code=201, dependencies=[Depends(require_permission("admin"))])
def create_api_key(data: APIKeyCreate, current_user=Depends(get_current_user)):
    """Create a new API key. The raw key is returned ONLY ONCE."""
    db = get_db_connection(current_user.company_id)
    try:
        raw_key = f"aman_{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]
        
        expires_at = None
        if data.expires_in_days:
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(days=data.expires_in_days)
        
        row = db.execute(text("""
            INSERT INTO api_keys (name, key_hash, key_prefix, permissions, rate_limit_per_minute, 
                                  created_by, expires_at, notes)
            VALUES (:name, :hash, :prefix, :perms, :rate, :user, :expires, :notes)
            RETURNING id
        """), {
            "name": data.name,
            "hash": key_hash,
            "prefix": key_prefix,
            "perms": json.dumps(data.permissions),
            "rate": data.rate_limit_per_minute,
            "user": current_user.id,
            "expires": expires_at,
            "notes": data.notes
        }).scalar()
        db.commit()
        
        log_activity(
            db=db, user_id=current_user.id, username=current_user.username,
            action="create", resource_type="api_keys",
            resource_id=str(row), details={"name": data.name, "prefix": key_prefix}
        )
        
        return {
            "id": row,
            "api_key": raw_key,
            "prefix": key_prefix,
            "message": "احفظ المفتاح الآن — لن يظهر مرة أخرى"
        }
    finally:
        db.close()


@router.delete("/api-keys/{key_id}", dependencies=[Depends(require_permission("admin"))])
def revoke_api_key(key_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("UPDATE api_keys SET is_active = FALSE WHERE id = :id"), {"id": key_id})
        db.commit()
        log_activity(
            db=db, user_id=current_user.id, username=current_user.username,
            action="revoke", resource_type="api_keys",
            resource_id=str(key_id), details={}
        )
        return {"message": "تم إلغاء المفتاح"}
    finally:
        db.close()


# ======================== API-002: Webhooks ========================

@router.get("/webhooks/events")
def list_webhook_events(current_user=Depends(get_current_user)):
    """List all available webhook events."""
    return WEBHOOK_EVENTS


@router.get("/webhooks", dependencies=[Depends(require_permission(["settings.view", "admin"]))])
def list_webhooks(current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("SELECT * FROM webhooks ORDER BY created_at DESC")).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/webhooks", status_code=201, dependencies=[Depends(require_permission(["settings.manage", "admin"]))])
def create_webhook(data: WebhookCreate, current_user=Depends(get_current_user)):
    # Validate events
    invalid = [e for e in data.events if e not in WEBHOOK_EVENTS]
    if invalid:
        raise HTTPException(400, f"أحداث غير معروفة: {invalid}")

    try:
        validate_webhook_url(data.url)
    except ValueError:
        raise HTTPException(**http_error(400, "url_not_allowed"))

    db = get_db_connection(current_user.company_id)
    try:
        auto_secret = data.secret or secrets.token_hex(32)
        encrypted_secret = encrypt_webhook_secret(auto_secret)
        row = db.execute(text("""
            INSERT INTO webhooks (name, url, secret, events, retry_count, timeout_seconds, created_by)
            VALUES (:name, :url, :secret, :events, :retry, :timeout, :user)
            RETURNING id
        """), {
            "name": data.name,
            "url": data.url,
            "secret": encrypted_secret,
            "events": json.dumps(data.events),
            "retry": data.retry_count,
            "timeout": data.timeout_seconds,
            "user": current_user.id
        }).scalar()
        db.commit()
        log_activity(
            db=db, user_id=current_user.id, username=current_user.username,
            action="create", resource_type="webhook",
            resource_id=str(row), details={"name": data.name, "url": data.url}
        )
        return {"id": row, "secret": auto_secret, "message": "تم إنشاء الـ webhook"}
    finally:
        db.close()


@router.put("/webhooks/{webhook_id}", dependencies=[Depends(require_permission(["settings.manage", "admin"]))])
def update_webhook(webhook_id: int, data: WebhookUpdate, current_user=Depends(get_current_user)):
    if data.url is not None:
        try:
            validate_webhook_url(data.url)
        except ValueError:
            raise HTTPException(**http_error(400, "url_not_allowed"))
    db = get_db_connection(current_user.company_id)
    try:
        updates = {}
        if data.name is not None: updates["name"] = data.name
        if data.url is not None: updates["url"] = data.url
        if data.events is not None: updates["events"] = json.dumps(data.events)
        if data.is_active is not None: updates["is_active"] = data.is_active
        if data.retry_count is not None: updates["retry_count"] = data.retry_count
        if data.timeout_seconds is not None: updates["timeout_seconds"] = data.timeout_seconds
        
        if not updates:
            raise HTTPException(**http_error(400, "no_data_to_update"))
        
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = webhook_id
        db.execute(text(f"UPDATE webhooks SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        log_activity(
            db=db, user_id=current_user.id, username=current_user.username,
            action="update", resource_type="webhook",
            resource_id=str(webhook_id), details={k: v for k, v in updates.items() if k != "id"}
        )
        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.delete("/webhooks/{webhook_id}", dependencies=[Depends(require_permission(["settings.manage", "admin"]))])
def delete_webhook(webhook_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM webhooks WHERE id = :id"), {"id": webhook_id})
        db.commit()
        log_activity(
            db=db, user_id=current_user.id, username=current_user.username,
            action="delete", resource_type="webhook",
            resource_id=str(webhook_id), details={}
        )
        return {"message": "تم الحذف"}
    finally:
        db.close()


@router.get("/webhooks/{webhook_id}/logs", dependencies=[Depends(require_permission(["settings.view", "admin"]))])
def get_webhook_logs(webhook_id: int, limit: int = 50, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT id, event, response_status, success, attempt, error_message, created_at
            FROM webhook_logs WHERE webhook_id = :wid ORDER BY created_at DESC LIMIT :lim
        """), {"wid": webhook_id, "lim": limit}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


# ======================== ZATCA: QR + Signing ========================

@router.post("/zatca/generate-qr", dependencies=[Depends(require_permission(["sales.view", "accounting.view"]))])
def generate_qr_code(
    invoice_id: int,
    current_user=Depends(get_current_user)
):
    """Generate ZATCA QR code for an invoice."""
    db = get_db_connection(current_user.company_id)
    try:
        # Get invoice details
        inv = db.execute(text("""
            SELECT i.id, i.invoice_number, i.invoice_date, i.total, i.tax_amount,
                   p.name as customer_name
            FROM invoices i
            LEFT JOIN parties p ON i.party_id = p.id
            WHERE i.id = :id
        """), {"id": invoice_id}).fetchone()
        
        if not inv:
            raise HTTPException(**http_error(404, "invoice_not_found"))
        
        # Get company info
        seller_name = db.execute(text(
            "SELECT setting_value FROM company_settings WHERE setting_key = 'company_name'"
        )).scalar() or "AMAN ERP"
        
        vat_number = db.execute(text(
            "SELECT setting_value FROM company_settings WHERE setting_key = 'zatca_vat_number'"
        )).scalar() or db.execute(text(
            "SELECT setting_value FROM company_settings WHERE setting_key = 'tax_number'"
        )).scalar() or "000000000000000"
        
        # Get private key for signing (optional)
        private_key = db.execute(text(
            "SELECT setting_value FROM company_settings WHERE setting_key = 'zatca_private_key'"
        )).scalar()
        
        result = process_invoice_for_zatca(
            db=db,
            invoice_id=inv.id,
            company_id=current_user.company_id,
            seller_name=seller_name,
            vat_number=vat_number,
            invoice_number=inv.invoice_number,
            invoice_date=str(inv.invoice_date),
            total=float(inv.total),
            vat_amount=float(inv.tax_amount or 0),
            private_key_pem=private_key
        )
        db.commit()
        
        return {
            "invoice_id": invoice_id,
            "invoice_number": inv.invoice_number,
            **result
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("ZATCA QR generation failed")
        raise HTTPException(500, "خطأ في توليد QR")
    finally:
        db.close()


@router.post("/zatca/generate-keypair", dependencies=[Depends(require_permission("admin"))])
def generate_keypair(current_user=Depends(get_current_user)):
    """Generate RSA keypair for ZATCA signing and store in company settings."""
    db = get_db_connection(current_user.company_id)
    try:
        private_pem, public_pem = generate_rsa_keypair()
        
        # Store in company settings
        for key, val in [("zatca_private_key", private_pem), ("zatca_public_key", public_pem)]:
            db.execute(text("""
                INSERT INTO company_settings (setting_key, setting_value, category)
                VALUES (:key, :val, 'zatca')
                ON CONFLICT (setting_key) DO UPDATE SET setting_value = :val
            """), {"key": key, "val": val})
        
        db.commit()
        return {
            "message": "تم توليد مفتاح التوقيع الرقمي",
            "public_key": public_pem
        }
    finally:
        db.close()


@router.get("/zatca/verify/{invoice_id}", dependencies=[Depends(require_permission(["sales.view", "accounting.view"]))])
def verify_invoice_qr(invoice_id: int, current_user=Depends(get_current_user)):
    """Verify a ZATCA QR code and signature for an invoice."""
    db = get_db_connection(current_user.company_id)
    try:
        inv = db.execute(text("""
            SELECT zatca_hash, zatca_signature, zatca_qr, zatca_status
            FROM invoices WHERE id = :id
        """), {"id": invoice_id}).fetchone()
        
        if not inv or not inv.zatca_hash:
            raise HTTPException(404, "لم يتم توليد بيانات ZATCA لهذه الفاتورة")
        
        result = {
            "invoice_id": invoice_id,
            "hash": inv.zatca_hash,
            "has_signature": bool(inv.zatca_signature),
            "has_qr": bool(inv.zatca_qr),
            "status": inv.zatca_status,
            "signature_valid": None
        }
        
        if inv.zatca_signature:
            public_key = db.execute(text(
                "SELECT setting_value FROM company_settings WHERE setting_key = 'zatca_public_key'"
            )).scalar()
            if public_key:
                result["signature_valid"] = verify_invoice_signature(
                    inv.zatca_hash, inv.zatca_signature, public_key
                )
        
        return result
    finally:
        db.close()


# ======================== TAX-001: Withholding Tax ========================

@router.get("/wht/rates", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def list_wht_rates(current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("SELECT * FROM wht_rates WHERE is_active = TRUE ORDER BY category, name")).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/wht/rates", status_code=201, dependencies=[Depends(require_permission(["accounting.manage", "taxes.manage"]))])
def create_wht_rate(data: WHTRateCreate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rid = db.execute(text("""
            INSERT INTO wht_rates (name, name_ar, rate, category, description)
            VALUES (:name, :name_ar, :rate, :cat, :desc) RETURNING id
        """), {
            "name": data.name, "name_ar": data.name_ar, "rate": data.rate,
            "cat": data.category, "desc": data.description
        }).scalar()
        db.commit()
        return {"id": rid}
    finally:
        db.close()


@router.post("/wht/calculate", dependencies=[Depends(require_permission(["accounting.view", "buying.view"]))])
def calculate_wht(data: WHTTransactionCreate, current_user=Depends(get_current_user)):
    """Calculate WHT amount without creating a transaction."""
    db = get_db_connection(current_user.company_id)
    try:
        rate_row = db.execute(text("SELECT rate FROM wht_rates WHERE id = :id AND is_active = TRUE"),
                              {"id": data.wht_rate_id}).fetchone()
        if not rate_row:
            raise HTTPException(**http_error(404, "wht_rate_not_found"))
        
        wht_rate = _dec(rate_row.rate)
        gross_amount = _dec(data.gross_amount)
        wht_amount = (gross_amount * wht_rate / Decimal('100')).quantize(_D2, ROUND_HALF_UP)
        net_amount = (gross_amount - wht_amount).quantize(_D2, ROUND_HALF_UP)
        
        return {
            "gross_amount": data.gross_amount,
            "wht_rate": float(wht_rate),
            "wht_amount": wht_amount,
            "net_amount": net_amount
        }
    finally:
        db.close()


@router.post("/wht/transactions", status_code=201, 
             dependencies=[Depends(require_permission(["accounting.edit", "taxes.manage"]))])
def create_wht_transaction(data: WHTTransactionCreate, current_user=Depends(get_current_user)):
    """Create a WHT transaction and optionally post GL entries."""
    db = get_db_connection(current_user.company_id)
    try:
        rate_row = db.execute(text("SELECT rate, name FROM wht_rates WHERE id = :id"),
                              {"id": data.wht_rate_id}).fetchone()
        if not rate_row:
            raise HTTPException(**http_error(404, "wht_rate_not_found"))
        
        wht_rate = _dec(rate_row.rate)
        gross_amount = _dec(data.gross_amount)
        wht_amount = (gross_amount * wht_rate / Decimal('100')).quantize(_D2, ROUND_HALF_UP)
        net_amount = (gross_amount - wht_amount).quantize(_D2, ROUND_HALF_UP)
        
        # Generate certificate number
        cert_num = f"WHT-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}"
        
        tid = db.execute(text("""
            INSERT INTO wht_transactions (
                invoice_id, payment_id, supplier_id, wht_rate_id,
                gross_amount, wht_rate, wht_amount, net_amount,
                certificate_number, period_date, created_by
            ) VALUES (
                :inv, :pay, :sup, :rate_id,
                :gross, :rate, :wht, :net,
                :cert, :period, :user
            ) RETURNING id
        """), {
            "inv": data.invoice_id, "pay": data.payment_id,
            "sup": data.supplier_id, "rate_id": data.wht_rate_id,
            "gross": gross_amount, "rate": wht_rate,
            "wht": wht_amount, "net": net_amount,
            "cert": cert_num, "period": datetime.now().date(),
            "user": current_user.id
        }).scalar()
        
        db.commit()
        
        return {
            "id": tid,
            "certificate_number": cert_num,
            "gross_amount": data.gross_amount,
            "wht_rate": wht_rate,
            "wht_amount": wht_amount,
            "net_amount": net_amount
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Error creating WHT transaction")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.get("/wht/transactions", dependencies=[Depends(require_permission(["accounting.view", "taxes.view"]))])
def list_wht_transactions(
    supplier_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT wt.*, wr.name as rate_name, p.name as supplier_name
            FROM wht_transactions wt
            LEFT JOIN wht_rates wr ON wt.wht_rate_id = wr.id
            LEFT JOIN parties p ON wt.supplier_id = p.id
            WHERE 1=1
        """
        params = {}
        if supplier_id:
            query += " AND wt.supplier_id = :sup"
            params["sup"] = supplier_id
        if from_date:
            query += " AND wt.period_date >= :from"
            params["from"] = from_date
        if to_date:
            query += " AND wt.period_date <= :to"
            params["to"] = to_date
        
        query += " ORDER BY wt.created_at DESC"
        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()
