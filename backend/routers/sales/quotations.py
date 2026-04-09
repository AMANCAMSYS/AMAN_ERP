"""Sales quotations endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission
from .schemas import QuotationCreate

quotations_router = APIRouter()
logger = logging.getLogger(__name__)

_D2 = Decimal('0.01')


def _dec(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal('0')


@quotations_router.get("/quotations", response_model=List[dict], dependencies=[Depends(require_permission("sales.view"))])
def list_quotations(branch_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """List all sales quotations"""
    db = get_db_connection(current_user.company_id)
    try:
        query_str = """
            SELECT q.id, q.sq_number, q.quotation_date, q.expiry_date, q.total, q.status,
                   p.name as customer_name
            FROM sales_quotations q
            JOIN parties p ON q.party_id = p.id
            WHERE 1=1
        """
        params = {}
        if branch_id:
            query_str += " AND q.branch_id = :branch_id"
            params["branch_id"] = branch_id

        query_str += " ORDER BY q.created_at DESC"

        result = db.execute(text(query_str), params).fetchall()
        return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Error listing quotations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@quotations_router.get("/quotations/{id}", response_model=dict, dependencies=[Depends(require_permission("sales.view"))])
def get_quotation(id: int, current_user: dict = Depends(get_current_user)):
    """Get quotation details"""
    db = get_db_connection(current_user.company_id)
    try:
        # Get Header
        quotation = db.execute(text("""
            SELECT q.*, p.name as customer_name, p.email as customer_email, 
                   p.phone as customer_phone, p.address as customer_address, p.tax_number as customer_tax_number
            FROM sales_quotations q
            JOIN parties p ON q.party_id = p.id
            WHERE q.id = :id
        """), {"id": id}).fetchone()

        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        # Get Items
        items = db.execute(text("""
            SELECT l.*, p.product_name
            FROM sales_quotation_lines l
            LEFT JOIN products p ON l.product_id = p.id
            WHERE l.sq_id = :id
        """), {"id": id}).fetchall()

        return {
            **dict(quotation._mapping),
            "items": [dict(row._mapping) for row in items]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quotation {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@quotations_router.post("/quotations", response_model=dict, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("sales.create"))])
def create_quotation(quotation: QuotationCreate, current_user: dict = Depends(get_current_user)):
    """Create a new sales quotation"""
    db = get_db_connection(current_user.company_id)
    try:
        # Generate SQ Number (SQ-YYYY-XXXX)
        year = datetime.now().year
        last_sq = db.execute(text(
            "SELECT sq_number FROM sales_quotations WHERE sq_number LIKE :prefix ORDER BY id DESC LIMIT 1"
        ), {"prefix": f"SQ-{year}-%"}).scalar()

        if last_sq:
            last_seq = int(last_sq.split('-')[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        sq_num = f"SQ-{year}-{new_seq:04d}"

        # Calculate Totals
        subtotal = Decimal('0')
        total_tax = Decimal('0')
        total_discount = Decimal('0')
        items_to_save = []

        for item in quotation.items:
            line_subtotal = _dec(item.quantity) * _dec(item.unit_price)
            taxable = line_subtotal - _dec(item.discount)
            line_tax = taxable * (_dec(item.tax_rate) / Decimal('100'))
            line_total = (taxable + line_tax).quantize(_D2, ROUND_HALF_UP)

            subtotal += line_subtotal
            total_tax += line_tax
            total_discount += _dec(item.discount)

            items_to_save.append({
                **item.model_dump(),
                "total": line_total
            })

        grand_total = (subtotal - total_discount + total_tax).quantize(_D2, ROUND_HALF_UP)

        # Save Header
        res = db.execute(text("""
            INSERT INTO sales_quotations (
                sq_number, party_id, quotation_date, expiry_date,
                subtotal, tax_amount, discount, total, status, notes, terms_conditions, created_by, branch_id,
                currency, exchange_rate
            ) VALUES (
                :num, :cust, :qdate, :expdate,
                :sub, :tax, :disc, :total, 'draft', :notes, :terms, :user, :bid,
                :currency, :exchange_rate
            ) RETURNING id
        """), {
            "num": sq_num, "cust": quotation.customer_id, "qdate": quotation.quotation_date,
            "expdate": quotation.expiry_date, "sub": subtotal, "tax": total_tax,
            "disc": total_discount, "total": grand_total, "notes": quotation.notes,
            "terms": quotation.terms_conditions, "user": current_user.id,
            "bid": quotation.branch_id, "currency": quotation.currency,
            "exchange_rate": quotation.exchange_rate
        }).fetchone()

        sq_id = res[0]

        # Save Lines
        for line in items_to_save:
            db.execute(text("""
                INSERT INTO sales_quotation_lines (
                    sq_id, product_id, description, quantity, unit_price, tax_rate, discount, total
                ) VALUES (
                    :sq_id, :pid, :desc, :qty, :price, :tax_rate, :disc, :total
                )
            """), {
                "sq_id": sq_id, "pid": line["product_id"], "desc": line["description"],
                "qty": line["quantity"], "price": line["unit_price"], "tax_rate": line["tax_rate"],
                "disc": line["discount"], "total": line["total"]
            })

        db.commit()

        cust_name = db.execute(text("SELECT name FROM parties WHERE id = :id"), {"id": quotation.customer_id}).scalar()
        # AUDIT LOG
        log_activity(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="sales.quotation.create",
            resource_type="sales_quotation",
            resource_id=str(sq_id),
            details={"sq_number": sq_num, "total": float(grand_total), "customer_id": quotation.customer_id, "customer_name": cust_name},
            request=None
        )
        return {"id": sq_id, "sq_number": sq_num}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating Quotation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
