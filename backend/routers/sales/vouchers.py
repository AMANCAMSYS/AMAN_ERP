"""Customer receipts and payments (vouchers) endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from utils.i18n import http_error
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
from utils.cache import invalidate_company_cache

from database import get_db_connection
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission
from utils.accounting import get_mapped_account_id
from .schemas import CustomerReceiptCreate, CustomerPaymentCreate

vouchers_router = APIRouter()
logger = logging.getLogger(__name__)

_D2 = Decimal("0.01")
def _dec(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal("0")
# --- Customer Receipts (Payment Vouchers) ---

@vouchers_router.post("/receipts", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("sales.create"))])
def create_customer_receipt(request: Request, data: CustomerReceiptCreate, current_user: dict = Depends(get_current_user)):
    """إنشاء سند قبض من عميل"""
    db = get_db_connection(current_user.company_id)
    try:
        from utils.accounting import generate_sequential_number, get_base_currency
        base_currency = get_base_currency(db)
        voucher_num = generate_sequential_number(db, f"RCV-{datetime.now().year}", "payment_vouchers", "voucher_number")

        # SLS-011: Prevent posting receipts to closed fiscal periods
        from utils.accounting import check_fiscal_period_open
        check_fiscal_period_open(db, data.voucher_date)

        # Currency & Exchange Rate
        currency = data.currency or base_currency
        exchange_rate = _dec(data.exchange_rate or 1)
        if exchange_rate <= 0:
            raise HTTPException(**http_error(400, "exchange_rate_must_be_positive"))
        amount_base = (_dec(data.amount) * exchange_rate).quantize(_D2, ROUND_HALF_UP)

        # 1. Insert Voucher Header
        result = db.execute(text("""
            INSERT INTO payment_vouchers (
                voucher_number, voucher_type, voucher_date, party_type, party_id,
                amount, payment_method, bank_account_id, treasury_account_id, check_number, check_date,
                reference, notes, status, created_by, branch_id,
                currency, exchange_rate
            ) VALUES (
                :vnum, 'receipt', :vdate, 'customer', :cust,
                :amt, :method, :bank, :treasury, :check_num, :check_date,
                :ref, :notes, 'posted', :user, :bid,
                :curr, :rate
            ) RETURNING id
        """), {
            "vnum": voucher_num, "vdate": data.voucher_date, "cust": data.customer_id,
            "amt": data.amount, "method": data.payment_method, "bank": data.bank_account_id,
            "treasury": getattr(data, 'treasury_id', None) or data.bank_account_id,
            "check_num": data.check_number, "check_date": data.check_date,
            "ref": data.reference, "notes": data.notes, "user": current_user.id,
            "bid": data.branch_id,
            "curr": currency, "rate": exchange_rate
        }).fetchone()

        voucher_id = result[0]

        # 2. Process Allocations
        total_allocated = Decimal("0")
        for alloc in data.allocations:
            alloc_amt = _dec(alloc.allocated_amount).quantize(_D2, ROUND_HALF_UP)
            if alloc_amt <= 0:
                raise HTTPException(status_code=400, detail="مبلغ التخصيص يجب أن يكون أكبر من صفر")

            # Lock invoice row to prevent concurrent over-allocation
            inv_info = db.execute(text("""
                SELECT party_id, total, COALESCE(paid_amount, 0) AS paid_amount
                FROM invoices
                WHERE id = :iid
                FOR UPDATE
            """), {"iid": alloc.invoice_id}).fetchone()
            if not inv_info:
                raise HTTPException(status_code=404, detail=f"الفاتورة {alloc.invoice_id} غير موجودة")
            if int(inv_info.party_id) != int(data.customer_id):
                raise HTTPException(status_code=400, detail=f"الفاتورة {alloc.invoice_id} لا تتبع العميل المحدد")

            remaining = (_dec(inv_info.total) - _dec(inv_info.paid_amount)).quantize(_D2, ROUND_HALF_UP)
            if alloc_amt > remaining + _D2:
                raise HTTPException(status_code=400, detail=f"مبلغ التخصيص ({alloc_amt:.2f}) يتجاوز المتبقي على الفاتورة ({remaining:.2f})")

            total_allocated = (total_allocated + alloc_amt).quantize(_D2, ROUND_HALF_UP)

            # Insert allocation record
            db.execute(text("""
                INSERT INTO payment_allocations (voucher_id, invoice_id, allocated_amount)
                VALUES (:vid, :iid, :amt)
            """), {"vid": voucher_id, "iid": alloc.invoice_id, "amt": alloc_amt})

            # Update invoice paid_amount and status
            db.execute(text("""
                UPDATE invoices
                SET paid_amount = COALESCE(paid_amount, 0) + :amt,
                    status = CASE
                        WHEN (COALESCE(paid_amount, 0) + :amt) >= total THEN 'paid'
                        WHEN (COALESCE(paid_amount, 0) + :amt) > 0 THEN 'partial'
                        ELSE status
                    END
                WHERE id = :iid
            """), {"amt": alloc_amt, "iid": alloc.invoice_id})

        if total_allocated > (_dec(data.amount) + _D2):
            raise HTTPException(**http_error(400, "allocations_exceed_voucher_amount"))

        # 3. Update Customer Balance (reduce receivables in Base Currency)
        db.execute(text("""
            UPDATE parties
            SET current_balance = current_balance - :amt
            WHERE id = :cid
        """), {"amt": amount_base, "cid": data.customer_id})

        # Also update balance_currency for FC receipts
        if currency and currency != base_currency:
            db.execute(text("""
                UPDATE parties
                SET balance_currency = COALESCE(balance_currency, 0) - :amt
                WHERE id = :cid
            """), {"amt": data.amount, "cid": data.customer_id})

        # 4. Create GL Entry
        acc_ar = get_mapped_account_id(db, "acc_map_ar")
        acc_cash = get_mapped_account_id(db, "acc_map_cash_main")
        acc_bank = get_mapped_account_id(db, "acc_map_bank")

        je_num = f"JE-RCV-{voucher_num}"
        je_id = db.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, description, reference, status, 
                created_by, branch_id, currency, exchange_rate
            )
            VALUES (
                :num, :date, :desc, :ref, 'posted', 
                :user, :bid, :curr, :rate
            ) RETURNING id
        """), {
            "num": je_num, "date": data.voucher_date,
            "desc": f"Customer Receipt {voucher_num} ({currency})",
            "ref": voucher_num, "user": current_user.id,
            "bid": data.branch_id,
            "curr": currency, "rate": exchange_rate
        }).scalar()

        je_lines = []
        # Debit: Cash/Bank
        if data.payment_method == "cash":
            je_lines.append({"account_id": acc_cash, "debit": amount_base, "credit": 0, "description": f"Cash Receipt - {voucher_num}"})
        elif data.payment_method in ["bank", "check"]:
            je_lines.append({"account_id": acc_bank, "debit": amount_base, "credit": 0, "description": f"Bank Receipt - {voucher_num}"})

        # Credit: AR
        je_lines.append({"account_id": acc_ar, "debit": 0, "credit": amount_base, "description": f"AR Collection - {voucher_num}"})

        for line in je_lines:
            if line["account_id"]:
                db.execute(text("""
                    INSERT INTO journal_lines (
                        journal_entry_id, account_id, debit, credit, description,
                        amount_currency, currency
                    )
                    VALUES (:jid, :aid, :deb, :cred, :desc, :amt_curr, :curr)
                """), {
                    "jid": je_id,
                    "aid": line["account_id"],
                    "deb": line["debit"],
                    "cred": line["credit"],
                    "desc": line["description"],
                    "amt_curr": data.amount,
                    "curr": currency
                })

                # Update account balance (base + currency)
                from utils.accounting import update_account_balance as uab_receipt
                uab_receipt(
                    db,
                    account_id=line["account_id"],
                    debit_base=line["debit"],
                    credit_base=line["credit"],
                    debit_curr=_dec(data.amount) if line["debit"] > 0 else 0,
                    credit_curr=_dec(data.amount) if line["credit"] > 0 else 0,
                    currency=currency
                )

        # 5. Update Treasury Balance
        if hasattr(data, 'treasury_id') and data.treasury_id:
            # Get treasury currency to determine what amount to add
            treas_info = db.execute(text("""
                SELECT ta.currency as currency_code
                FROM treasury_accounts ta
                WHERE ta.id = :id
            """), {"id": data.treasury_id}).fetchone()

            if treas_info and treas_info.currency_code and treas_info.currency_code != base_currency:
                # FC treasury: add in foreign currency
                treas_amount = _dec(data.amount)
            else:
                # SAR treasury: add in base currency
                treas_amount = amount_base

            db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance + :amt WHERE id = :id"),
                       {"amt": treas_amount, "id": data.treasury_id})

        db.commit()
        invalidate_company_cache(str(current_user.company_id))
        

        cust_name = db.execute(text("SELECT name FROM parties WHERE id = :id"), {"id": data.customer_id}).scalar()
        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="sales.receipt.create",
            resource_type="payment_voucher",
            resource_id=str(voucher_id),
            details={"voucher_number": voucher_num, "amount": data.amount, "customer_id": data.customer_id, "customer_name": cust_name},
            request=request,
            branch_id=data.branch_id
        )

        # Notify finance team
        try:
            db.execute(text("""
                INSERT INTO notifications (user_id, type, title, message, link, is_read, created_at)
                SELECT DISTINCT u.id, 'payment_received', :title, :message, :link, FALSE, NOW()
                FROM company_users u
                WHERE u.is_active = TRUE AND u.role IN ('admin', 'superuser')
                AND u.id != :current_uid
            """), {
                "title": "💵 تم تحصيل دفعة من عميل",
                "message": f"تم تحصيل {data.amount:,.2f} من العميل {cust_name or ''} — سند {voucher_num}",
                "link": f"/sales/receipts/{voucher_id}",
                "current_uid": current_user.id
            })
            db.commit()
        except Exception:
            pass

        return {"id": voucher_id, "voucher_number": voucher_num}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating receipt: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@vouchers_router.post("/payments", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("sales.create"))])
def create_customer_payment(request: Request, data: CustomerPaymentCreate, current_user: dict = Depends(get_current_user)):
    """إنشاء سند صرف لعميل (رد مبلغ)"""
    db = get_db_connection(current_user.company_id)
    try:
        from utils.accounting import generate_sequential_number, get_base_currency
        base_currency = get_base_currency(db)
        voucher_num = generate_sequential_number(db, f"PAY-{datetime.now().year}", "payment_vouchers", "voucher_number")

        # SLS-011: Prevent posting payments to closed fiscal periods
        from utils.accounting import check_fiscal_period_open
        check_fiscal_period_open(db, data.voucher_date)

        # Currency & Exchange Rate
        currency = data.currency or base_currency
        exchange_rate = _dec(data.exchange_rate or 1)
        if exchange_rate <= 0:
            raise HTTPException(**http_error(400, "exchange_rate_must_be_positive"))
        amount_base = (_dec(data.amount) * exchange_rate).quantize(_D2, ROUND_HALF_UP)

        # 1. Insert Voucher Header
        result = db.execute(text("""
            INSERT INTO payment_vouchers (
                voucher_number, voucher_type, voucher_date, party_type, party_id,
                amount, payment_method, bank_account_id, treasury_account_id, check_number, check_date,
                reference, notes, status, created_by, branch_id,
                currency, exchange_rate
            ) VALUES (
                :vnum, 'payment', :vdate, 'customer', :cust,
                :amt, :method, :bank, :treasury, :check_num, :check_date,
                :ref, :notes, 'posted', :user, :bid,
                :curr, :rate
            ) RETURNING id
        """), {
            "vnum": voucher_num, "vdate": data.voucher_date, "cust": data.customer_id,
            "amt": data.amount, "method": data.payment_method, "bank": data.bank_account_id,
            "treasury": getattr(data, 'treasury_id', None) or data.bank_account_id,
            "check_num": data.check_number, "check_date": data.check_date,
            "ref": data.reference, "notes": data.notes, "user": current_user.id,
            "bid": data.branch_id,
            "curr": currency, "rate": exchange_rate
        }).fetchone()

        voucher_id = result[0]

        # 1.5 Process Allocations (if any)
        total_allocated = Decimal("0")
        for alloc in data.allocations:
            alloc_amt = _dec(alloc.allocated_amount).quantize(_D2, ROUND_HALF_UP)
            if alloc_amt <= 0:
                raise HTTPException(status_code=400, detail="مبلغ التخصيص يجب أن يكون أكبر من صفر")

            inv_info = db.execute(text("""
                SELECT party_id, total, COALESCE(paid_amount, 0) AS paid_amount
                FROM invoices
                WHERE id = :iid
                FOR UPDATE
            """), {"iid": alloc.invoice_id}).fetchone()
            if not inv_info:
                raise HTTPException(status_code=404, detail=f"الفاتورة {alloc.invoice_id} غير موجودة")
            if int(inv_info.party_id) != int(data.customer_id):
                raise HTTPException(status_code=400, detail=f"الفاتورة {alloc.invoice_id} لا تتبع العميل المحدد")

            remaining = (_dec(inv_info.total) - _dec(inv_info.paid_amount)).quantize(_D2, ROUND_HALF_UP)
            if alloc_amt > remaining + _D2:
                raise HTTPException(status_code=400, detail=f"مبلغ التخصيص ({alloc_amt:.2f}) يتجاوز المتبقي على الفاتورة ({remaining:.2f})")

            total_allocated = (total_allocated + alloc_amt).quantize(_D2, ROUND_HALF_UP)

            db.execute(text("""
                INSERT INTO payment_allocations (voucher_id, invoice_id, allocated_amount)
                VALUES (:vid, :iid, :amt)
            """), {"vid": voucher_id, "iid": alloc.invoice_id, "amt": alloc_amt})

            # Update invoice paid_amount
            db.execute(text("""
                UPDATE invoices
                SET paid_amount = COALESCE(paid_amount, 0) + :amt
                WHERE id = :iid
            """), {"amt": alloc_amt, "iid": alloc.invoice_id})

            # Update status
            db.execute(text("""
                UPDATE invoices
                SET status = CASE 
                    WHEN (total - COALESCE(paid_amount, 0)) <= 0.01 THEN 'paid'
                    ELSE 'partial'
                END
                WHERE id = :iid
            """), {"iid": alloc.invoice_id})

        if total_allocated > (_dec(data.amount) + _D2):
            raise HTTPException(**http_error(400, "allocations_exceed_voucher_amount"))

        # 2. Update Customer Balance (increase because we're paying them)
        db.execute(text("""
            UPDATE parties
            SET current_balance = current_balance + :amt
            WHERE id = :cid
        """), {"amt": amount_base, "cid": data.customer_id})

        # Also update balance_currency for FC payments
        if currency and currency != base_currency:
            db.execute(text("""
                UPDATE parties
                SET balance_currency = COALESCE(balance_currency, 0) + :amt
                WHERE id = :cid
            """), {"amt": data.amount, "cid": data.customer_id})

        # 3. Create GL Entry
        from utils.accounting import get_mapped_account_id, validate_je_lines
        acc_ar = get_mapped_account_id(db, "acc_map_ar")
        acc_cash = get_mapped_account_id(db, "acc_map_cash")
        acc_bank = get_mapped_account_id(db, "acc_map_bank") or get_mapped_account_id(db, "acc_map_cash")

        je_num = f"JE-PAY-{voucher_num}"
        je_id = db.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, description, reference, status, 
                created_by, branch_id, currency, exchange_rate
            )
            VALUES (
                :num, :date, :desc, :ref, 'posted', 
                :user, :bid, :curr, :rate
            ) RETURNING id
        """), {
            "num": je_num, "date": data.voucher_date,
            "desc": f"Customer Payment {voucher_num} ({currency})",
            "ref": voucher_num, "user": current_user.id,
            "bid": data.branch_id,
            "curr": currency, "rate": exchange_rate
        }).scalar()

        je_lines = []
        # Debit: AR (reduce customer credit)
        je_lines.append({"account_id": acc_ar, "debit": amount_base, "credit": 0, "description": f"AR Payment - {voucher_num}"})

        # Credit: Cash/Bank (money out)
        if data.payment_method == "cash":
            je_lines.append({"account_id": acc_cash, "debit": 0, "credit": amount_base, "description": f"Cash Payment - {voucher_num}"})
        elif data.payment_method in ["bank", "check"]:
            je_lines.append({"account_id": acc_bank, "debit": 0, "credit": amount_base, "description": f"Bank Payment - {voucher_num}"})

        # Validate before insert
        valid_lines = validate_je_lines(je_lines, source=f"REFUND-{voucher_num}")

        for line in valid_lines:
            db.execute(text("""
                INSERT INTO journal_lines (
                    journal_entry_id, account_id, debit, credit, description,
                    amount_currency, currency
                )
                VALUES (:jid, :aid, :deb, :cred, :desc, :amt_curr, :curr)
            """), {
                "jid": je_id,
                "aid": line["account_id"],
                "deb": line["debit"],
                "cred": line["credit"],
                "desc": line["description"],
                "amt_curr": data.amount,
                "curr": currency
            })

            # Update account balance (base + currency)
            from utils.accounting import update_account_balance as uab_payment
            uab_payment(
                db,
                account_id=line["account_id"],
                debit_base=line["debit"],
                credit_base=line["credit"],
                    debit_curr=_dec(data.amount) if line["debit"] > 0 else 0,
                    credit_curr=_dec(data.amount) if line["credit"] > 0 else 0,
                currency=currency
            )

        db.commit()
        invalidate_company_cache(str(current_user.company_id))
        

        cust_name = db.execute(text("SELECT name FROM parties WHERE id = :id"), {"id": data.customer_id}).scalar()
        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="sales.payment.create",
            resource_type="payment_voucher",
            resource_id=str(voucher_id),
            details={"voucher_number": voucher_num, "amount": data.amount, "customer_id": data.customer_id, "customer_name": cust_name},
            request=request,
            branch_id=data.branch_id
        )
        return {"id": voucher_id, "voucher_number": voucher_num}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating receipt: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@vouchers_router.get("/receipts", response_model=List[dict], dependencies=[Depends(require_permission("sales.view"))])
def list_customer_receipts(branch_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """قائمة سندات القبض"""
    from utils.permissions import validate_branch_access
    branch_id = validate_branch_access(current_user, branch_id)

    db = get_db_connection(current_user.company_id)
    try:
        query_str = """
            SELECT pv.id, pv.voucher_number, pv.voucher_date, pv.amount,
                   pv.payment_method, pv.status, p.name as customer_name
            FROM payment_vouchers pv
            JOIN parties p ON pv.party_id = p.id
            WHERE pv.voucher_type = 'receipt' AND pv.party_type = 'customer'
        """
        params = {}
        if branch_id:
            query_str += " AND pv.branch_id = :branch_id"
            params["branch_id"] = branch_id

        query_str += " ORDER BY pv.created_at DESC"

        result = db.execute(text(query_str), params).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Error listing receipts: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@vouchers_router.get("/payments", response_model=List[dict], dependencies=[Depends(require_permission("sales.view"))])
def list_customer_payments(branch_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """قائمة سندات الصرف (العملاء)"""
    from utils.permissions import validate_branch_access
    branch_id = validate_branch_access(current_user, branch_id)

    db = get_db_connection(current_user.company_id)
    try:
        query_str = """
            SELECT pv.id, pv.voucher_number, pv.voucher_date, pv.amount,
                   pv.payment_method, pv.status, p.name as customer_name
            FROM payment_vouchers pv
            JOIN parties p ON pv.party_id = p.id
            WHERE pv.voucher_type = 'payment' AND pv.party_type = 'customer'
        """
        params = {}
        if branch_id:
            query_str += " AND pv.branch_id = :branch_id"
            params["branch_id"] = branch_id

        query_str += " ORDER BY pv.created_at DESC"

        result = db.execute(text(query_str), params).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@vouchers_router.get("/payments/{voucher_id}", response_model=dict, dependencies=[Depends(require_permission("sales.view"))])
def get_payment_details(voucher_id: int, current_user: dict = Depends(get_current_user)):
    """تفاصيل سند صرف"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get Header
        header = db.execute(text("""
            SELECT pv.*, p.name as customer_name, p.email as customer_email, p.phone as customer_phone
            FROM payment_vouchers pv
            JOIN parties p ON pv.party_id = p.id
            WHERE pv.id = :id AND pv.voucher_type = 'payment'
        """), {"id": voucher_id}).fetchone()

        if not header:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Enforce branch access for single resource
        from utils.permissions import validate_branch_access
        if header.branch_id:
            validate_branch_access(current_user, header.branch_id)

        return dict(header._mapping)
    except Exception as e:
        logger.error(f"Error getting payment details: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
@vouchers_router.get("/receipts/{voucher_id}", response_model=dict, dependencies=[Depends(require_permission("sales.view"))])
def get_receipt_details(voucher_id: int, current_user: dict = Depends(get_current_user)):
    """تفاصيل سند قبض"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get Header
        header = db.execute(text("""
            SELECT pv.*, p.name as customer_name, p.email as customer_email, p.phone as customer_phone
            FROM payment_vouchers pv
            JOIN parties p ON pv.party_id = p.id
            WHERE pv.id = :id AND pv.voucher_type = 'receipt'
        """), {"id": voucher_id}).fetchone()

        if not header:
            raise HTTPException(status_code=404, detail="Receipt not found")

        # Enforce branch access for single resource
        from utils.permissions import validate_branch_access
        if header.branch_id:
            validate_branch_access(current_user, header.branch_id)

        # Get Allocations
        allocations = db.execute(text("""
            SELECT pa.*, i.invoice_number
            FROM payment_allocations pa
            JOIN invoices i ON pa.invoice_id = i.id
            WHERE pa.voucher_id = :id
        """), {"id": voucher_id}).fetchall()

        return {
            **dict(header._mapping),
            "allocations": [dict(a._mapping) for a in allocations]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting receipt: {str(e)}")
        logger.exception("Internal error")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()
