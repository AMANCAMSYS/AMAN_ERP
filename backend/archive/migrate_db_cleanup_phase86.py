"""
Phase 8.6 — Database Cleanup Migration
DB-101: Remove deprecated customer_id/supplier_id columns (add party_id where missing)
DB-102: Fix references (projects, pos_orders)
DB-103: Clean legacy tables (keep customers/suppliers for reference but add views)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from config import settings


def get_company_ids():
    root_url = settings.get_company_database_url("postgres").replace("/aman_postgres", "/postgres")
    engine = create_engine(root_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT datname FROM pg_database WHERE datname LIKE 'aman_%' AND datistemplate = false"
        ))
        ids = [row[0].replace("aman_", "") for row in result]
    engine.dispose()
    return ids


def col_exists(conn, table, column):
    r = conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = :t AND column_name = :c
    """), {"t": table, "c": column}).fetchone()
    return r is not None


def table_exists(conn, table):
    r = conn.execute(text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = :t
    """), {"t": table}).fetchone()
    return r is not None


def migrate_company(company_id):
    db_url = settings.get_company_database_url(company_id)
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()
    changes = []

    try:
        # --- DB-102: Fix projects.customer_id → party_id ---
        if table_exists(conn, "projects"):
            if col_exists(conn, "projects", "customer_id") and not col_exists(conn, "projects", "party_id"):
                conn.execute(text("ALTER TABLE projects ADD COLUMN party_id INTEGER"))
                # Copy data from customer_id to party_id (customers might map to parties)
                # Try to find matching party for each customer
                conn.execute(text("""
                    UPDATE projects p SET party_id = (
                        SELECT pa.id FROM parties pa
                        JOIN customers c ON (c.customer_name = pa.name OR c.email = pa.email)
                        WHERE c.id = p.customer_id
                        LIMIT 1
                    ) WHERE p.customer_id IS NOT NULL AND p.party_id IS NULL
                """))
                # Direct match if customer_id = party_id (common case)
                conn.execute(text("""
                    UPDATE projects SET party_id = customer_id
                    WHERE party_id IS NULL AND customer_id IS NOT NULL
                    AND EXISTS (SELECT 1 FROM parties WHERE id = projects.customer_id)
                """))
                changes.append("projects: added party_id, migrated from customer_id")
            elif col_exists(conn, "projects", "customer_id") and col_exists(conn, "projects", "party_id"):
                # Both columns exist — just ensure party_id is populated
                conn.execute(text("""
                    UPDATE projects SET party_id = customer_id
                    WHERE party_id IS NULL AND customer_id IS NOT NULL
                    AND EXISTS (SELECT 1 FROM parties WHERE id = projects.customer_id)
                """))
                changes.append("projects: synced party_id from customer_id")

        # --- DB-102: Fix pos_orders.customer_id → party_id ---
        if table_exists(conn, "pos_orders"):
            if col_exists(conn, "pos_orders", "customer_id") and not col_exists(conn, "pos_orders", "party_id"):
                conn.execute(text("ALTER TABLE pos_orders ADD COLUMN party_id INTEGER"))
                conn.execute(text("""
                    UPDATE pos_orders SET party_id = customer_id
                    WHERE party_id IS NULL AND customer_id IS NOT NULL
                    AND EXISTS (SELECT 1 FROM parties WHERE id = pos_orders.customer_id)
                """))
                changes.append("pos_orders: added party_id, migrated from customer_id")
            elif col_exists(conn, "pos_orders", "customer_id") and col_exists(conn, "pos_orders", "party_id"):
                conn.execute(text("""
                    UPDATE pos_orders SET party_id = customer_id
                    WHERE party_id IS NULL AND customer_id IS NOT NULL
                    AND EXISTS (SELECT 1 FROM parties WHERE id = pos_orders.customer_id)
                """))
                changes.append("pos_orders: synced party_id from customer_id")

        # --- DB-101: Ensure invoices has deprecated columns marked ---
        # invoices already has party_id + customer_id + supplier_id
        # We keep them for backward compatibility but ensure party_id is always populated
        if table_exists(conn, "invoices"):
            if col_exists(conn, "invoices", "customer_id") and col_exists(conn, "invoices", "party_id"):
                updated = conn.execute(text("""
                    UPDATE invoices SET party_id = customer_id
                    WHERE party_id IS NULL AND customer_id IS NOT NULL
                    AND EXISTS (SELECT 1 FROM parties WHERE id = invoices.customer_id)
                """)).rowcount
                if updated:
                    changes.append(f"invoices: synced {updated} rows customer_id → party_id")

            if col_exists(conn, "invoices", "supplier_id") and col_exists(conn, "invoices", "party_id"):
                updated = conn.execute(text("""
                    UPDATE invoices SET party_id = supplier_id
                    WHERE party_id IS NULL AND supplier_id IS NOT NULL
                    AND EXISTS (SELECT 1 FROM parties WHERE id = invoices.supplier_id)
                """)).rowcount
                if updated:
                    changes.append(f"invoices: synced {updated} rows supplier_id → party_id")

        # --- DB-101: sales_orders, sales_quotations, sales_returns, purchase_orders, purchase_invoices ---
        for tbl in ["sales_orders", "sales_quotations", "sales_returns", "purchase_orders", "purchase_invoices", "payment_vouchers"]:
            if not table_exists(conn, tbl):
                continue
            for old_col in ["customer_id", "supplier_id"]:
                if col_exists(conn, tbl, old_col) and col_exists(conn, tbl, "party_id"):
                    updated = conn.execute(text(f"""
                        UPDATE {tbl} SET party_id = {old_col}
                        WHERE party_id IS NULL AND {old_col} IS NOT NULL
                        AND EXISTS (SELECT 1 FROM parties WHERE id = {tbl}.{old_col})
                    """)).rowcount
                    if updated:
                        changes.append(f"{tbl}: synced {updated} rows {old_col} → party_id")
                elif col_exists(conn, tbl, old_col) and not col_exists(conn, tbl, "party_id"):
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN party_id INTEGER"))
                    conn.execute(text(f"""
                        UPDATE {tbl} SET party_id = {old_col}
                        WHERE {old_col} IS NOT NULL
                        AND EXISTS (SELECT 1 FROM parties WHERE id = {tbl}.{old_col})
                    """))
                    changes.append(f"{tbl}: added party_id, migrated from {old_col}")

        # --- DB-103: Create views for legacy tables (don't drop, just create views for compatibility) ---
        if table_exists(conn, "parties"):
            # Create or replace customer_view and supplier_view
            conn.execute(text("""
                CREATE OR REPLACE VIEW customer_view AS
                SELECT id, party_code as customer_code, name as customer_name, 
                       name_en as customer_name_en, email, phone, mobile,
                       address, city, country, tax_number, credit_limit, 
                       current_balance, status, branch_id, created_at
                FROM parties WHERE is_customer = TRUE
            """))
            conn.execute(text("""
                CREATE OR REPLACE VIEW supplier_view AS
                SELECT id, party_code as supplier_code, name as supplier_name,
                       name_en as supplier_name_en, email, phone, mobile,
                       address, city, country, tax_number, credit_limit,
                       current_balance, status, branch_id, created_at
                FROM parties WHERE is_supplier = TRUE
            """))
            changes.append("Created customer_view and supplier_view from parties")

        # --- DB-103: Migrate any remaining data from customers/suppliers → parties ---
        if table_exists(conn, "customers") and table_exists(conn, "parties"):
            migrated = conn.execute(text("""
                INSERT INTO parties (name, name_en, email, phone, mobile, address, city, country,
                                     tax_number, is_customer, is_supplier, status, branch_id)
                SELECT c.customer_name, c.customer_name_en, c.email, c.phone, c.mobile, c.address,
                       c.city, c.country, c.tax_number, TRUE, FALSE, c.status, c.branch_id
                FROM customers c
                WHERE NOT EXISTS (
                    SELECT 1 FROM parties p 
                    WHERE p.name = c.customer_name 
                    OR (p.email = c.email AND c.email IS NOT NULL AND c.email != '')
                )
            """)).rowcount
            if migrated:
                changes.append(f"Migrated {migrated} customers → parties")

        if table_exists(conn, "suppliers") and table_exists(conn, "parties"):
            migrated = conn.execute(text("""
                INSERT INTO parties (name, name_en, email, phone, mobile, address, city, country,
                                     tax_number, is_customer, is_supplier, status, branch_id)
                SELECT s.supplier_name, s.supplier_name_en, s.email, s.phone, s.mobile, s.address,
                       s.city, s.country, s.tax_number, FALSE, TRUE, s.status, s.branch_id
                FROM suppliers s
                WHERE NOT EXISTS (
                    SELECT 1 FROM parties p
                    WHERE p.name = s.supplier_name
                    OR (p.email = s.email AND s.email IS NOT NULL AND s.email != '')
                )
            """)).rowcount
            if migrated:
                changes.append(f"Migrated {migrated} suppliers → parties")

        trans.commit()
        print(f"  [{company_id}] OK — {len(changes)} changes: {'; '.join(changes) if changes else 'already clean'}")

    except Exception as e:
        trans.rollback()
        print(f"  [{company_id}] ERROR: {e}")
    finally:
        conn.close()
        engine.dispose()


if __name__ == "__main__":
    companies = get_company_ids()
    print(f"=== Phase 8.6 DB Cleanup — {len(companies)} companies ===")
    for cid in companies:
        migrate_company(cid)
    print("=== Done ===")
