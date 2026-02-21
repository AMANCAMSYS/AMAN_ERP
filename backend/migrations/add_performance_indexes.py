"""
Migration: Performance Indexes & Cascade Fixes
- Composite indexes on most-queried columns (20 indexes)
- pg_trgm GIN indexes for fast text search (11 indexes)  
- ON DELETE CASCADE on critical FK relationships
"""

from sqlalchemy import text
import logging

logger = logging.getLogger("aman.migration.indexes")


COMPOSITE_INDEXES = [
    # Journal entries — most queried table
    ("idx_journal_entries_status_date", "journal_entries", "(status, entry_date)"),
    ("idx_journal_entries_branch_status", "journal_entries", "(branch_id, status)"),
    ("idx_journal_lines_entry_account", "journal_lines", "(journal_entry_id, account_id)"),
    
    # Invoices — heavy filtering by type+status
    ("idx_invoices_type_status", "invoices", "(invoice_type, status)"),
    ("idx_invoices_party_type", "invoices", "(party_id, invoice_type)"),
    
    # Employees & HR
    ("idx_employees_user_id", "employees", "(user_id)"),
    ("idx_leave_requests_emp_status", "leave_requests", "(employee_id, status)"),
    ("idx_employee_loans_emp_status", "employee_loans", "(employee_id, status)"),
    ("idx_attendance_emp_date", "attendance", "(employee_id, date)"),
    
    # POS — real-time queries
    ("idx_pos_sessions_user_status", "pos_sessions", "(user_id, status)"),
    ("idx_pos_orders_session_status", "pos_orders", "(session_id, status)"),
    
    # Checks — status+due_date for aging reports
    ("idx_checks_recv_status_due", "checks_receivable", "(status, due_date)"),
    ("idx_checks_pay_status_due", "checks_payable", "(status, due_date)"),
    
    # Projects
    ("idx_project_expenses_proj_status", "project_expenses", "(project_id, status)"),
    ("idx_project_revenues_proj_status", "project_revenues", "(project_id, status)"),
    
    # Notifications — polled frequently
    ("idx_notifications_user_read", "notifications", "(user_id, is_read)"),
    
    # Other high-frequency tables
    ("idx_approval_requests_wf_status", "approval_requests", "(workflow_id, status)"),
    ("idx_accounts_code_active", "accounts", "(account_code, is_active)"),
    ("idx_production_orders_status", "production_orders", "(status)"),
    ("idx_contracts_status_end", "contracts", "(status, end_date)"),
    ("idx_user_branches_user", "user_branches", "(user_id)"),
    ("idx_tax_returns_status_due", "tax_returns", "(status, due_date)"),
]


TRGM_INDEXES = [
    # Accounts — searched by name in Arabic/English
    ("idx_accounts_name_trgm", "accounts", "name"),
    ("idx_accounts_name_en_trgm", "accounts", "name_en"),
    
    # Parties — customer/supplier search
    ("idx_parties_name_trgm", "parties", "name"),
    
    # Products — POS barcode/name lookup
    ("idx_products_name_trgm", "products", "product_name"),
    ("idx_products_code_trgm", "products", "product_code"),
    
    # Journal entries — search by number/description
    ("idx_je_number_trgm", "journal_entries", "entry_number"),
    ("idx_je_desc_trgm", "journal_entries", "description"),
    
    # Invoices
    ("idx_invoices_number_trgm", "invoices", "invoice_number"),
    
    # Expenses
    ("idx_expenses_desc_trgm", "expenses", "description"),
    
    # Checks
    ("idx_checks_recv_num_trgm", "checks_receivable", "check_number"),
    ("idx_checks_pay_num_trgm", "checks_payable", "check_number"),
]


# FKs that should have ON DELETE CASCADE but currently don't
# Format: (child_table, fk_column, parent_table, parent_column)
CASCADE_FIXES = [
    # Attendance/Leave/Loans → employees (if employee deleted, records should go)
    ("attendance", "employee_id", "employees", "id"),
    ("leave_requests", "employee_id", "employees", "id"),
    ("employee_loans", "employee_id", "employees", "id"),
    
    # POS loyalty chain
    ("pos_loyalty_points", "program_id", "pos_loyalty_programs", "id"),
    ("pos_loyalty_transactions", "loyalty_id", "pos_loyalty_points", "id"),
    ("pos_table_orders", "table_id", "pos_tables", "id"),
    
    # Job applications → job openings
    ("job_applications", "opening_id", "job_openings", "id"),
]


def run_migration(db):
    """Run all index and cascade migrations on a single company DB."""
    stats = {"composite": 0, "trgm": 0, "cascade": 0, "skipped": 0, "errors": []}

    # 1. Create composite indexes
    for idx_name, table, columns in COMPOSITE_INDEXES:
        try:
            # Check if table exists first
            exists = db.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
            ), {"t": table}).fetchone()
            if not exists:
                stats["skipped"] += 1
                continue

            db.execute(text(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} {columns}"
            ))
            stats["composite"] += 1
        except Exception as e:
            stats["errors"].append(f"Composite {idx_name}: {e}")

    # 2. Enable pg_trgm extension and create GIN indexes
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    except Exception as e:
        stats["errors"].append(f"pg_trgm extension: {e}")

    for idx_name, table, column in TRGM_INDEXES:
        try:
            exists = db.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
            ), {"t": table}).fetchone()
            if not exists:
                stats["skipped"] += 1
                continue

            # Check column exists
            col_exists = db.execute(text(
                "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
            ), {"t": table, "c": column}).fetchone()
            if not col_exists:
                stats["skipped"] += 1
                continue

            db.execute(text(
                f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} USING gin ({column} gin_trgm_ops)"
            ))
            stats["trgm"] += 1
        except Exception as e:
            stats["errors"].append(f"Trgm {idx_name}: {e}")

    # 3. Fix ON DELETE CASCADE on critical FKs
    for child_table, fk_col, parent_table, parent_col in CASCADE_FIXES:
        try:
            # Check both tables exist
            for t in (child_table, parent_table):
                t_exists = db.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
                ), {"t": t}).fetchone()
                if not t_exists:
                    stats["skipped"] += 1
                    break
            else:
                # Check FK column exists
                col_exists = db.execute(text(
                    "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
                ), {"t": child_table, "c": fk_col}).fetchone()
                if not col_exists:
                    stats["skipped"] += 1
                    continue

                # Drop old FK constraint if exists, then add with CASCADE
                constraint_name = f"fk_{child_table}_{fk_col}_cascade"
                
                # Find the existing FK constraint name
                old_fk = db.execute(text("""
                    SELECT tc.constraint_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_name = :child
                      AND kcu.column_name = :col
                      AND ccu.table_name = :parent
                """), {"child": child_table, "col": fk_col, "parent": parent_table}).fetchone()

                if old_fk:
                    db.execute(text(
                        f"ALTER TABLE {child_table} DROP CONSTRAINT {old_fk[0]}"
                    ))
                
                db.execute(text(f"""
                    ALTER TABLE {child_table} 
                    ADD CONSTRAINT {constraint_name}
                    FOREIGN KEY ({fk_col}) REFERENCES {parent_table}({parent_col})
                    ON DELETE CASCADE
                """))
                stats["cascade"] += 1
        except Exception as e:
            stats["errors"].append(f"Cascade {child_table}.{fk_col}: {e}")

    db.commit()
    return stats


def migrate_all_companies():
    """Run migration for all company databases."""
    from database import get_system_db, get_db_connection

    system_db = get_system_db()
    try:
        rows = system_db.execute(text(
            "SELECT database_name FROM system_companies WHERE status = 'active'"
        )).fetchall()
        companies = [r[0].replace('aman_', '') for r in rows]
    finally:
        system_db.close()

    print(f"\n{'='*60}")
    print(f"  Performance Indexes & Cascade Migration")
    print(f"  Companies to process: {len(companies)}")
    print(f"{'='*60}\n")

    for cid in companies:
        print(f"  Processing {cid}...", end=" ")
        try:
            db = get_db_connection(cid)
            stats = run_migration(db)
            db.close()
            print(f"✓ composite={stats['composite']} trgm={stats['trgm']} cascade={stats['cascade']} skip={stats['skipped']}")
            if stats["errors"]:
                for err in stats["errors"]:
                    print(f"    ⚠ {err}")
        except Exception as e:
            print(f"✗ {e}")

    print(f"\n{'='*60}")
    print(f"  Migration complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    migrate_all_companies()
