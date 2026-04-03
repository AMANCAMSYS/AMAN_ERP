import sys
sys.path.append("/home/omar/Desktop/aman/backend")
from database import _get_engine
from sqlalchemy import text

company_id = "eaed4032"
engine = _get_engine(company_id)
with engine.connect() as db:
    branch_id = 1
    params_cash = {"branch_id": branch_id}
    
    try:
        low_stock_query = """
            SELECT COUNT(*) FROM (
                SELECT p.id
                FROM products p
                LEFT JOIN (
                    SELECT product_id, SUM(quantity) as total_qty 
                    FROM inventory inv
                    JOIN warehouses w ON inv.warehouse_id = w.id
                    WHERE w.branch_id = :branch_id
                    GROUP BY product_id
                ) inv_sum ON p.id = inv_sum.product_id
                WHERE (COALESCE(inv_sum.total_qty, 0) <= p.reorder_level)
                OR (p.reorder_level = 0 AND COALESCE(inv_sum.total_qty, 0) <= 5)
            ) as low_stock_items
        """
        db.execute(text(low_stock_query), params_cash)
        print("low_stock_query OK")
    except Exception as e:
        print("low_stock_query error:", str(e).split('\n')[0])
        db.rollback()

    try:
        reserved_stock_query = """
            SELECT p.product_name, SUM(inv.reserved_quantity) as reserved_qty
            FROM inventory inv
            JOIN products p ON inv.product_id = p.id
            JOIN warehouses w ON inv.warehouse_id = w.id
            WHERE inv.reserved_quantity > 0
            AND w.branch_id = :branch_id
            GROUP BY p.product_name
        """
        db.execute(text(reserved_stock_query), params_cash)
        print("reserved_stock_query OK")
    except Exception as e:
        print("reserved_stock_query error:", str(e).split('\n')[0])
        db.rollback()

    try:
        branch_filter_je = "AND je.branch_id = :branch_id"
        db.execute(text(f"""
            SELECT COALESCE(SUM(jl.credit - jl.debit), 0)
            FROM journal_lines jl
            JOIN journal_entries je ON jl.journal_entry_id = je.id
            JOIN accounts a ON jl.account_id = a.id
            WHERE a.account_type = 'revenue' {branch_filter_je}
        """), params_cash)
        print("calculate_period_stats OK")
    except Exception as e:
        print("calculate_period_stats error:", str(e).split('\n')[0])
        db.rollback()
        
    try:
        cash_sql = """
            SELECT COALESCE(SUM(a.balance), 0) 
            FROM treasury_accounts ta
            JOIN accounts a ON ta.gl_account_id = a.id
            WHERE ta.is_active = TRUE AND ta.branch_id = :branch_id
        """
        db.execute(text(cash_sql), params_cash)
        print("cash_sql OK")
    except Exception as e:
        print("cash_sql error:", str(e).split('\n')[0])
        db.rollback()
