
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission, validate_branch_access

router = APIRouter(prefix="/reports", tags=["التقارير"])

# --- Schemas ---
class TrialBalanceItem(BaseModel):
    account_id: int
    account_number: str
    name: str
    name_en: Optional[str]
    account_type: str
    opening_debit: float
    opening_credit: float
    period_debit: float
    period_credit: float
    closing_debit: float
    closing_credit: float

class TrialBalanceResponse(BaseModel):
    period: Dict[str, date]
    data: List[TrialBalanceItem]
    totals: Dict[str, float]

class FinancialStatementItem(BaseModel):
    id: int
    account_number: str
    name: str
    name_en: Optional[str] = None
    account_type: str
    balance: float
    level: int = 0
    parent_id: Optional[int] = None
    children: List['FinancialStatementItem'] = []

class FinancialStatementResponse(BaseModel):
    period: Dict[str, date]
    data: List[FinancialStatementItem]
    total: float

@router.get("/sales/summary", response_model=Dict[str, Any], dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def get_sales_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """ملخص المبيعات (إجمالي، عدد الفواتير، الأرباح التقريبية)"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
            
        params = {"start": start_date, "end": end_date}
        
        branch_filter = "AND branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        # 1. Total Sales & Count (Combined Invoices + POS)
        summary = db.execute(text(f"""
            WITH all_sales AS (
                SELECT 
                    total, 
                    COALESCE(exchange_rate, 1.0) as exchange_rate, 
                    paid_amount, 
                    invoice_date as sale_date, 
                    branch_id,
                    id,
                    'invoice' as source
                FROM invoices 
                WHERE invoice_type = 'sales' 
                AND status != 'cancelled'
                
                UNION ALL
                
                SELECT 
                    total_amount as total, 
                    1.0 as exchange_rate, 
                    paid_amount, 
                    CAST(order_date AS DATE) as sale_date, 
                    branch_id,
                    id,
                    'pos' as source
                FROM pos_orders
                WHERE status = 'paid'
            )
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total * exchange_rate), 0) as total_sales,
                COALESCE(SUM(paid_amount * exchange_rate), 0) as total_paid,
                COALESCE(SUM((total - paid_amount) * exchange_rate), 0) as total_due,
                COALESCE(SUM((total * COALESCE(exchange_rate, 1.0) * (
                    CASE WHEN source = 'invoice' THEN 
                        (SELECT AVG(tax_rate) FROM invoice_lines WHERE invoice_id = all_sales.id)
                    ELSE
                        15 -- Standard POS tax if not easily fetchable in this CTE
                    END
                ) / (100 + 15)) ), 0) as total_tax
            FROM all_sales 
            WHERE sale_date BETWEEN :start AND :end
            {branch_filter.replace('branch_id', 'branch_id')}
        """), params).fetchone()
        
        # 2. Approximate Profit (Combined Invoices + POS)
        profit_query = db.execute(text(f"""
            WITH combined_lines AS (
                SELECT 
                    (il.total - (il.total * il.tax_rate / (100 + il.tax_rate))) * COALESCE(i.exchange_rate, 1.0) as revenue,
                    il.quantity * COALESCE(p.cost_price, 0) as cogs,
                    i.invoice_date as sale_date,
                    i.branch_id
                FROM invoice_lines il
                JOIN invoices i ON il.invoice_id = i.id
                LEFT JOIN products p ON il.product_id = p.id
                WHERE i.invoice_type = 'sales' AND i.status != 'cancelled'
                
                UNION ALL
                
                SELECT 
                    poi.total - poi.tax_amount as revenue,
                    poi.quantity * COALESCE(p.cost_price, 0) as cogs,
                    CAST(po.order_date AS DATE) as sale_date,
                    po.branch_id
                FROM pos_order_lines poi
                JOIN pos_orders po ON poi.order_id = po.id
                LEFT JOIN products p ON poi.product_id = p.id
                WHERE po.status = 'paid'
            )
            SELECT 
                COALESCE(SUM(revenue), 0) as total_revenue,
                COALESCE(SUM(cogs), 0) as total_cogs
            FROM combined_lines
            WHERE sale_date BETWEEN :start AND :end
            {branch_filter}
        """), params).fetchone()
        
        revenue = float(profit_query.total_revenue or 0)
        cogs = float(profit_query.total_cogs or 0)

        gross_profit = revenue - cogs
        
        # 3. Operating Expenses from GL (expense accounts excluding COGS)
        # Use journal_lines for accurate calculation based on date range
        opex_params = {"start": start_date, "end": end_date}
        opex_branch_filter = ""
        if branch_id:
            opex_branch_filter = "AND je.branch_id = :opex_branch"
            opex_params["opex_branch"] = branch_id
            
        opex_query = db.execute(text(f"""
            SELECT COALESCE(SUM(jl.debit) - SUM(jl.credit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.journal_entry_id
            JOIN accounts a ON a.id = jl.account_id
            WHERE a.account_type = 'expense' 
            AND a.account_code NOT IN ('CGS')
            AND je.entry_date BETWEEN :start AND :end
            AND je.status = 'posted'
            {opex_branch_filter}
        """), opex_params).scalar() or 0
        
        operating_expenses = float(opex_query)
        net_profit = gross_profit - operating_expenses
        
        return {
            "period": {"start": start_date, "end": end_date},
            "stats": {
                "invoice_count": summary.count,
                "total_sales": float(summary.total_sales or 0),
                "total_paid": float(summary.total_paid or 0),
                "total_due": float(summary.total_due or 0),
                "net_revenue": revenue,
                "total_tax": float(summary.total_sales or 0) - revenue,
                "total_cogs": cogs,
                "gross_profit": gross_profit,
                "operating_expenses": operating_expenses,
                "net_profit": net_profit,
                "margin": (gross_profit / revenue * 100) if revenue > 0 else 0
            }
        }
    finally:
        db.close()

@router.get("/sales/trend", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def get_sales_trend(
    days: int = 30,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """اتجاه المبيعات اليومي"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        start_date = date.today() - timedelta(days=days)
        params = {"start": start_date}
        
        branch_filter = "AND branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id
        
        result = db.execute(text(f"""
            WITH all_sales AS (
                SELECT 
                    invoice_date as sale_date,
                    total * COALESCE(exchange_rate, 1.0) as total_bc,
                    branch_id
                FROM invoices 
                WHERE invoice_type = 'sales' AND status != 'cancelled'
                
                UNION ALL
                
                SELECT 
                    CAST(order_date AS DATE) as sale_date,
                    total_amount as total_bc,
                    branch_id
                FROM pos_orders
                WHERE status = 'paid'
            )
            SELECT 
                sale_date as date,
                COUNT(*) as count,
                COALESCE(SUM(total_bc), 0) as total
            FROM all_sales 
            WHERE sale_date >= :start
            {branch_filter.replace('branch_id', 'branch_id')}
            GROUP BY sale_date
            ORDER BY sale_date
        """), params).fetchall()
        
        return [{"date": row.date, "count": row.count, "total": float(row.total)} for row in result]
    finally:
        db.close()

@router.get("/sales/by-customer", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def get_sales_by_customer(
    limit: int = 5,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """أفضل العملاء"""
    db = get_db_connection(current_user.company_id)
    try:
        params = {"limit": limit}
        branch_filter = "AND i.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        result = db.execute(text(f"""
            WITH all_sales AS (
                SELECT 
                    party_id, 
                    total * COALESCE(exchange_rate, 1.0) as total_bc,
                    branch_id
                FROM invoices 
                WHERE invoice_type = 'sales' AND status != 'cancelled'
                
                UNION ALL
                
                SELECT 
                    customer_id as party_id, 
                    total_amount as total_bc,
                    branch_id
                FROM pos_orders
                WHERE status = 'paid'
            )
            SELECT 
                p.name as name,
                COUNT(s.party_id) as invoice_count,
                COALESCE(SUM(s.total_bc), 0) as total_sales
            FROM all_sales s
            JOIN parties p ON s.party_id = p.id
            WHERE 1=1
            {branch_filter.replace('i.branch_id', 's.branch_id')}
            GROUP BY p.id, p.name
            ORDER BY total_sales DESC
            LIMIT :limit
        """), params).fetchall()
        
        return [{"name": row.name, "count": row.invoice_count, "value": float(row.total_sales)} for row in result]
    finally:
        db.close()

@router.get("/sales/by-product", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def get_sales_by_product(
    limit: int = 5,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """المنتجات الأكثر مبيعاً"""
    db = get_db_connection(current_user.company_id)
    try:
        params = {"limit": limit}
        branch_filter = "AND i.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        result = db.execute(text(f"""
            WITH combined_lines AS (
                SELECT 
                    il.product_id,
                    il.quantity,
                    il.total * COALESCE(i.exchange_rate, 1.0) as total_bc,
                    i.branch_id
                FROM invoice_lines il
                JOIN invoices i ON il.invoice_id = i.id
                WHERE i.invoice_type = 'sales' AND i.status != 'cancelled'
                
                UNION ALL
                
                SELECT 
                    poi.product_id,
                    poi.quantity,
                    poi.total as total_bc,
                    po.branch_id
                FROM pos_order_lines poi
                JOIN pos_orders po ON poi.order_id = po.id
                WHERE po.status = 'paid'
            )
            SELECT 
                p.product_name as name,
                COALESCE(SUM(cl.quantity), 0) as quantity,
                COALESCE(SUM(cl.total_bc), 0) as total_sales
            FROM combined_lines cl
            JOIN products p ON cl.product_id = p.id
            WHERE 1=1
            {branch_filter.replace('i.branch_id', 'cl.branch_id')}
            GROUP BY p.id, p.product_name
            ORDER BY total_sales DESC
            LIMIT :limit
        """), params).fetchall()
        
        return [{"name": row.name, "quantity": float(row.quantity), "value": float(row.total_sales)} for row in result]
    finally:
        db.close()

@router.get("/sales/customer-statement/{customer_id}", response_model=Dict[str, Any], dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def get_customer_statement(
    customer_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """كشف حساب عميل تفصيلي"""
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        params = {"cid": customer_id, "start": start_date}
        branch_filter = "AND branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        # 1. Get Opening Balance (Combined: invoices + POS + payment vouchers)
        opening_balance = db.execute(text(f"""
            WITH all_movements AS (
                SELECT 
                    (total * COALESCE(exchange_rate, 1.0)) as debit, 
                    0 as credit,
                    invoice_date as sale_date,
                    branch_id,
                    party_id
                FROM invoices
                WHERE invoice_type = 'sales' AND status NOT IN ('cancelled', 'draft')
                
                UNION ALL
                
                SELECT 
                    total_amount as debit, 
                    0 as credit,
                    CAST(order_date AS DATE) as sale_date,
                    branch_id,
                    customer_id as party_id
                FROM pos_orders
                WHERE status = 'paid'
                
                UNION ALL
                
                SELECT 
                    0 as debit,
                    (amount * COALESCE(exchange_rate, 1.0)) as credit,
                    voucher_date as sale_date,
                    branch_id,
                    party_id
                FROM payment_vouchers
                WHERE party_type = 'customer' AND voucher_type = 'receipt' AND status != 'cancelled'
            )
            SELECT (COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0)) as balance
            FROM all_movements
            WHERE party_id = :cid AND sale_date < :start
            {branch_filter.replace('branch_id', 'branch_id')}
        """), params).scalar() or 0

        # Also consider manual transactions or deprecated table structure if needed,
        # but for now we rely on invoices. Ideally we should query customer_transactions.
        # Let's check `customer_transactions` table existence in database.py
        # Creating a more robust query using `customer_transactions` if populated, 
        # but our Invoice creation (sales.py) doesn't seem to insert into `customer_transactions` yet explicitly based on my last read?
        # Re-checking sales.py: create_invoice updates `customers` balance but I didn't see insert into `customer_transactions`.
        # Wait, `database.py` has `customer_transactions`.
        # If I didn't implement writing to `customer_transactions` in `sales.py`, the statement will be empty if I rely on it.
        # For this version, I will rely on `invoices` and `customer_receipts` (if implemented).
        # Let's stick to `invoices` for now as primary source.

        # 2. Get Transactions (Combined: invoices + POS + payment vouchers)
        params["end"] = end_date
        transactions = db.execute(text(f"""
            WITH all_movements AS (
                SELECT 
                    id, invoice_date as date, invoice_number as ref, 
                    'invoice' as type, (total * COALESCE(exchange_rate, 1.0)) as debit,
                    0 as credit,
                    currency, exchange_rate, branch_id, party_id
                FROM invoices
                WHERE invoice_type = 'sales' AND status NOT IN ('cancelled', 'draft')
                
                UNION ALL
                
                SELECT 
                    id, CAST(order_date AS DATE) as date, order_number as ref, 
                    'pos_order' as type, total_amount as debit, 
                    0 as credit,
                    (SELECT COALESCE((SELECT code FROM currencies WHERE is_base = TRUE LIMIT 1), (SELECT setting_value FROM company_settings WHERE setting_key = 'default_currency'), 'SYP')) as currency, 1.0 as exchange_rate, branch_id, customer_id as party_id
                FROM pos_orders
                WHERE status = 'paid'
                
                UNION ALL
                
                SELECT 
                    id, voucher_date as date, voucher_number as ref,
                    'receipt' as type, 0 as debit,
                    (amount * COALESCE(exchange_rate, 1.0)) as credit,
                    currency, exchange_rate, branch_id, party_id
                FROM payment_vouchers
                WHERE party_type = 'customer' AND voucher_type = 'receipt' AND status != 'cancelled'
            )
            SELECT * FROM all_movements
            WHERE party_id = :cid AND date BETWEEN :start AND :end
            {branch_filter.replace('branch_id', 'branch_id')}
            ORDER BY date
        """), params).fetchall()

        # 3. Running Balance
        statement = []
        running_balance = float(opening_balance)
        
        for t in transactions:
            debit = float(t.debit)
            credit = float(t.credit or 0) 
            
            balance_after = running_balance + debit - credit
            statement.append({
                "date": t.date,
                "ref": t.ref,
                "type": t.type,
                "debit": debit,
                "credit": credit,
                "balance": balance_after,
                "currency": t.currency,
                "original_amount": float(t.debit / (t.exchange_rate if t.exchange_rate else 1))
            })
            running_balance = balance_after

        return {
            "customer_id": customer_id,
            "period": {"start": start_date, "end": end_date},
            "opening_balance": float(opening_balance),
            "transactions": statement,
            "closing_balance": running_balance
        }
    finally:
        db.close()

@router.get("/sales/aging", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def get_aging_report(
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير أعمار الديون"""
    db = get_db_connection(current_user.company_id)
    try:
        params = {}
        branch_filter = "AND i.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id
        # Get all unpaid invoices with days overdue
        results = db.execute(text(f"""
            SELECT 
                p.name as customer_name,
                i.invoice_number,
                i.invoice_date,
                i.due_date,
                (i.total - COALESCE(i.paid_amount, 0)) as due_amount_fc,
                (i.total - COALESCE(i.paid_amount, 0)) * COALESCE(i.exchange_rate, 1) as due_amount,
                CURRENT_DATE - COALESCE(i.due_date, i.invoice_date) as days_old,
                i.currency
            FROM invoices i
            JOIN parties p ON i.party_id = p.id
            WHERE i.invoice_type = 'sales' 
            AND i.status NOT IN ('draft', 'cancelled', 'paid')
            AND (i.total - COALESCE(i.paid_amount, 0)) > 0.01
            {branch_filter}
            ORDER BY days_old DESC
        """), params).fetchall()

        # Group buckets
        report = []
        for row in results:
            bucket = "0-30"
            days = row.days_old or 0
            if days > 90: bucket = "90+"
            elif days > 60: bucket = "61-90"
            elif days > 30: bucket = "31-60"
            
            report.append({
                "customer": row.customer_name,
                "invoice": row.invoice_number,
                "date": row.invoice_date,
                "due_date": row.due_date,
                "amount": float(row.due_amount or 0),
                "amount_fc": float(row.due_amount_fc or 0),
                "currency": row.currency,
                "days": days,
                "bucket": bucket
            })
            
        return report
    finally:
        db.close()

# --- Purchases Reports ---

@router.get("/purchases/summary", response_model=Dict[str, Any], dependencies=[Depends(require_permission(["buying.reports", "reports.view"]))])
def get_purchases_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """ملخص المشتريات"""
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            import calendar
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            end_date = start_date.replace(day=last_day)
            
        params = {"start": start_date, "end": end_date}
        
        branch_filter = "AND branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id
        
        summary = db.execute(text(f"""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total), 0) as total_purchases,
                COALESCE(SUM(paid_amount), 0) as total_paid,
                COALESCE(SUM(total - paid_amount), 0) as total_due
            FROM invoices 
            WHERE invoice_type = 'purchase' 
            AND invoice_date BETWEEN :start AND :end
            {branch_filter}
        """), params).fetchone()
        
        return {
            "period": {"start": start_date, "end": end_date},
            "stats": {
                "invoice_count": summary.count,
                "total_purchases": float(summary.total_purchases or 0),
                "total_paid": float(summary.total_paid or 0),
                "total_due": float(summary.total_due or 0)
            }
        }
    finally:
        db.close()

@router.get("/purchases/trend", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["buying.reports", "reports.view"]))])
def get_purchases_trend(
    days: int = 30,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """اتجاه المشتريات اليومي"""
    db = get_db_connection(current_user.company_id)
    try:
        start_date = date.today() - timedelta(days=days)
        params = {"start": start_date}
        
        branch_filter = "AND branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        result = db.execute(text(f"""
            SELECT 
                invoice_date as date,
                COUNT(*) as count,
                COALESCE(SUM(total), 0) as total
            FROM invoices 
            WHERE invoice_type = 'purchase' 
            AND invoice_date >= :start
            {branch_filter}
            GROUP BY invoice_date
            ORDER BY invoice_date
        """), params).fetchall()
        
        return [{"date": row.date, "count": row.count, "total": float(row.total)} for row in result]
    finally:
        db.close()

@router.get("/purchases/by-supplier", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["buying.reports", "reports.view"]))])
def get_purchases_by_supplier(
    limit: int = 5,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """أكبر الموردين"""
    db = get_db_connection(current_user.company_id)
    try:
        params = {"limit": limit}
        branch_filter = "AND i.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        result = db.execute(text(f"""
            SELECT 
                p.name as name,
                COUNT(i.id) as invoice_count,
                COALESCE(SUM(i.total), 0) as total_purchases
            FROM invoices i
            JOIN parties p ON i.party_id = p.id
            WHERE i.invoice_type = 'purchase'
            {branch_filter}
            GROUP BY p.id, p.name
            ORDER BY total_purchases DESC
            LIMIT :limit
        """), params).fetchall()
        
        return [{"name": row.name, "count": row.invoice_count, "value": float(row.total_purchases)} for row in result]
    finally:
        db.close()

@router.get("/purchases/supplier-statement/{supplier_id}", response_model=Dict[str, Any], dependencies=[Depends(require_permission(["buying.reports", "reports.view"]))])
def get_supplier_statement(
    supplier_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """كشف حساب مورد تفصيلي"""
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()
            
        params = {"sid": supplier_id, "start": start_date}
        branch_filter = "AND branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        # 1. Get Opening Balance (Before start_date)
        # For suppliers: Invoices (credit/increase) - Payments (debit/decrease)
        opening_balance = db.execute(text(f"""
            WITH all_movements AS (
                SELECT 
                    0 as debit, total as credit,
                    invoice_date as txn_date,
                    branch_id,
                    party_id
                FROM invoices
                WHERE invoice_type = 'purchase' AND status NOT IN ('cancelled', 'draft')
                
                UNION ALL
                
                SELECT 
                    (amount * COALESCE(exchange_rate, 1.0)) as debit, 0 as credit,
                    voucher_date as txn_date,
                    branch_id,
                    party_id
                FROM payment_vouchers
                WHERE party_type = 'supplier' AND voucher_type = 'payment' AND status != 'cancelled'
            )
            SELECT (COALESCE(SUM(credit), 0) - COALESCE(SUM(debit), 0)) as balance
            FROM all_movements
            WHERE party_id = :sid AND txn_date < :start
            {branch_filter}
        """), params).scalar() or 0

        # 2. Get Transactions (invoices + payment vouchers)
        params["end"] = end_date
        transactions = db.execute(text(f"""
            WITH all_movements AS (
                SELECT 
                    id, invoice_date as date, invoice_number as ref, 
                    'invoice' as type, total as credit, 0 as debit,
                    party_id, branch_id
                FROM invoices
                WHERE invoice_type = 'purchase' AND status NOT IN ('cancelled', 'draft')
                
                UNION ALL
                
                SELECT 
                    id, voucher_date as date, voucher_number as ref,
                    'payment' as type, 0 as credit,
                    (amount * COALESCE(exchange_rate, 1.0)) as debit,
                    party_id, branch_id
                FROM payment_vouchers
                WHERE party_type = 'supplier' AND voucher_type = 'payment' AND status != 'cancelled'
            )
            SELECT * FROM all_movements
            WHERE party_id = :sid AND date BETWEEN :start AND :end
            {branch_filter}
            ORDER BY date
        """), params).fetchall()

        # 3. Running Balance
        statement = []
        running_balance = float(opening_balance)
        
        for t in transactions:
            credit = float(t.credit) # Purchase increases debt
            debit = float(t.debit)   # Payment reduces debt
            
            balance_after = running_balance + credit - debit
            statement.append({
                "date": t.date,
                "ref": t.ref,
                "type": t.type,
                "debit": debit,
                "credit": credit,
                "balance": balance_after
            })
            running_balance = balance_after

        return {
            "supplier_id": supplier_id,
            "period": {"start": start_date, "end": end_date},
            "opening_balance": float(opening_balance),
            "transactions": statement,
            "closing_balance": running_balance
        }
    finally:
        db.close()

# --- HR Reports ---

@router.get("/hr/payroll/trend", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["hr.reports", "reports.view"]))])
def get_payroll_trend(
    months: int = 12,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """اتجاه تكاليف الرواتب الشهرية"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        # Calculate start date (first day of month, 'months' ago)
        today = date.today()
        start_date = (today.replace(day=1) - timedelta(days=months*30)).replace(day=1)
        
        params = {"start": start_date}
        
        # Note: Payroll Periods are generally company-wide, but we can filter entries by employee branch if needed.
        # However, payroll_periods table is the main grouper.
        # Let's group by period end_date or start_date.
        
        query = """
            SELECT 
                TO_CHAR(p.end_date, 'YYYY-MM') as month,
                COALESCE(SUM(pe.net_salary), 0) as total_net,
                COALESCE(SUM(pe.basic_salary + pe.housing_allowance + pe.transport_allowance + pe.other_allowances), 0) as total_gross
            FROM payroll_periods p
            JOIN payroll_entries pe ON p.id = pe.period_id
            JOIN employees e ON pe.employee_id = e.id
            WHERE p.status = 'posted'
            AND p.end_date >= :start
        """
        
        if branch_id:
            query += " AND e.branch_id = :branch_id"
            params["branch_id"] = branch_id
            
        query += """
            GROUP BY TO_CHAR(p.end_date, 'YYYY-MM')
            ORDER BY month
        """
        
        result = db.execute(text(query), params).fetchall()
        
        # Fill missing months? For now just return data
        return [
            {
                "month": row.month, 
                "total_net": float(row.total_net), 
                "total_gross": float(row.total_gross)
            } 
            for row in result
        ]
    finally:
        db.close()

@router.get("/hr/leaves/usage", response_model=List[Dict[str, Any]], dependencies=[Depends(require_permission(["hr.reports", "reports.view"]))])
def get_leave_usage(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """إحصائيات الإجازات حسب النوع"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1, month=1) # Start of year
        if not end_date:
            end_date = date.today()
            
        params = {"start": start_date, "end": end_date}
        
        branch_filter = ""
        if branch_id:
            branch_filter = "AND e.branch_id = :branch_id"
            params["branch_id"] = branch_id

        # Group by Leave Type
        query = f"""
            SELECT 
                l.leave_type,
                COUNT(*) as request_count,
                COALESCE(SUM(l.end_date - l.start_date + 1), 0) as total_days
            FROM leave_requests l
            JOIN employees e ON l.employee_id = e.id
            WHERE l.status = 'approved'
            AND l.start_date BETWEEN :start AND :end
            {branch_filter}
            GROUP BY l.leave_type
        """
        
        result = db.execute(text(query), params).fetchall()
        
        return [
            {
                "type": row.leave_type,
                "count": row.request_count,
                "days": int(row.total_days)
            }
            for row in result
        ]
    finally:
        db.close()
@router.get("/accounting/trial-balance", response_model=TrialBalanceResponse, dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def get_trial_balance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب ميزان المراجعة لفترة محددة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1, month=1) # Start of year
        if not end_date:
            end_date = date.today()
            
        params = {"start": start_date, "end": end_date}
        
        branch_filter = ""
        if branch_id:
            branch_filter = "AND je.branch_id = :branch_id"
            params["branch_id"] = branch_id

        query = f"""
            WITH opening_bal AS (
                SELECT 
                    jl.account_id,
                    SUM(jl.debit) as open_debit,
                    SUM(jl.credit) as open_credit
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                WHERE je.entry_date < :start
                AND je.status = 'posted'
                {branch_filter}
                GROUP BY jl.account_id
            ),
            movement AS (
                SELECT 
                    jl.account_id,
                    SUM(jl.debit) as period_debit,
                    SUM(jl.credit) as period_credit
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                WHERE je.entry_date BETWEEN :start AND :end
                AND je.status = 'posted'
                {branch_filter}
                GROUP BY jl.account_id
            )
            SELECT 
                a.id, a.account_number, a.name, a.name_en, a.account_type,
                COALESCE(o.open_debit, 0) as open_debit,
                COALESCE(o.open_credit, 0) as open_credit,
                COALESCE(m.period_debit, 0) as period_debit,
                COALESCE(m.period_credit, 0) as period_credit
            FROM accounts a
            LEFT JOIN opening_bal o ON a.id = o.account_id
            LEFT JOIN movement m ON a.id = m.account_id
            WHERE (o.open_debit IS NOT NULL OR o.open_credit IS NOT NULL OR m.period_debit IS NOT NULL OR m.period_credit IS NOT NULL)
            ORDER BY a.account_number
        """
        
        result = db.execute(text(query), params).fetchall()
        
        data = []
        total_open_dr = total_open_cr = total_period_dr = total_period_cr = total_close_dr = total_close_cr = 0
        
        for row in result:
            acct_type = row.account_type
            
            # Net opening balance by account type direction
            raw_open_dr = float(row.open_debit)
            raw_open_cr = float(row.open_credit)
            open_net = raw_open_dr - raw_open_cr  # positive = debit balance
            
            # Debit-normal accounts (asset, expense): show net in DR if positive
            # Credit-normal accounts (liability, equity, revenue): show net in CR if positive
            if acct_type in ('asset', 'expense'):
                o_dr = open_net if open_net > 0 else 0
                o_cr = abs(open_net) if open_net < 0 else 0
            else:
                # For credit-normal accounts, flip: negative net means debit excess
                o_cr = abs(open_net) if open_net < 0 else 0  # credit-normal: net < 0 means excess debit
                o_dr = open_net if open_net > 0 else 0
                # Actually: credit-normal: positive credit balance = credit - debit > 0 → net < 0
                # Recalculate: for credit-normal, opening = CR - DR (if positive → show in CR column)
                credit_net = raw_open_cr - raw_open_dr
                o_cr = credit_net if credit_net > 0 else 0
                o_dr = abs(credit_net) if credit_net < 0 else 0
            
            # Period movement
            p_dr = float(row.period_debit)
            p_cr = float(row.period_credit)
            
            # Closing
            # Standard Accounting logic: (DR_open + DR_period) - (CR_open + CR_period)
            # If positive -> Closing DR. If negative -> Closing CR.
            net_total = (o_dr + p_dr) - (o_cr + p_cr)
            
            c_dr = net_total if net_total > 0 else 0
            c_cr = abs(net_total) if net_total < 0 else 0
            
            data.append({
                "account_id": row.id,
                "account_number": row.account_number,
                "name": row.name,
                "name_en": row.name_en,
                "account_type": row.account_type,
                "opening_debit": o_dr,
                "opening_credit": o_cr,
                "period_debit": p_dr,
                "period_credit": p_cr,
                "closing_debit": c_dr,
                "closing_credit": c_cr
            })
            
            total_open_dr += o_dr
            total_open_cr += o_cr
            total_period_dr += p_dr
            total_period_cr += p_cr
            total_close_dr += c_dr
            total_close_cr += c_cr
            
        return {
            "period": {"start": start_date, "end": end_date},
            "data": data,
            "totals": {
                "opening_debit": total_open_dr,
                "opening_credit": total_open_cr,
                "period_debit": total_period_dr,
                "period_credit": total_period_cr,
                "closing_debit": total_close_dr,
                "closing_credit": total_close_cr
            }
        }
    finally:
        db.close()

def _get_profit_loss_data(db, start_date, end_date, branch_id=None):
    """Internal helper to get profit loss data"""
    params = {"start": start_date, "end": end_date}
    branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""
    if branch_id: params["branch_id"] = branch_id

    # Fetch all accounts and their period balances
    query = f"""
        SELECT 
            a.id, a.account_number, a.name, a.name_en, a.account_type, a.parent_id,
            COALESCE(SUM(CASE 
                WHEN a.account_type = 'expense' THEN jl.debit - jl.credit
                WHEN a.account_type = 'revenue' THEN jl.credit - jl.debit
                ELSE 0 
            END), 0) as balance
        FROM accounts a
        LEFT JOIN journal_lines jl ON a.id = jl.account_id
        LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
        WHERE a.account_type IN ('revenue', 'expense')
        AND (je.id IS NULL OR (je.entry_date BETWEEN :start AND :end AND je.status = 'posted' {branch_filter}))
        GROUP BY a.id, a.account_number, a.name, a.name_en, a.account_type, a.parent_id
        ORDER BY a.account_number
    """
    
    accounts = [dict(row._mapping) for row in db.execute(text(query), params).fetchall()]
    
    # Build hierarchy
    account_map = {a["id"]: {**a, "children": [], "level": 0} for a in accounts}
    roots = []
    
    # First pass: map children and find roots
    for acc_id, acc in account_map.items():
        parent_id = acc["parent_id"]
        if parent_id and parent_id in account_map:
            account_map[parent_id]["children"].append(acc)
        else:
            roots.append(acc)
    
    # Second pass: Roll up balances and set levels
    def rollup(node, level):
        node["level"] = level
        child_sum = 0
        for child in node["children"]:
            child_sum += rollup(child, level + 1)
        node["balance"] = float(node["balance"]) + child_sum
        return node["balance"]

    total_revenue = 0
    total_expense = 0
    for root in roots:
        bal = rollup(root, 0)
        if root["account_type"] == 'revenue':
            total_revenue += bal
        elif root["account_type"] == 'expense':
            total_expense += bal
    
    # Net Income = Revenue - Expenses (not Revenue + Expenses)
    net_income = total_revenue - total_expense
        
    return {
        "period": {"start": start_date, "end": end_date},
        "data": roots,
        "total": net_income
    }

@router.get("/accounting/profit-loss", response_model=FinancialStatementResponse, dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def get_profit_loss(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب قائمة الدخل (الأرباح والخسائر) الهيكلية"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1, month=1)
        if not end_date:
            end_date = date.today()
            
        return _get_profit_loss_data(db, start_date, end_date, branch_id)
    finally:
        db.close()

def _get_balance_sheet_data(db, as_of_date, branch_id=None):
    """Internal helper to get balance sheet data"""
    branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""
    params = {"as_of": as_of_date}
    if branch_id: params["branch_id"] = branch_id

    # Balance Sheet follows Assets = Liabilities + Equity
    # We sum all transactions from the beginning of time up to as_of_date
    query = f"""
        SELECT 
            a.id, a.account_number, a.name, a.name_en, a.account_type, a.parent_id,
            COALESCE(SUM(CASE 
                WHEN a.account_type IN ('asset', 'expense') THEN jl.debit - jl.credit
                ELSE jl.credit - jl.debit
            END), 0) as balance
        FROM accounts a
        LEFT JOIN journal_lines jl ON a.id = jl.account_id
        LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
        WHERE a.account_type IN ('asset', 'liability', 'equity')
        AND (je.id IS NULL OR (je.entry_date <= :as_of AND je.status = 'posted' {branch_filter}))
        GROUP BY a.id, a.account_number, a.name, a.name_en, a.account_type, a.parent_id
        ORDER BY a.account_number
    """
    
    accounts = [dict(row._mapping) for row in db.execute(text(query), params).fetchall()]
    
    # Build hierarchy
    account_map = {a["id"]: {**a, "children": [], "level": 0} for a in accounts}
    roots = []
    
    for acc_id, acc in account_map.items():
        parent_id = acc["parent_id"]
        if parent_id and parent_id in account_map:
            account_map[parent_id]["children"].append(acc)
        else:
            roots.append(acc)
    
    def rollup(node, level):
        node["level"] = level
        child_sum = 0
        for child in node["children"]:
            child_sum += rollup(child, level + 1)
        node["balance"] = float(node["balance"]) + child_sum
        return node["balance"]

    for root in roots:
        rollup(root, 0)
    
    # Calculate Retained Earnings (Net Income) = Revenue - Expenses
    # This ensures Balance Sheet balances: Assets = Liabilities + Equity + Retained Earnings
    net_income_query = f"""
        SELECT 
            COALESCE(SUM(CASE WHEN a.account_type = 'revenue' THEN jl.credit - jl.debit ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN a.account_type = 'expense' THEN jl.debit - jl.credit ELSE 0 END), 0) as net_income
        FROM journal_lines jl
        JOIN journal_entries je ON jl.journal_entry_id = je.id
        JOIN accounts a ON jl.account_id = a.id
        WHERE a.account_type IN ('revenue', 'expense')
        AND je.entry_date <= :as_of AND je.status = 'posted' {branch_filter}
    """
    net_income_row = db.execute(text(net_income_query), params).fetchone()
    
    retained_earnings = float(net_income_row.net_income) if net_income_row else 0
    
    # Add retained earnings as a virtual equity item
    if retained_earnings != 0:
        roots.append({
            "id": -1,
            "account_number": "RE",
            "name": "Retained Earnings / الأرباح المبقاة",
            "name_en": "Retained Earnings",
            "account_type": "equity",
            "balance": retained_earnings,
            "children": [],
            "level": 0
        })

    # Compute totals
    total_assets = sum(r["balance"] for r in roots if r.get("account_type") == "asset")
    total_liabilities = sum(r["balance"] for r in roots if r.get("account_type") == "liability")
    total_equity = sum(r["balance"] for r in roots if r.get("account_type") == "equity") + retained_earnings

    return {
        "period": {"start": as_of_date, "end": as_of_date},
        "data": roots,
        "total": total_assets,
        "as_of": as_of_date,
        "net_income": retained_earnings,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity
    }

@router.get("/accounting/balance-sheet", response_model=FinancialStatementResponse, dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def get_balance_sheet(
    as_of_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب الميزانية العمومية الهيكلية"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not as_of_date:
            as_of_date = date.today()
            
        return _get_balance_sheet_data(db, as_of_date, branch_id)
    finally:
        db.close()

@router.get("/accounting/budget-vs-actual", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def get_budget_report(
    budget_id: int,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """مقارنة الميزانية التقديرية مع الفعلي"""
    company_id = current_user.company_id if not isinstance(current_user, dict) else current_user.get("company_id")
    db = get_db_connection(company_id)
    try:
        # 1. Get Budget info
        budget = db.execute(text("SELECT * FROM budgets WHERE id = :id"), {"id": budget_id}).fetchone()
        if not budget:
             raise HTTPException(status_code=404, detail="الميزانية غير موجودة")
             
        start_date = budget.start_date
        end_date = budget.end_date
        
        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""
        params = {"start": start_date, "end": end_date, "bid": budget_id}
        if branch_id: params["branch_id"] = branch_id

        # 2. Get Budget Items vs Actuals
        query = f"""
            SELECT 
                a.id as account_id, a.account_number, a.name, a.name_en,
                bi.planned_amount,
                COALESCE(actuals.balance, 0) as actual_amount
            FROM budget_items bi
            JOIN accounts a ON bi.account_id = a.id
            LEFT JOIN (
                SELECT 
                    jl.account_id,
                    SUM(CASE 
                        WHEN a2.account_type IN ('expense', 'asset') THEN jl.debit - jl.credit
                        ELSE jl.credit - jl.debit
                    END) as balance
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                JOIN accounts a2 ON jl.account_id = a2.id
                WHERE je.entry_date BETWEEN :start AND :end
                  AND je.status = 'posted'
                  {branch_filter}
                GROUP BY jl.account_id
            ) as actuals ON bi.account_id = actuals.account_id
            WHERE bi.budget_id = :bid
            ORDER BY a.account_number
        """
        
        items = db.execute(text(query), params).fetchall()
        
        report_data = []
        for r in items:
            planned = float(r.planned_amount or 0)
            actual = float(r.actual_amount or 0)
            variance = planned - actual
            performance = (actual / planned * 100) if planned != 0 else 0
            
            report_data.append({
                "account_id": r.account_id,
                "account_number": r.account_number,
                "name": r.name,
                "name_en": r.name_en,
                "planned": planned,
                "actual": actual,
                "variance": variance,
                "performance_pct": performance
            })
            
        return {
            "budget": dict(budget._mapping),
            "data": report_data
        }
    finally:
        db.close()

@router.get("/accounting/cashflow", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def get_cashflow_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير التدفقات النقدية (مبسط)"""
    company_id = current_user.company_id if not isinstance(current_user, dict) else current_user.get("company_id")
    db = get_db_connection(company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()
            
        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""
        params = {"start": start_date, "end": end_date}
        if branch_id: params["branch_id"] = branch_id

        # 1. Get all Cash/Bank GL Account IDs
        # From treasury_accounts table
        treasury_gl_ids = [row[0] for row in db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE is_active = true")).fetchall() if row[0]]
        
        # From legacy codes (BOX, BNK)
        legacy_gl_ids = [row[0] for row in db.execute(text("SELECT id FROM accounts WHERE account_code IN ('BOX', 'BNK')")).fetchall()]
        
        # Combine and deduplicate
        all_cash_ids = list(set(treasury_gl_ids + legacy_gl_ids))
        
        if not all_cash_ids:
            return {
                "period": {"start": start_date, "end": end_date},
                "inflows": [], "outflows": [], "total_inflow": 0, "total_outflow": 0, "net_cash_flow": 0
            }

        # Build safe IN clause using f-string (IDs are from DB, not user input)
        cash_ids_str = ','.join(map(str, all_cash_ids))

        # Inflows (Debit Cash/Bank)
        inflow_query = f"""
            SELECT 
                a_other.account_type, 
                a_other.name as category,
                SUM(jl_other.credit) as amount
            FROM journal_lines jl_cash
            JOIN journal_entries je ON jl_cash.journal_entry_id = je.id
            JOIN accounts a_cash ON jl_cash.account_id = a_cash.id
            JOIN journal_lines jl_other ON je.id = jl_other.journal_entry_id
            JOIN accounts a_other ON jl_other.account_id = a_other.id
            WHERE a_cash.id IN ({cash_ids_str})
              AND jl_cash.debit > 0
              AND a_other.id != a_cash.id
              AND je.entry_date BETWEEN :start AND :end
              AND je.status = 'posted'
              {branch_filter}
            GROUP BY a_other.account_type, a_other.name
        """
        
        inflows = db.execute(text(inflow_query), params).fetchall()
        
        # Outflows (Credit Cash/Bank)
        outflow_query = f"""
            SELECT 
                a_other.account_type, 
                a_other.name as category,
                SUM(jl_other.debit) as amount
            FROM journal_lines jl_cash
            JOIN journal_entries je ON jl_cash.journal_entry_id = je.id
            JOIN accounts a_cash ON jl_cash.account_id = a_cash.id
            JOIN journal_lines jl_other ON je.id = jl_other.journal_entry_id
            JOIN accounts a_other ON jl_other.account_id = a_other.id
            WHERE a_cash.id IN ({cash_ids_str})
              AND jl_cash.credit > 0
              AND a_other.id != a_cash.id
              AND je.entry_date BETWEEN :start AND :end
              AND je.status = 'posted'
              {branch_filter}
            GROUP BY a_other.account_type, a_other.name
        """
        
        outflows = db.execute(text(outflow_query), params).fetchall()
        
        return {
            "period": {"start": start_date, "end": end_date},
            "inflows": [dict(r._mapping) for r in inflows],
            "outflows": [dict(r._mapping) for r in outflows],
            "total_inflow": sum(float(r.amount) for r in inflows),
            "total_outflow": sum(float(r.amount) for r in outflows),
            "net_cash_flow": sum(float(r.amount) for r in inflows) - sum(float(r.amount) for r in outflows)
        }
    finally:
        db.close()


@router.get("/accounting/general-ledger", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def get_general_ledger(
    account_id: int = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """جلب دفتر الأستاذ العام - حركات حساب محدد"""
    if not account_id:
        raise HTTPException(status_code=400, detail="يجب تحديد الحساب")
    
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        if not start_date:
            start_date = date.today().replace(day=1, month=1)
        if not end_date:
            end_date = date.today()
            
        params = {"account_id": account_id, "start": start_date, "end": end_date}
        
        branch_filter = ""
        if branch_id:
            branch_filter = "AND je.branch_id = :branch_id"
            params["branch_id"] = branch_id

        query = f"""
            SELECT 
                je.entry_date,
                je.entry_number,
                je.description,
                je.reference,
                jl.debit,
                jl.credit,
                jl.description as line_description
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            WHERE jl.account_id = :account_id
            AND je.entry_date BETWEEN :start AND :end
            AND je.status = 'posted'
            {branch_filter}
            ORDER BY je.entry_date ASC, je.id ASC
        """
        
        result = db.execute(text(query), params).fetchall()
        
        entries = []
        for row in result:
            entries.append({
                "entry_date": str(row.entry_date),
                "entry_number": row.entry_number,
                "description": row.line_description or row.description,
                "reference": row.reference,
                "debit": float(row.debit),
                "credit": float(row.credit)
            })
        
        return {
            "account_id": account_id,
            "period": {"start": start_date, "end": end_date},
            "entries": entries
        }
    finally:
        db.close()


# ==================== ACC-004: Period Comparison Reports ====================

@router.get("/accounting/profit-loss/compare", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def compare_profit_loss(
    periods: str = "2025-01-01:2025-12-31,2024-01-01:2024-12-31",
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """مقارنة قوائم الدخل بين فترات متعددة
    periods: comma-separated pairs start:end  e.g. 2025-01-01:2025-12-31,2024-01-01:2024-12-31
    """
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        parsed = _parse_periods(periods)
        if len(parsed) < 2:
            raise HTTPException(status_code=400, detail="يجب تحديد فترتين على الأقل للمقارنة")

        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""

        # Fetch all revenue/expense accounts once
        all_accounts = db.execute(text("""
            SELECT id, account_number, name, name_en, account_type, parent_id
            FROM accounts WHERE account_type IN ('revenue', 'expense')
            ORDER BY account_number
        """)).fetchall()
        account_list = [dict(r._mapping) for r in all_accounts]

        period_results = []
        for p in parsed:
            params = {"start": p["start"], "end": p["end"]}
            if branch_id:
                params["branch_id"] = branch_id

            balances = db.execute(text(f"""
                SELECT a.id,
                    COALESCE(SUM(CASE
                        WHEN a.account_type = 'expense' THEN jl.debit - jl.credit
                        WHEN a.account_type = 'revenue' THEN jl.credit - jl.debit
                        ELSE 0
                    END), 0) as balance
                FROM accounts a
                LEFT JOIN journal_lines jl ON a.id = jl.account_id
                LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
                    AND je.entry_date BETWEEN :start AND :end
                    AND je.status = 'posted' {branch_filter}
                WHERE a.account_type IN ('revenue', 'expense')
                GROUP BY a.id
            """), params).fetchall()
            bal_map = {r.id: float(r.balance) for r in balances}

            accounts_with_bal = []
            total_rev = 0
            total_exp = 0
            for a in account_list:
                bal = bal_map.get(a["id"], 0)
                accounts_with_bal.append({**a, "balance": bal})
                if a["account_type"] == "revenue":
                    total_rev += bal
                elif a["account_type"] == "expense":
                    total_exp += bal

            period_results.append({
                "period": {"start": str(p["start"]), "end": str(p["end"]), "label": p.get("label", "")},
                "accounts": accounts_with_bal,
                "total_revenue": total_rev,
                "total_expense": total_exp,
                "net_income": total_rev - total_exp,
            })

        # Build flat comparison table
        comparison = _build_comparison_table(account_list, period_results, "revenue_expense")

        return {
            "periods": [pr["period"] for pr in period_results],
            "summary": [{
                "period": pr["period"],
                "total_revenue": pr["total_revenue"],
                "total_expense": pr["total_expense"],
                "net_income": pr["net_income"],
            } for pr in period_results],
            "comparison": comparison,
        }
    finally:
        db.close()


@router.get("/accounting/balance-sheet/compare", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def compare_balance_sheet(
    periods: str = "2025-12-31,2024-12-31",
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """مقارنة الميزانية العمومية بين تواريخ متعددة
    periods: comma-separated dates  e.g. 2025-12-31,2024-12-31
    """
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        dates = [d.strip() for d in periods.split(",") if d.strip()]
        if len(dates) < 2:
            raise HTTPException(status_code=400, detail="يجب تحديد تاريخين على الأقل")

        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""

        all_accounts = db.execute(text("""
            SELECT id, account_number, name, name_en, account_type, parent_id
            FROM accounts WHERE account_type IN ('asset', 'liability', 'equity')
            ORDER BY account_number
        """)).fetchall()
        account_list = [dict(r._mapping) for r in all_accounts]

        period_results = []
        for d in dates:
            params = {"end": d}
            if branch_id:
                params["branch_id"] = branch_id

            balances = db.execute(text(f"""
                SELECT a.id,
                    COALESCE(SUM(CASE
                        WHEN a.account_type IN ('asset', 'expense') THEN jl.debit - jl.credit
                        ELSE jl.credit - jl.debit
                    END), 0) as balance
                FROM accounts a
                LEFT JOIN journal_lines jl ON a.id = jl.account_id
                LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
                    AND je.entry_date <= :end
                    AND je.status = 'posted' {branch_filter}
                WHERE a.account_type IN ('asset', 'liability', 'equity')
                GROUP BY a.id
            """), params).fetchall()
            bal_map = {r.id: float(r.balance) for r in balances}

            accounts_with_bal = []
            total_assets = 0
            total_liab = 0
            total_equity = 0
            for a in account_list:
                bal = bal_map.get(a["id"], 0)
                accounts_with_bal.append({**a, "balance": bal})
                if a["account_type"] == "asset":
                    total_assets += bal
                elif a["account_type"] == "liability":
                    total_liab += bal
                elif a["account_type"] == "equity":
                    total_equity += bal

            period_results.append({
                "period": {"date": d, "label": d},
                "accounts": accounts_with_bal,
                "total_assets": total_assets,
                "total_liabilities": total_liab,
                "total_equity": total_equity,
            })

        comparison = _build_comparison_table(account_list, period_results, "balance_sheet")

        return {
            "periods": [pr["period"] for pr in period_results],
            "summary": [{
                "period": pr["period"],
                "total_assets": pr["total_assets"],
                "total_liabilities": pr["total_liabilities"],
                "total_equity": pr["total_equity"],
            } for pr in period_results],
            "comparison": comparison,
        }
    finally:
        db.close()


# ==================== Export Endpoints ====================

from utils.exports import generate_pdf, generate_excel, create_export_response
from fastapi.responses import StreamingResponse

@router.get("/accounting/profit-loss/export", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def export_profit_loss(
    format: str = "pdf",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تصدير قائمة الدخل (PDF/Excel)"""
    branch_id = validate_branch_access(current_user, branch_id)
    
    # Parse dates
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today().replace(day=1, month=1)
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Reuse get_profit_loss logic (call it directly or refactor)
    # For simplicity, calling the function logic essentially
    data = get_profit_loss(start_date=s_date, end_date=e_date, branch_id=branch_id, current_user=current_user)
    
    # Flatten data for export
    flat_data = []
    
    def flatten(nodes, indent=0):
        for node in nodes:
            flat_data.append({
                "Account Number": node["account_number"],
                "Account Name": f"{'  ' * indent}{node['name']}",
                "Balance": f"{float(node['balance']):,.2f}",
                "Type": node["account_type"]
            })
            if node.get("children"):
                flatten(node["children"], indent + 1)
                
    flatten(data["data"])
    
    # Add Total Row
    flat_data.append({
        "Account Number": "",
        "Account Name": "Net Income / صافي الدخل",
        "Balance": f"{float(data['total']):,.2f}",
        "Type": ""
    })
    
    if format == "excel":
        buffer = generate_excel(flat_data, ["Account Number", "Account Name", "Balance"])
        return create_export_response(buffer, f"profit_loss_{s_date}_{e_date}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        # Prepare PDF data (List of Lists)
        pdf_data = [["Account #", "Account Name", "Balance"]]
        for row in flat_data:
            pdf_data.append([row["Account Number"], row["Account Name"], row["Balance"]])
            
        buffer = generate_pdf(pdf_data, f"Profit & Loss ({s_date} to {e_date})")
        return create_export_response(buffer, f"profit_loss_{s_date}_{e_date}.pdf", "application/pdf")

@router.get("/accounting/balance-sheet/export", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def export_balance_sheet(
    format: str = "pdf",
    as_of_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تصدير الميزانية العمومية (PDF/Excel)"""
    branch_id = validate_branch_access(current_user, branch_id)
    
    try:
        target_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
    data = get_balance_sheet(as_of_date=target_date, branch_id=branch_id, current_user=current_user)
    
    flat_data = []
    def flatten(nodes, indent=0):
        for node in nodes:
            flat_data.append({
                "Account Number": node.get("account_number", ""),
                "Account Name": f"{'  ' * indent}{node['name']}",
                "Balance": f"{float(node['balance']):,.2f}",
                "Type": node["account_type"]
            })
            if node.get("children"):
                flatten(node["children"], indent + 1)
    
    flatten(data["data"])
    
    # Add Totals? The hierarchical view already sums up, but get_balance_sheet 
    # returns structure where roots Sum up to Total Assets (Left side) = Liabilities + Equity (Right Side)
    # Ideally logic should separate Assets vs Liab/Equity
    
    if format == "excel":
        buffer = generate_excel(flat_data, ["Account Number", "Account Name", "Balance", "Type"])
        return create_export_response(buffer, f"balance_sheet_{target_date}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        pdf_data = [["Account #", "Account Name", "Balance", "Type"]]
        for row in flat_data:
            pdf_data.append([row["Account Number"], row["Account Name"], row["Balance"], row["Type"]])
            
        buffer = generate_pdf(pdf_data, f"Balance Sheet (As of {target_date})")
        return create_export_response(buffer, f"balance_sheet_{target_date}.pdf", "application/pdf")


@router.get("/accounting/trial-balance/compare", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def compare_trial_balance(
    periods: str = "2025-01-01:2025-12-31,2024-01-01:2024-12-31",
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """مقارنة ميزان المراجعة بين فترات متعددة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        parsed = _parse_periods(periods)
        if len(parsed) < 2:
            raise HTTPException(status_code=400, detail="يجب تحديد فترتين على الأقل")

        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""

        all_accounts = db.execute(text("""
            SELECT id, account_number, name, name_en, account_type, parent_id
            FROM accounts ORDER BY account_number
        """)).fetchall()
        account_list = [dict(r._mapping) for r in all_accounts]

        period_results = []
        for p in parsed:
            params = {"start": p["start"], "end": p["end"]}
            if branch_id:
                params["branch_id"] = branch_id

            balances = db.execute(text(f"""
                SELECT a.id,
                    COALESCE(SUM(jl.debit), 0) as total_debit,
                    COALESCE(SUM(jl.credit), 0) as total_credit
                FROM accounts a
                LEFT JOIN journal_lines jl ON a.id = jl.account_id
                LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
                    AND je.entry_date BETWEEN :start AND :end
                    AND je.status = 'posted' {branch_filter}
                GROUP BY a.id
            """), params).fetchall()
            bal_map = {r.id: {"debit": float(r.total_debit), "credit": float(r.total_credit)} for r in balances}

            accounts_with_bal = []
            sum_debit = 0
            sum_credit = 0
            for a in account_list:
                b = bal_map.get(a["id"], {"debit": 0, "credit": 0})
                accounts_with_bal.append({**a, "debit": b["debit"], "credit": b["credit"]})
                sum_debit += b["debit"]
                sum_credit += b["credit"]

            period_results.append({
                "period": {"start": str(p["start"]), "end": str(p["end"]), "label": p.get("label", "")},
                "accounts": accounts_with_bal,
                "total_debit": sum_debit,
                "total_credit": sum_credit,
            })

        # Build comparison rows
        rows = []
        for a in account_list:
            period_values = []
            has_data = False
            for pr in period_results:
                acc = next((x for x in pr["accounts"] if x["id"] == a["id"]), None)
                if acc and (acc.get("debit", 0) != 0 or acc.get("credit", 0) != 0):
                    has_data = True
                period_values.append({
                    "debit": acc["debit"] if acc else 0,
                    "credit": acc["credit"] if acc else 0,
                })
            if has_data:
                rows.append({
                    "account_id": a["id"],
                    "account_number": a["account_number"],
                    "name": a["name"],
                    "name_en": a.get("name_en"),
                    "account_type": a["account_type"],
                    "periods": period_values,
                })

        return {
            "periods": [pr["period"] for pr in period_results],
            "summary": [{
                "period": pr["period"],
                "total_debit": pr["total_debit"],
                "total_credit": pr["total_credit"],
            } for pr in period_results],
            "comparison": rows,
        }
    finally:
        db.close()


def _parse_periods(periods_str: str):
    """Parse 'start:end,start:end' or 'start:end' strings into list of dicts"""
    result = []
    for part in periods_str.split(","):
        part = part.strip()
        if ":" in part:
            s, e = part.split(":", 1)
            result.append({"start": s.strip(), "end": e.strip()})
        else:
            # Single date: treat as full year
            result.append({"start": f"{part.strip()[:4]}-01-01", "end": part.strip()})
    return result


def _build_comparison_table(account_list, period_results, mode):
    """Build a flat comparison table with all periods side by side"""
    rows = []
    for a in account_list:
        period_values = []
        has_data = False
        for pr in period_results:
            acc = next((x for x in pr["accounts"] if x["id"] == a["id"]), None)
            bal = acc["balance"] if acc else 0
            if bal != 0:
                has_data = True
            period_values.append(bal)
        if has_data:
            # Calculate change between first two periods
            change = period_values[0] - period_values[1] if len(period_values) >= 2 else 0
            change_pct = (change / abs(period_values[1]) * 100) if len(period_values) >= 2 and period_values[1] != 0 else 0

            rows.append({
                "account_id": a["id"],
                "account_number": a["account_number"],
                "name": a["name"],
                "name_en": a.get("name_en"),
                "account_type": a["account_type"],
                "periods": period_values,
                "change": change,
                "change_pct": round(change_pct, 2),
            })
    return rows

# ═══════════════════════════════════════════════════════════
# RPT-101/102: Export Endpoints for All Reports (PDF/Excel)
# ═══════════════════════════════════════════════════════════

@router.get("/accounting/trial-balance/export", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def export_trial_balance(
    format: str = "pdf",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تصدير ميزان المراجعة (PDF/Excel)"""
    branch_id = validate_branch_access(current_user, branch_id)
    s = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today().replace(day=1, month=1)
    e = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
    data = get_trial_balance(start_date=str(s), end_date=str(e), branch_id=branch_id, current_user=current_user)

    flat = []
    for r in data["data"]:
        flat.append({
            "رقم الحساب": r["account_number"], "اسم الحساب": r["name"],
            "رصيد افتتاحي مدين": f"{r['opening_debit']:,.2f}", "رصيد افتتاحي دائن": f"{r['opening_credit']:,.2f}",
            "حركة مدين": f"{r['period_debit']:,.2f}", "حركة دائن": f"{r['period_credit']:,.2f}",
            "رصيد ختامي مدين": f"{r['closing_debit']:,.2f}", "رصيد ختامي دائن": f"{r['closing_credit']:,.2f}",
        })
    cols = ["رقم الحساب", "اسم الحساب", "رصيد افتتاحي مدين", "رصيد افتتاحي دائن", "حركة مدين", "حركة دائن", "رصيد ختامي مدين", "رصيد ختامي دائن"]
    fname = f"trial_balance_{s}_{e}"

    if format == "excel":
        buf = generate_excel(flat, cols, "Trial Balance")
        return create_export_response(buf, f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    buf = generate_pdf([[r.get(c, "") for c in cols] for r in flat], f"Trial Balance ({s} → {e})", cols)
    return create_export_response(buf, f"{fname}.pdf", "application/pdf")


@router.get("/accounting/general-ledger/export", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def export_general_ledger(
    account_id: int,
    format: str = "pdf",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تصدير دفتر الأستاذ لحساب معين"""
    branch_id = validate_branch_access(current_user, branch_id)
    data = get_general_ledger(account_id=account_id, start_date=start_date, end_date=end_date, branch_id=branch_id, current_user=current_user)
    flat = []
    balance = 0.0
    for e_row in data["entries"]:
        balance += e_row["debit"] - e_row["credit"]
        flat.append({
            "التاريخ": e_row["entry_date"], "رقم القيد": e_row["entry_number"],
            "البيان": e_row["description"] or "", "المرجع": e_row["reference"] or "",
            "مدين": f"{e_row['debit']:,.2f}", "دائن": f"{e_row['credit']:,.2f}",
            "الرصيد": f"{balance:,.2f}",
        })
    cols = ["التاريخ", "رقم القيد", "البيان", "المرجع", "مدين", "دائن", "الرصيد"]
    fname = f"general_ledger_{account_id}"

    if format == "excel":
        buf = generate_excel(flat, cols, "General Ledger")
        return create_export_response(buf, f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    buf = generate_pdf([[r.get(c, "") for c in cols] for r in flat], f"General Ledger — Account {account_id}", cols)
    return create_export_response(buf, f"{fname}.pdf", "application/pdf")


@router.get("/accounting/cashflow/export", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def export_cashflow(
    format: str = "pdf",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تصدير تقرير التدفقات النقدية"""
    branch_id = validate_branch_access(current_user, branch_id)
    data = get_cashflow_report(start_date=start_date, end_date=end_date, branch_id=branch_id, current_user=current_user)
    flat = []
    for section_name, section_data in [("Operating", data.get("operating", {})), ("Investing", data.get("investing", {})), ("Financing", data.get("financing", {}))]:
        if isinstance(section_data, dict):
            for k, v in section_data.items():
                if k != "total":
                    flat.append({"Section": section_name, "Item": k, "Amount": f"{float(v or 0):,.2f}"})
            flat.append({"Section": section_name, "Item": "المجموع", "Amount": f"{float(section_data.get('total', 0)):,.2f}"})
    flat.append({"Section": "", "Item": "صافي التغير في النقدية", "Amount": f"{float(data.get('net_change', 0)):,.2f}"})
    cols = ["Section", "Item", "Amount"]
    fname = f"cashflow_{start_date}_{end_date}"
    if format == "excel":
        buf = generate_excel(flat, cols, "Cash Flow")
        return create_export_response(buf, f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    buf = generate_pdf([[r[c] for c in cols] for r in flat], "Cash Flow Statement", cols)
    return create_export_response(buf, f"{fname}.pdf", "application/pdf")


@router.get("/sales/aging/export", dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def export_aging(format: str = "pdf", current_user: dict = Depends(get_current_user)):
    """تصدير تقرير أعمار الديون"""
    data = get_aging_report(current_user=current_user)
    flat = data if isinstance(data, list) else data.get("data", [])
    cols = list(flat[0].keys()) if flat else ["customer", "0-30", "31-60", "61-90", "90+", "total"]
    fname = "aging_report"
    if format == "excel":
        buf = generate_excel(flat, cols, "Aging")
        return create_export_response(buf, f"{fname}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    pdf_rows = [[str(r.get(c, "")) for c in cols] for r in flat]
    buf = generate_pdf(pdf_rows, "Accounts Receivable Aging", cols)
    return create_export_response(buf, f"{fname}.pdf", "application/pdf")


# ═══════════════════════════════════════════════════════════
# RPT-103: Advanced Financial Reports
# ═══════════════════════════════════════════════════════════

@router.get("/accounting/horizontal-analysis", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def horizontal_analysis(
    periods: str = "2026-01-01:2026-12-31,2025-01-01:2025-12-31",
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تحليل أفقي — اتجاه الأرقام عبر الفترات"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    try:
        parsed = _parse_periods(periods)
        if len(parsed) < 2:
            raise HTTPException(status_code=400, detail="يجب فترتين على الأقل")

        branch_filter = "AND je.branch_id = :branch_id" if branch_id else ""

        all_accounts = db.execute(text("SELECT id, account_number, name, name_en, account_type FROM accounts ORDER BY account_number")).fetchall()

        results = []
        for acct in all_accounts:
            a = acct._mapping
            period_balances = []
            for p in parsed:
                params = {"acct": a["id"], "start": p["start"], "end": p["end"]}
                if branch_id:
                    params["branch_id"] = branch_id
                bal = db.execute(text(f"""
                    SELECT COALESCE(SUM(jl.debit - jl.credit), 0) as net
                    FROM journal_lines jl
                    JOIN journal_entries je ON jl.journal_entry_id = je.id
                    WHERE jl.account_id = :acct AND je.entry_date BETWEEN :start AND :end
                      AND je.status = 'posted' {branch_filter}
                """), params).scalar()
                period_balances.append(float(bal))

            if not any(abs(b) > 0.01 for b in period_balances):
                continue

            changes = []
            for i in range(len(period_balances) - 1):
                curr, prev = period_balances[i], period_balances[i + 1]
                abs_change = curr - prev
                pct_change = (abs_change / abs(prev) * 100) if prev != 0 else None
                changes.append({"absolute": round(abs_change, 2), "percentage": round(pct_change, 2) if pct_change is not None else None})

            results.append({
                "account_number": a["account_number"], "name": a["name"],
                "account_type": a["account_type"], "periods": period_balances, "changes": changes,
                "trend": "increasing" if all(period_balances[i] >= period_balances[i+1] for i in range(len(period_balances)-1)) else
                         "decreasing" if all(period_balances[i] <= period_balances[i+1] for i in range(len(period_balances)-1)) else "mixed"
            })

        return {"report_name": "التحليل الأفقي", "periods": [f"{p['start']}→{p['end']}" for p in parsed], "data": results}
    finally:
        db.close()


@router.get("/accounting/financial-ratios", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def financial_ratios(
    as_of_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تحليل النسب المالية — سيولة / ربحية / ملاءة"""
    branch_id = validate_branch_access(current_user, branch_id)
    d = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()
    start_of_year = d.replace(month=1, day=1)
    db = get_db_connection(current_user.company_id)
    try:
        def acct_sum(type_like, start=None, end=None):
            params = {}
            date_filter = ""
            if start and end:
                date_filter = "AND je.entry_date BETWEEN :start AND :end"
                params["start"] = start
                params["end"] = end
            br = "AND je.branch_id = :branch_id" if branch_id else ""
            if branch_id:
                params["branch_id"] = branch_id
            return float(db.execute(text(f"""
                SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                JOIN accounts a ON jl.account_id = a.id
                WHERE a.account_type = :atype AND je.status = 'posted' {date_filter} {br}
            """), {**params, "atype": type_like}).scalar())

        def code_sum(like_pattern, start=None, end=None):
            params = {"p": like_pattern}
            df = ""
            if start and end:
                df = "AND je.entry_date BETWEEN :start AND :end"
                params["start"] = start
                params["end"] = end
            br = "AND je.branch_id = :branch_id" if branch_id else ""
            if branch_id:
                params["branch_id"] = branch_id
            return float(db.execute(text(f"""
                SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                JOIN accounts a ON jl.account_id = a.id
                WHERE a.account_number LIKE :p AND je.status='posted' {df} {br}
            """), params).scalar())

        # Balance Sheet items (cumulative to date)
        total_assets = acct_sum("asset", None, None)
        current_assets = code_sum("11%")
        fixed_assets = code_sum("12%")
        total_liabilities = abs(acct_sum("liability"))
        current_liabilities = abs(code_sum("21%"))
        equity = abs(acct_sum("equity"))

        # P&L items (YTD)
        revenue = abs(acct_sum("revenue", start_of_year, d))
        expenses = acct_sum("expense", start_of_year, d)
        net_income = revenue - expenses
        cogs = code_sum("51%", start_of_year, d)
        gross_profit = revenue - cogs

        # Inventory
        inventory = code_sum("1103%") + code_sum("1103%")  # net balance
        ar = code_sum("1102%")
        ap = abs(code_sum("2101%"))

        # Ratios
        ratios = {
            "liquidity": {
                "current_ratio": round(current_assets / current_liabilities, 2) if current_liabilities else None,
                "quick_ratio": round((current_assets - abs(inventory)) / current_liabilities, 2) if current_liabilities else None,
                "cash_ratio": round(code_sum("1101%") / current_liabilities, 2) if current_liabilities else None,
            },
            "profitability": {
                "gross_profit_margin": round(gross_profit / revenue * 100, 2) if revenue else None,
                "net_profit_margin": round(net_income / revenue * 100, 2) if revenue else None,
                "return_on_assets": round(net_income / total_assets * 100, 2) if total_assets else None,
                "return_on_equity": round(net_income / equity * 100, 2) if equity else None,
            },
            "solvency": {
                "debt_to_equity": round(total_liabilities / equity, 2) if equity else None,
                "debt_to_assets": round(total_liabilities / total_assets, 2) if total_assets else None,
                "equity_ratio": round(equity / total_assets * 100, 2) if total_assets else None,
            },
            "activity": {
                "ar_turnover": round(revenue / ar, 2) if ar else None,
                "ar_days": round(365 / (revenue / ar), 1) if ar and revenue else None,
                "ap_turnover": round(cogs / ap, 2) if ap else None,
                "ap_days": round(365 / (cogs / ap), 1) if ap and cogs else None,
                "inventory_turnover": round(cogs / abs(inventory), 2) if inventory else None,
                "inventory_days": round(365 / (cogs / abs(inventory)), 1) if inventory and cogs else None,
            }
        }

        return {
            "report_name": "تحليل النسب المالية",
            "as_of_date": str(d),
            "summary": {
                "total_assets": round(total_assets, 2), "current_assets": round(current_assets, 2),
                "total_liabilities": round(total_liabilities, 2), "equity": round(equity, 2),
                "revenue_ytd": round(revenue, 2), "net_income_ytd": round(net_income, 2),
            },
            "ratios": ratios,
        }
    finally:
        db.close()


@router.get("/accounting/cost-center-report", dependencies=[Depends(require_permission(["accounting.view", "reports.view"]))])
def cost_center_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير مراكز التكلفة"""
    branch_id = validate_branch_access(current_user, branch_id)
    db = get_db_connection(current_user.company_id)
    s = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today().replace(month=1, day=1)
    e = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
    try:
        params = {"start": s, "end": e}
        br = "AND je.branch_id = :branch_id" if branch_id else ""
        if branch_id:
            params["branch_id"] = branch_id

        rows = db.execute(text(f"""
            SELECT cc.id, cc.name, cc.code,
                   COALESCE(SUM(jl.debit), 0) as total_debit,
                   COALESCE(SUM(jl.credit), 0) as total_credit,
                   COALESCE(SUM(jl.debit - jl.credit), 0) as net
            FROM cost_centers cc
            LEFT JOIN journal_lines jl ON cc.id = jl.cost_center_id
            LEFT JOIN journal_entries je ON jl.journal_entry_id = je.id
                AND je.entry_date BETWEEN :start AND :end AND je.status = 'posted' {br}
            GROUP BY cc.id, cc.name, cc.code
            ORDER BY net DESC
        """), params).fetchall()

        return {
            "report_name": "تقرير مراكز التكلفة",
            "period": {"start": str(s), "end": str(e)},
            "data": [dict(r._mapping) for r in rows],
            "total_net": sum(float(r.net) for r in rows),
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# RPT-104: Inventory Reports
# ═══════════════════════════════════════════════════════════

@router.get("/inventory/valuation", dependencies=[Depends(require_permission(["stock.view", "reports.view"]))])
def inventory_valuation_report(
    warehouse_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقييم المخزون بالتكلفة المتوسطة"""
    db = get_db_connection(current_user.company_id)
    try:
        wh_filter = "AND i.warehouse_id = :wh" if warehouse_id else ""
        params = {}
        if warehouse_id:
            params["wh"] = warehouse_id

        rows = db.execute(text(f"""
            SELECT p.id, p.sku, p.product_name, p.cost_price,
                   COALESCE(SUM(i.quantity), 0) as total_qty,
                   COALESCE(SUM(i.quantity), 0) * COALESCE(p.cost_price, 0) as total_value,
                   w.warehouse_name
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id {wh_filter}
            LEFT JOIN warehouses w ON i.warehouse_id = w.id
            WHERE p.product_type != 'service'
            GROUP BY p.id, p.sku, p.product_name, p.cost_price, w.warehouse_name
            HAVING COALESCE(SUM(i.quantity), 0) != 0
            ORDER BY total_value DESC
        """), params).fetchall()

        items = []
        grand_total = 0.0
        for r in rows:
            m = r._mapping
            val = float(m["total_value"] or 0)
            grand_total += val
            items.append({
                "product_id": m["id"], "sku": m["sku"], "product_name": m["product_name"],
                "warehouse": m["warehouse_name"], "quantity": float(m["total_qty"]),
                "cost_price": float(m["cost_price"] or 0),
                "total_value": round(val, 2),
            })

        return {"report_name": "تقييم المخزون", "items": items, "grand_total": round(grand_total, 2)}
    finally:
        db.close()


@router.get("/inventory/turnover", dependencies=[Depends(require_permission(["stock.view", "reports.view"]))])
def inventory_turnover_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير دوران المخزون"""
    db = get_db_connection(current_user.company_id)
    s = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today().replace(month=1, day=1)
    e = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
    days_in_period = max((e - s).days, 1)
    try:
        rows = db.execute(text("""
            SELECT p.id, p.sku, p.product_name, p.cost_price,
                   COALESCE(SUM(i.quantity), 0) as current_qty,
                   COALESCE(sold.qty, 0) as sold_qty
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN (
                SELECT il.product_id, SUM(ABS(il.quantity)) as qty
                FROM invoice_lines il
                JOIN invoices inv ON il.invoice_id = inv.id
                WHERE inv.invoice_type = 'sales' AND inv.status != 'cancelled'
                  AND inv.invoice_date BETWEEN :start AND :end
                GROUP BY il.product_id
            ) sold ON sold.product_id = p.id
            WHERE p.product_type != 'service'
            GROUP BY p.id, p.sku, p.product_name, p.cost_price, sold.qty
            HAVING COALESCE(SUM(i.quantity), 0) > 0 OR COALESCE(sold.qty, 0) > 0
            ORDER BY sold.qty DESC NULLS LAST
        """), {"start": s, "end": e}).fetchall()

        items = []
        for r in rows:
            m = r._mapping
            avg_inv = float(m["current_qty"] or 0)
            sold = float(m["sold_qty"] or 0)
            cogs_val = sold * float(m["cost_price"] or 0)
            turnover = cogs_val / (avg_inv * float(m["cost_price"] or 1)) if avg_inv > 0 and m["cost_price"] else 0
            days_on_hand = round(days_in_period / turnover, 1) if turnover > 0 else None

            items.append({
                "product_id": m["id"], "sku": m["sku"], "product_name": m["product_name"],
                "current_stock": avg_inv, "sold_qty": sold,
                "cogs_value": round(cogs_val, 2),
                "turnover_ratio": round(turnover, 2),
                "days_on_hand": days_on_hand,
            })

        return {"report_name": "دوران المخزون", "period": {"start": str(s), "end": str(e)}, "items": items}
    finally:
        db.close()


@router.get("/inventory/dead-stock", dependencies=[Depends(require_permission(["stock.view", "reports.view"]))])
def dead_stock_report(
    days_threshold: int = 90,
    current_user: dict = Depends(get_current_user)
):
    """المخزون الراكد — منتجات بدون حركة لفترة محددة"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT p.id, p.sku, p.product_name, p.cost_price,
                   COALESCE(SUM(i.quantity), 0) as stock_qty,
                   COALESCE(SUM(i.quantity), 0) * COALESCE(p.cost_price, 0) as stock_value,
                   MAX(it.created_at) as last_movement
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            LEFT JOIN inventory_transactions it ON p.id = it.product_id
            WHERE p.product_type != 'service'
            GROUP BY p.id, p.sku, p.product_name, p.cost_price
            HAVING COALESCE(SUM(i.quantity), 0) > 0
               AND (MAX(it.created_at) IS NULL OR MAX(it.created_at) < NOW() - :days * INTERVAL '1 day')
            ORDER BY stock_value DESC
        """), {"days": days_threshold}).fetchall()

        items = []
        total_val = 0.0
        for r in rows:
            m = r._mapping
            val = float(m["stock_value"] or 0)
            total_val += val
            items.append({
                "product_id": m["id"], "sku": m["sku"], "product_name": m["product_name"],
                "stock_qty": float(m["stock_qty"]),
                "cost_price": float(m["cost_price"] or 0),
                "stock_value": round(val, 2),
                "last_movement": str(m["last_movement"]) if m["last_movement"] else "لا توجد حركة",
            })

        return {
            "report_name": f"المخزون الراكد (>{days_threshold} يوم)",
            "days_threshold": days_threshold,
            "items": items,
            "total_dead_stock_value": round(total_val, 2),
            "count": len(items),
        }
    finally:
        db.close()


@router.get("/inventory/cogs", dependencies=[Depends(require_permission(["stock.view", "reports.view"]))])
def cogs_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير تكلفة البضاعة المباعة"""
    db = get_db_connection(current_user.company_id)
    s = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today().replace(month=1, day=1)
    e = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
    try:
        rows = db.execute(text("""
            SELECT p.id, p.sku, p.product_name, p.cost_price,
                   SUM(ABS(il.quantity)) as sold_qty,
                   SUM(ABS(il.quantity) * COALESCE(il.unit_cost, p.cost_price, 0)) as cogs_total,
                   SUM(il.quantity * il.unit_price) as revenue_total
            FROM invoice_lines il
            JOIN invoices inv ON il.invoice_id = inv.id
            JOIN products p ON il.product_id = p.id
            WHERE inv.invoice_type = 'sales' AND inv.status != 'cancelled'
              AND inv.invoice_date BETWEEN :start AND :end
            GROUP BY p.id, p.sku, p.product_name, p.cost_price
            ORDER BY cogs_total DESC
        """), {"start": s, "end": e}).fetchall()

        items = []
        total_cogs = 0.0
        total_rev = 0.0
        for r in rows:
            m = r._mapping
            cogs = float(m["cogs_total"] or 0)
            rev = float(m["revenue_total"] or 0)
            gross = rev - cogs
            margin = (gross / rev * 100) if rev > 0 else 0
            total_cogs += cogs
            total_rev += rev
            items.append({
                "product_id": m["id"], "sku": m["sku"], "product_name": m["product_name"],
                "sold_qty": float(m["sold_qty"] or 0),
                "unit_cost": float(m["cost_price"] or 0),
                "cogs": round(cogs, 2), "revenue": round(rev, 2),
                "gross_profit": round(gross, 2), "margin_pct": round(margin, 2),
            })

        return {
            "report_name": "تكلفة البضاعة المباعة",
            "period": {"start": str(s), "end": str(e)},
            "items": items,
            "totals": {"cogs": round(total_cogs, 2), "revenue": round(total_rev, 2),
                       "gross_profit": round(total_rev - total_cogs, 2)},
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# RPT-105: Sales & Purchases Reports
# ═══════════════════════════════════════════════════════════

@router.get("/sales/by-cashier", dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def sales_by_cashier(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير المبيعات حسب البائع/الكاشير"""
    db = get_db_connection(current_user.company_id)
    s = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today().replace(month=1, day=1)
    e = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
    try:
        rows = db.execute(text("""
            SELECT u.id, u.full_name,
                   COUNT(inv.id) as invoice_count,
                   COALESCE(SUM(inv.total), 0) as total_sales,
                   COALESCE(SUM(inv.paid_amount), 0) as total_collected,
                   COALESCE(AVG(inv.total), 0) as avg_invoice
            FROM invoices inv
            JOIN company_users u ON inv.created_by = u.id
            WHERE inv.invoice_type = 'sales' AND inv.status != 'cancelled'
              AND inv.invoice_date BETWEEN :start AND :end
            GROUP BY u.id, u.full_name
            ORDER BY total_sales DESC
        """), {"start": s, "end": e}).fetchall()

        return {
            "report_name": "المبيعات حسب البائع",
            "period": {"start": str(s), "end": str(e)},
            "data": [{
                "user_id": r.id, "name": r.full_name,
                "invoice_count": r.invoice_count,
                "total_sales": round(float(r.total_sales), 2),
                "total_collected": round(float(r.total_collected), 2),
                "avg_invoice": round(float(r.avg_invoice), 2),
            } for r in rows],
        }
    finally:
        db.close()


@router.get("/sales/target-vs-actual", dependencies=[Depends(require_permission(["sales.reports", "reports.view"]))])
def sales_target_vs_actual(
    year: int = None,
    current_user: dict = Depends(get_current_user)
):
    """تقرير المبيعات المستهدفة vs الفعلية (شهري)"""
    db = get_db_connection(current_user.company_id)
    yr = year or date.today().year
    try:
        # Get monthly targets if exist
        targets = {}
        try:
            tgt_rows = db.execute(text(
                "SELECT month_number, target_amount FROM sales_targets WHERE year = :y"
            ), {"y": yr}).fetchall()
            for t in tgt_rows:
                targets[t.month_number] = float(t.target_amount)
        except Exception:
            pass  # Table may not exist

        # Actual monthly sales
        actuals = db.execute(text("""
            SELECT EXTRACT(MONTH FROM invoice_date)::int as month,
                   COALESCE(SUM(total), 0) as actual
            FROM invoices
            WHERE invoice_type = 'sales' AND status != 'cancelled'
              AND EXTRACT(YEAR FROM invoice_date) = :y
            GROUP BY month
            ORDER BY month
        """), {"y": yr}).fetchall()

        actual_map = {r.month: float(r.actual) for r in actuals}

        months = []
        for m in range(1, 13):
            target = targets.get(m, 0)
            actual = actual_map.get(m, 0)
            variance = actual - target
            pct = (actual / target * 100) if target > 0 else None
            months.append({
                "month": m, "target": round(target, 2), "actual": round(actual, 2),
                "variance": round(variance, 2), "achievement_pct": round(pct, 2) if pct is not None else None,
            })

        return {"report_name": "المبيعات المستهدفة vs الفعلية", "year": yr, "months": months}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Custom Report Builder
# ═══════════════════════════════════════════════════════════

class CustomReportConfig(BaseModel):
    source: str # 'sales', 'purchases', 'inventory', 'projects'
    columns: List[str]
    filters: Optional[Dict[str, Any]] = {}
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "desc"

class CustomReportCreate(BaseModel):
    report_name: str
    description: Optional[str] = None
    config: CustomReportConfig

@router.post("/custom/preview", dependencies=[Depends(require_permission("reports.view"))])
async def preview_custom_report(
    config: CustomReportConfig,
    current_user: dict = Depends(get_current_user)
):
    """معاينة تقرير مخصص بناءً على التكوين"""
    db = get_db_connection(current_user.company_id)
    try:
        data = _generate_custom_report_data(db, config, current_user.id)
        return data
    except Exception as e:
        logger.error(f"Error previewing report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/custom", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("reports.create"))])
async def create_custom_report(
    report: CustomReportCreate,
    current_user: dict = Depends(get_current_user)
):
    """حفظ تقرير مخصص"""
    db = get_db_connection(current_user.company_id)
    try:
        report_id = db.execute(text("""
            INSERT INTO custom_reports (
                report_name, description, config, created_by
            ) VALUES (:name, :desc, :config, :uid)
            RETURNING id
        """), {
            "name": report.report_name,
            "desc": report.description,
            "config": report.config.json(),
            "uid": current_user.id
        }).scalar()
        
        db.commit()
        return {"success": True, "id": report_id, "message": "تم حفظ التقرير بنجاح"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/custom", dependencies=[Depends(require_permission("reports.view"))])
async def list_custom_reports(current_user: dict = Depends(get_current_user)):
    """جلب قائمة التقارير المخصصة المحفوظة"""
    db = get_db_connection(current_user.company_id)
    try:
        reports = db.execute(text("""
            SELECT cr.*, u.full_name as created_by_name
            FROM custom_reports cr
            LEFT JOIN company_users u ON cr.created_by = u.id
            ORDER BY cr.created_at DESC
        """)).fetchall()
        return [dict(r._mapping) for r in reports]
    finally:
        db.close()

@router.get("/custom/{report_id}", dependencies=[Depends(require_permission("reports.view"))])
async def get_custom_report(report_id: int, current_user: dict = Depends(get_current_user)):
    """تشغيل تقرير مخصص محفوظ"""
    db = get_db_connection(current_user.company_id)
    try:
        report = db.execute(text("SELECT * FROM custom_reports WHERE id = :id"), {"id": report_id}).fetchone()
        if not report:
            raise HTTPException(status_code=404, detail="التقرير غير موجود")
            
        config_dict = report.config if isinstance(report.config, dict) else json.loads(report.config)
        config = CustomReportConfig(**config_dict)
        
        data = _generate_custom_report_data(db, config, current_user.id)
        return {"report": dict(report._mapping), "results": data}
    except Exception as e:
        logger.error(f"Error executing saved report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.delete("/custom/{report_id}", dependencies=[Depends(require_permission("reports.delete"))])
async def delete_custom_report(report_id: int, current_user: dict = Depends(get_current_user)):
    """حذف تقرير مخصص"""
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM custom_reports WHERE id = :id"), {"id": report_id})
        db.commit()
        return {"success": True, "message": "تم حذف التقرير"}
    finally:
        db.close()

def _generate_custom_report_data(db, config: CustomReportConfig, user_id: int):
    """Engine to build dynamic SQL based on config"""
    import json
    
    # 1. Source Mapping
    source_map = {
        "sales": {
            "table": "invoices",
            "alias": "i",
            "joins": "LEFT JOIN parties p ON i.party_id = p.id",
            "where": "i.invoice_type = 'sales' AND i.status != 'cancelled'",
            "columns": {
                "invoice_number": "i.invoice_number",
                "date": "i.invoice_date",
                "customer": "p.name",
                "total": "i.total",
                "paid": "i.paid_amount",
                "status": "i.status",
                "branch_id": "i.branch_id"
            }
        },
        "purchases": {
            "table": "invoices",
            "alias": "i",
            "joins": "LEFT JOIN parties p ON i.party_id = p.id",
            "where": "i.invoice_type = 'purchase' AND i.status != 'cancelled'",
            "columns": {
                "invoice_number": "i.invoice_number",
                "date": "i.invoice_date",
                "supplier": "p.name",
                "total": "i.total",
                "paid": "i.paid_amount",
                "status": "i.status"
            }
        },
        "inventory": {
            "table": "products",
            "alias": "p",
            "joins": "LEFT JOIN inventory inv ON p.id = inv.product_id LEFT JOIN warehouses w ON inv.warehouse_id = w.id",
            "where": "1=1",
            "columns": {
                "sku": "p.sku",
                "product_name": "p.product_name",
                "warehouse": "w.warehouse_name",
                "quantity": "inv.quantity",
                "cost_price": "p.cost_price",
                "selling_price": "p.selling_price"
            }
        },
         "projects": {
            "table": "projects",
            "alias": "p",
            "joins": "LEFT JOIN customers c ON p.customer_id = c.id LEFT JOIN employees e ON p.manager_id = e.id",
            "where": "1=1",
            "columns": {
                "code": "p.project_code",
                "project_name": "p.project_name",
                "customer": "c.customer_name",
                "manager": "CONCAT(e.first_name, ' ', e.last_name)",
                "status": "p.status",
                "progress": "p.progress_percentage"
            }
        }
    }
    
    src = source_map.get(config.source)
    if not src:
        raise ValueError("Invalid Data Source")
        
    # 2. Build Query
    select_cols = []
    for col in config.columns:
        if col in src["columns"]:
            select_cols.append(f"{src['columns'][col]} as {col}")
    
    if not select_cols:
        select_cols = ["*"] # Fallback
        
    query = f"SELECT {', '.join(select_cols)} FROM {src['table']} {src['alias']} {src['joins']} WHERE {src['where']}"
    
    # 3. Apply Filters
    params = {}
    if config.filters:
        for key, value in config.filters.items():
            if key in src["columns"] and value:
                valid_key = key.replace(" ", "_") # Safety
                query += f" AND {src['columns'][key]} = :{valid_key}"
                params[valid_key] = value
                
            # Date Range special handling
            if key == "date_from" and "date" in src["columns"]:
                 query += f" AND {src['columns']['date']} >= :date_from"
                 params["date_from"] = value
            if key == "date_to" and "date" in src["columns"]:
                 query += f" AND {src['columns']['date']} <= :date_to"
                 params["date_to"] = value

    # 4. Sorting
    if config.sort_by and config.sort_by in src["columns"]:
        order = "DESC" if config.sort_order == "desc" else "ASC"
        query += f" ORDER BY {src['columns'][config.sort_by]} {order}"
    
    # Execute
    result = db.execute(text(query), params).fetchall()
    return [dict(r._mapping) for r in result]
