import os
import sys
from dotenv import load_dotenv

load_dotenv("/home/omar/Desktop/aman/backend/.env")

sys.path.append("/home/omar/Desktop/aman/backend")
from database import _get_engine
from sqlalchemy import text
from datetime import date, timedelta
from decimal import Decimal

# Test against first active company
company_id = "ae4e964a"
try:
    engine = _get_engine(company_id)
    with engine.connect() as db:
        print("Connected")
        branch_id = 1
        
        branch_filter_cash = ""
        params_cash = {}
        if branch_id:
            branch_filter_cash = "AND branch_id = :branch_id"
            params_cash["branch_id"] = branch_id

        # Low Stock
        low_stock_query = f"""
            SELECT COUNT(*) FROM (
                SELECT p.id
                FROM products p
                LEFT JOIN (
                    SELECT product_id, SUM(quantity) as total_qty 
                    FROM inventory inv
                    {"JOIN warehouses w ON inv.warehouse_id = w.id" if branch_id else ""}
                    {"WHERE w.branch_id = :branch_id" if branch_id else ""}
                    GROUP BY product_id
                ) inv_sum ON p.id = inv_sum.product_id
                WHERE (COALESCE(inv_sum.total_qty, 0) <= p.reorder_level)
                OR (p.reorder_level = 0 AND COALESCE(inv_sum.total_qty, 0) <= 5)
            ) as low_stock_items
        """
        try:
            low_stock = db.execute(text(low_stock_query), params_cash).scalar() or 0
            print("low_stock_query SUCCESS", low_stock)
        except Exception as e:
            print("low_stock_query FAIL", e)

        # Reserved Stock
        reserved_stock_query = f"""
            SELECT p.product_name, SUM(inv.reserved_quantity) as reserved_qty
            FROM inventory inv
            JOIN products p ON inv.product_id = p.id
            {"JOIN warehouses w ON inv.warehouse_id = w.id" if branch_id else ""}
            WHERE inv.reserved_quantity > 0
            {"AND w.branch_id = :branch_id" if branch_id else ""}
            GROUP BY p.product_name
        """
        try:
            db.execute(text(reserved_stock_query), params_cash).fetchall()
            print("reserved_stock_query SUCCESS")
        except Exception as e:
            print("reserved_stock_query FAIL", e)

        # Calculate Period Stats
        try:
            start_dt = None
            end_dt = None
            branch_filter_je = "AND je.branch_id = :branch_id"
            date_filter_je = ""
            params_gl = {"branch_id": branch_id}
            
            total_income = db.execute(text(f"""
                SELECT COALESCE(SUM(jl.credit - jl.debit), 0)
                FROM journal_lines jl
                JOIN journal_entries je ON jl.journal_entry_id = je.id
                JOIN accounts a ON jl.account_id = a.id
                WHERE a.account_type = 'revenue' {branch_filter_je} {date_filter_je}
            """), params_gl).scalar() or 0
            print("total_income SUCCESS", total_income)
            
            treasury_ids = [row[0] for row in db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE is_active = true")).fetchall() if row[0]]
            legacy_ids = [row[0] for row in db.execute(text("SELECT id FROM accounts WHERE account_code LIKE 'BOX%' OR account_code LIKE 'BNK%'")).fetchall()]
            all_cash_ids = list(set(treasury_ids + legacy_ids))
            cash_balance = 0
            if all_cash_ids:
                id_params = {f"cid_{i}": cid for i, cid in enumerate(all_cash_ids)}
                id_placeholders = ", ".join(f":cid_{i}" for i in range(len(all_cash_ids)))
                cash_balance = db.execute(text(f"""
                    SELECT COALESCE(SUM(jl.debit - jl.credit), 0)
                    FROM journal_lines jl
                    JOIN journal_entries je ON jl.journal_entry_id = je.id
                    JOIN accounts a ON jl.account_id = a.id
                    WHERE a.id IN ({id_placeholders})
                    {branch_filter_je} {date_filter_je}
                """), {**params_gl, **id_params}).scalar() or 0
            print("cash_balance SUCCESS", cash_balance)
        except Exception as e:
            print("calculate_period_stats FAIL", e)

        # Cash
        try:
            cash_sql = f"""
                SELECT COALESCE(SUM(a.balance), 0) 
                FROM treasury_accounts ta
                JOIN accounts a ON ta.gl_account_id = a.id
                WHERE ta.is_active = TRUE {branch_filter_cash.replace('branch_id =', 'ta.branch_id =')}
            """
            cash = db.execute(text(cash_sql), params_cash).scalar() or 0
            print("cash_sql SUCCESS", cash)
        except Exception as e:
            print("cash_sql FAIL", e)
            
except Exception as e:
    print("General exception", e)
