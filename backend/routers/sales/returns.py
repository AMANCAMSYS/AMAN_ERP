"""Sales returns endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission
from utils.accounting import get_mapped_account_id
from .schemas import SalesReturnCreate

returns_router = APIRouter()
logger = logging.getLogger(__name__)


@returns_router.get("/returns", response_model=List[dict], dependencies=[Depends(require_permission("sales.view"))])
def list_sales_returns(branch_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """عرض قائمة مرتجعات المبيعات"""
    db = get_db_connection(current_user.company_id)
    try:
        query_str = """
            SELECT r.*, p.name as customer_name 
            FROM sales_returns r
            JOIN parties p ON r.party_id = p.id
            WHERE 1=1
        """
        params = {}
        if branch_id:
            query_str += " AND r.branch_id = :branch_id"
            params["branch_id"] = branch_id

        query_str += " ORDER BY r.created_at DESC"

        result = db.execute(text(query_str), params).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()


@returns_router.get("/returns/{return_id}", response_model=dict, dependencies=[Depends(require_permission("sales.view"))])
def get_sales_return(return_id: int, current_user: dict = Depends(get_current_user)):
    """جلب تفاصيل مرتجع مبيعات"""
    db = get_db_connection(current_user.company_id)
    try:
        header = db.execute(text("""
            SELECT r.*, p.name as customer_name, i.invoice_number
            FROM sales_returns r
            JOIN parties p ON r.party_id = p.id
            LEFT JOIN invoices i ON r.invoice_id = i.id
            WHERE r.id = :id
        """), {"id": return_id}).fetchone()

        if not header:
            raise HTTPException(status_code=404, detail="المرتجع غير موجود")

        lines = db.execute(text("""
            SELECT l.*, p.product_name
            FROM sales_return_lines l
            LEFT JOIN products p ON l.product_id = p.id
            WHERE l.return_id = :id
        """), {"id": return_id}).fetchall()

        return {
            **dict(header._mapping),
            "items": [dict(row._mapping) for row in lines]
        }
    finally:
        db.close()


@returns_router.post("/returns", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("sales.create"))])
def create_sales_return(request: Request, data: SalesReturnCreate, current_user: dict = Depends(get_current_user)):
    """إنشاء مرتجع مبيعات جديد (مسودة)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Generate Sequential Return Number
        from utils.accounting import generate_sequential_number
        ret_num = generate_sequential_number(db, f"RET-{datetime.now().year}", "invoices", "invoice_number")

        # Determine Branch
        branch_id = data.branch_id
        if not branch_id and data.invoice_id:
            branch_id = db.execute(text("SELECT branch_id FROM invoices WHERE id = :id"), {"id": data.invoice_id}).scalar()

        # Calculate totals
        subtotal = 0
        total_tax = 0
        lines_to_save = []

        for item in data.items:
            line_total = float(item.quantity) * float(item.unit_price)
            line_tax = float(line_total) * (float(item.tax_rate or 15.0) / 100.0)
            final_total = float(line_total) + float(line_tax)

            subtotal += float(line_total)
            total_tax += float(line_tax)

            lines_to_save.append({
                **item.model_dump(),
                "total": final_total
            })

        grand_total = subtotal + total_tax

        # Save Header
        res = db.execute(text("""
            INSERT INTO sales_returns (
                return_number, party_id, invoice_id, return_date,
                subtotal, tax_amount, total, status, notes, created_by,
                refund_method, refund_amount, bank_account_id, treasury_account_id, check_number, check_date, branch_id, warehouse_id,
                currency, exchange_rate
            ) VALUES (
                :num, :cust, :inv, :rdate,
                :sub, :tax, :total, 'draft', :notes, :user,
                :rmethod, :ramount, :rbank, :treasury, :rcheck, :rcheckdate, :bid, :wh_id,
                :currency, :exchange_rate
            ) RETURNING id
        """), {
            "num": ret_num, "cust": data.customer_id, "inv": data.invoice_id,
            "rdate": data.return_date, "sub": subtotal, "tax": total_tax,
            "total": grand_total, "notes": data.notes, "user": current_user.id,
            "rmethod": data.refund_method, "ramount": data.refund_amount,
            "rbank": data.bank_account_id, "treasury": data.bank_account_id,
            "rcheck": data.check_number,
            "rcheckdate": data.check_date, "bid": branch_id, "wh_id": data.warehouse_id,
            "currency": data.currency, "exchange_rate": data.exchange_rate
        }).fetchone()

        ret_id = res[0]

        # Save Lines
        for line in lines_to_save:
            db.execute(text("""
                INSERT INTO sales_return_lines (
                    return_id, product_id, description, quantity, unit_price, tax_rate, total, reason
                ) VALUES (
                    :ret_id, :pid, :desc, :qty, :price, :tax_rate, :total, :reason
                )
            """), {
                "ret_id": ret_id, "pid": line["product_id"], "desc": line["description"],
                "qty": line["quantity"], "price": line["unit_price"], "tax_rate": line["tax_rate"],
                "total": line["total"], "reason": line["reason"]
            })

        db.commit()

        cust_name = db.execute(text("SELECT name FROM parties WHERE id = :id"), {"id": data.customer_id}).scalar()
        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="sales.return.create",
            resource_type="sales_return",
            resource_id=str(ret_id),
            details={"return_number": ret_num, "total": grand_total, "customer_id": data.customer_id, "customer_name": cust_name},
            request=request,
            branch_id=data.branch_id
        )
        return {"id": ret_id, "return_number": ret_num}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@returns_router.post("/returns/{return_id}/approve", dependencies=[Depends(require_permission("sales.create"))])
def approve_sales_return(return_id: int, current_user: dict = Depends(get_current_user)):
    """اعتماد مرتجع المبيعات (تحديث المخزون وقيد محاسبي)"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get base currency
        base_currency_row = db.execute(text("SELECT code FROM currencies WHERE is_base = TRUE LIMIT 1")).fetchone()
        if not base_currency_row:
            base_currency_row = db.execute(text("SELECT setting_value as code FROM company_settings WHERE setting_key = 'default_currency'")).fetchone()
        base_currency = base_currency_row[0] if base_currency_row else "SAR"

        # 1. Fetch Return details
        header = db.execute(text("SELECT * FROM sales_returns WHERE id = :id"), {"id": return_id}).fetchone()
        if not header or header.status != 'draft':
            raise HTTPException(status_code=400, detail="المرتجع غير موجود أو تم اعتماده مسبقاً")

        lines = db.execute(text("SELECT * FROM sales_return_lines WHERE return_id = :id"), {"id": return_id}).fetchall()

        # 2. Update Stock
        # Determine warehouse: Use returned warehouse (header.warehouse_id) OR original invoice's warehouse if possible
        wh_id = header.warehouse_id

        if not wh_id and header.invoice_id:
            # Try to fetch warehouse from original invoice transactions
            orig_wh = db.execute(text("""
                SELECT warehouse_id FROM inventory_transactions 
                WHERE reference_id = :id AND reference_type = 'invoice' 
                LIMIT 1
            """), {"id": header.invoice_id}).scalar()
            if orig_wh:
                wh_id = orig_wh

        if not wh_id:
            # Fallback to default warehouse
            wh_id = db.execute(text("SELECT id FROM warehouses WHERE is_default = TRUE")).scalar() or 1

        total_cost_reversal = 0
        for line in lines:
            if line.product_id:
                # Calculate cost to reverse from COGS FIRST (before logging transaction)
                cost_price = 0
                if header.invoice_id:
                    historical_cost = db.execute(text("""
                        SELECT unit_cost FROM inventory_transactions 
                        WHERE product_id = :pid 
                          AND reference_id = :inv_id 
                          AND quantity < 0 
                        LIMIT 1
                    """), {"pid": line.product_id, "inv_id": header.invoice_id}).scalar()

                    if historical_cost is not None:
                         cost_price = float(historical_cost)

                # Fallback to current product cost if historical not found
                if cost_price == 0:
                     cost_price = db.execute(text("SELECT cost_price FROM products WHERE id = :id"), {"id": line.product_id}).scalar() or 0
                     cost_price = float(cost_price)

                # Update Inventory
                db.execute(text("""
                    UPDATE inventory SET quantity = quantity + :qty 
                    WHERE product_id = :pid AND warehouse_id = :wh
                """), {"qty": line.quantity, "pid": line.product_id, "wh": wh_id})

                # Log Inventory Transaction
                db.execute(text("""
                    INSERT INTO inventory_transactions (
                        product_id, warehouse_id, transaction_type, 
                        reference_type, reference_id, reference_document,
                        quantity, unit_cost, total_cost, created_by
                    ) VALUES (
                        :pid, :wh, 'sales_return', 'sales_return', :ret_id, :doc_num,
                        :qty, :cost, :total_cost, :user
                    )
                """), {
                    "pid": line.product_id,
                    "wh": wh_id,
                    "ret_id": return_id,
                    "doc_num": header.return_number,
                    "qty": line.quantity,
                    "cost": cost_price,
                    "total_cost": float(cost_price) * float(line.quantity),
                    "user": current_user.id if not isinstance(current_user, dict) else current_user.get("id")
                })

                total_cost_reversal += (float(cost_price) * float(line.quantity))

        # 3. Update Status
        db.execute(text("UPDATE sales_returns SET status = 'approved' WHERE id = :id"), {"id": return_id})

        exchange_rate = float(header.exchange_rate or 1.0)
        def to_base(amount):
            return round(float(amount) * exchange_rate, 2)

        # 4. Update Customer Balance (Reduction in Base AND Currency)
        gl_total = to_base(header.total)
        db.execute(text("""
            UPDATE parties SET current_balance = current_balance - :total 
            WHERE id = :id
        """), {"total": gl_total, "id": header.party_id})

        # Also update balance_currency for foreign currency returns
        if header.currency and header.currency != base_currency:
            db.execute(text("""
                UPDATE parties SET balance_currency = COALESCE(balance_currency, 0) - :amt
                WHERE id = :id
            """), {"amt": float(header.total), "id": header.party_id})

        # 4.5 Update Original Invoice Status (Treat return as payment/settlement)
        if header.invoice_id:
            db.execute(text("""
                UPDATE invoices 
                SET paid_amount = COALESCE(paid_amount, 0) + :return_val,
                    status = CASE 
                        WHEN (COALESCE(paid_amount, 0) + :return_val) >= total THEN 'paid'
                        WHEN (COALESCE(paid_amount, 0) + :return_val) > 0 THEN 'partial'
                        ELSE status
                    END
                WHERE id = :inv_id
            """), {"return_val": header.total, "inv_id": header.invoice_id})

        # 5. GL Entry (Automated using Dynamic Mappings)
        acc_sales = get_mapped_account_id(db, "acc_map_sales_rev")
        acc_vat_out = get_mapped_account_id(db, "acc_map_vat_out")
        acc_ar = get_mapped_account_id(db, "acc_map_ar")
        acc_cash = get_mapped_account_id(db, "acc_map_cash_main")
        acc_bank = get_mapped_account_id(db, "acc_map_bank")
        acc_cogs = get_mapped_account_id(db, "acc_map_cogs")
        acc_inventory = get_mapped_account_id(db, "acc_map_inventory")

        je_lines = []
        gl_subtotal = to_base(header.subtotal)
        gl_tax = to_base(header.tax_amount)

        # Debit: Sales Return (Revenue reduction)
        je_lines.append({"account_id": acc_sales, "debit": gl_subtotal, "credit": 0, "description": f"Sales Return - {header.return_number} ({header.currency})"})
        # Debit: VAT Output (Tax reduction)
        if gl_tax > 0:
            je_lines.append({"account_id": acc_vat_out, "debit": gl_tax, "credit": 0, "description": f"VAT Reduction - {header.return_number}"})
        # Credit: Accounts Receivable (Customer reduction)
        je_lines.append({"account_id": acc_ar, "debit": 0, "credit": gl_total, "description": f"AR Reduction - {header.return_number}"})

        # 6. Refund Processing (Payment Voucher + GL)
        if header.refund_method and header.refund_method != 'credit' and header.refund_amount > 0:
            from utils.accounting import generate_sequential_number
            voucher_num = generate_sequential_number(db, f"REF-{datetime.now().year}", "payment_vouchers", "voucher_number")

            # A. Create Payment Voucher
            voucher_id = db.execute(text("""
                INSERT INTO payment_vouchers (
                    voucher_number, voucher_type, voucher_date, party_type, party_id,
                    amount, payment_method, bank_account_id, treasury_account_id, check_number, check_date,
                    reference, status, created_by
                ) VALUES (
                    :vnum, 'payment', :vdate, 'customer', :cust,
                    :amt, :method, :bank, :treasury, :check_num, :check_date,
                    :ref, 'posted', :user
                ) RETURNING id
            """), {
                "vnum": voucher_num, "vdate": header.return_date, "cust": header.party_id,
                "amt": header.refund_amount, "method": header.refund_method,
                "bank": header.bank_account_id, "treasury": header.treasury_account_id or header.bank_account_id,
                "check_num": header.check_number,
                "check_date": header.check_date,
                "ref": f"Refund for {header.return_number}", "user": current_user.id
            }).scalar()

            # C. Update Customer Balance
            gl_refund = to_base(header.refund_amount)
            db.execute(text("""
                UPDATE parties SET current_balance = current_balance + :amt
                WHERE id = :id
            """), {"amt": gl_refund, "id": header.party_id})

            # GL for Refund
            acc_cash = get_mapped_account_id(db, "acc_map_cash_main")
            acc_bank = get_mapped_account_id(db, "acc_map_bank")

            credit_acc = acc_bank if header.refund_method == 'bank' else acc_cash

            if credit_acc:
                # Credit Cash/Bank
                je_lines.append({"account_id": credit_acc, "debit": 0, "credit": gl_refund, "description": f"Refund Paid - {header.return_number} ({header.currency})"})
                # Debit AR
                je_lines.append({"account_id": acc_ar, "debit": gl_refund, "credit": 0, "description": f"AR Offset (Refund) - {header.return_number}"})

            # Update Treasury Balance for refund
            if hasattr(header, 'treasury_id') and header.treasury_id:
                treas_info = db.execute(text("""
                    SELECT ta.currency as currency_code
                    FROM treasury_accounts ta
                    WHERE ta.id = :id
                """), {"id": header.treasury_id}).fetchone()

                if treas_info and treas_info.currency_code and treas_info.currency_code != base_currency:
                    treas_refund = header.refund_amount  # FC amount
                else:
                    treas_refund = gl_refund  # SAR amount

                db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance - :amt WHERE id = :id"),
                           {"amt": treas_refund, "id": header.treasury_id})
        # Inventory Reversal
        if total_cost_reversal > 0:
            je_lines.append({"account_id": acc_inventory, "debit": total_cost_reversal, "credit": 0, "description": f"Inv Increase - {header.return_number}"})
            je_lines.append({"account_id": acc_cogs, "debit": 0, "credit": total_cost_reversal, "description": f"COGS Reduction - {header.return_number}"})

        # Insert Journal Entry
        je_num = f"JE-RET-{header.return_number}"
        je_id = db.execute(text("""
            INSERT INTO journal_entries (
                entry_number, entry_date, description, reference, status, 
                created_by, branch_id, currency, exchange_rate
            )
            VALUES (:num, :date, :desc, :ref, 'posted', :user, :bid, :curr, :rate) RETURNING id
        """), {
            "num": je_num, "date": header.return_date, "desc": f"Sales Return {header.return_number} ({header.currency})",
            "ref": header.return_number, "user": current_user.id, "bid": header.branch_id,
            "curr": header.currency, "rate": exchange_rate
        }).scalar()

        from utils.accounting import update_account_balance as uab_return
        for line in je_lines:
            if line["account_id"]:
                amt_curr = round((line["debit"] + line["credit"]) / exchange_rate, 2) if exchange_rate else 0
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
                    "amt_curr": amt_curr,
                    "curr": header.currency
                })

                # Update balance using proper utility (handles base + currency)
                uab_return(
                    db,
                    account_id=line["account_id"],
                    debit_base=line["debit"],
                    credit_base=line["credit"],
                    debit_curr=amt_curr if line["debit"] > 0 else 0,
                    credit_curr=amt_curr if line["credit"] > 0 else 0,
                    currency=header.currency
                )

        db.commit()

        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="sales.return.approve",
            resource_type="sales_return",
            resource_id=str(return_id),
            details={"return_number": header.return_number, "total": float(header.total), "info": "Return Approved"},
            branch_id=header.branch_id
        )

        return {"status": "approved", "message": "تم اعتماد المرتجع بنجاح وتحديث المخزون والقيود المحاسبية"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving return: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
