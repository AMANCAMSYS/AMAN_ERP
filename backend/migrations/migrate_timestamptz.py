"""
Migration: TIMESTAMP → TIMESTAMPTZ
Converts all naive TIMESTAMP columns to TIMESTAMPTZ (UTC-aware).
Existing values are treated as UTC (AT TIME ZONE 'UTC').
Run once on all companies.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_system_db, get_db_connection
from sqlalchemy import text

# Tables and their TIMESTAMP columns to migrate
MIGRATIONS = [
    ("journal_entries",    ["created_at", "updated_at", "posted_at"]),
    ("invoices",           ["created_at", "updated_at"]),
    ("purchase_orders",    ["created_at", "updated_at"]),
    ("sales_orders",       ["created_at", "updated_at"]),
    ("payments",           ["created_at", "updated_at"]),
    ("expenses",           ["created_at", "updated_at"]),
    ("notifications",      ["created_at"]),
    ("audit_logs",         ["created_at"]),
    ("company_users",      ["created_at", "updated_at"]),
    ("branches",           ["created_at", "updated_at"]),
    ("inventory_movements",["created_at"]),
    ("manufacturing_orders",["created_at", "updated_at"]),
    ("hr_employees",       ["created_at", "updated_at"]),
    ("payroll_records",    ["created_at", "updated_at"]),
    ("token_blacklist",    ["blacklisted_at", "expires_at"]),
    ("recurring_journals", ["created_at", "updated_at", "last_generated_at", "next_run_date"]),
    ("scheduled_reports",  ["created_at", "last_run_at", "next_run_at"]),
    ("pos_sessions",       ["opened_at", "closed_at"]),
    ("pos_transactions",   ["created_at"]),
    ("contracts",          ["created_at", "updated_at"]),
    ("projects",           ["created_at", "updated_at"]),
    ("assets",             ["created_at", "updated_at", "purchase_date", "disposal_date"]),
    ("checks",             ["created_at", "updated_at"]),
    ("bank_reconciliations",["created_at", "updated_at"]),
]


def migrate_company(company_id: str, dry_run: bool = False):
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing company: {company_id}")
    db = get_db_connection(company_id)
    try:
        # Get existing tables in this company DB
        existing_tables = {r[0] for r in db.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )).fetchall()}

        for table, columns in MIGRATIONS:
            if table not in existing_tables:
                print(f"  ⏭  {table} — table not found, skipping")
                continue

            # Get existing columns for this table
            existing_cols = {r[0] for r in db.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
            )).fetchall()}

            # Only migrate columns that exist AND are currently TIMESTAMP (not TIMESTAMPTZ)
            cols_to_migrate = []
            for col in columns:
                if col not in existing_cols:
                    continue
                dtype = db.execute(text(f"""
                    SELECT data_type FROM information_schema.columns
                    WHERE table_name='{table}' AND column_name='{col}'
                """)).scalar()
                if dtype == 'timestamp without time zone':
                    cols_to_migrate.append(col)
                else:
                    print(f"  ✅ {table}.{col} — already {dtype}")

            if not cols_to_migrate:
                continue

            alter_parts = ", ".join(
                f"ALTER COLUMN {col} TYPE TIMESTAMPTZ USING {col} AT TIME ZONE 'UTC'"
                for col in cols_to_migrate
            )
            sql = f"ALTER TABLE {table} {alter_parts}"
            print(f"  🔄 {table}: {', '.join(cols_to_migrate)}")
            if not dry_run:
                db.execute(text(sql))
                db.commit()
                print(f"  ✅ {table} migrated")

    except Exception as e:
        db.rollback()
        print(f"  ❌ Error in {company_id}: {e}")
        raise
    finally:
        db.close()


def main():
    dry_run = '--dry-run' in sys.argv
    sys_db = get_system_db()
    try:
        rows = sys_db.execute(text(
            "SELECT database_name FROM system_companies WHERE status = 'active'"
        )).fetchall()
        companies = [r[0].replace('aman_', '') for r in rows]
    finally:
        sys_db.close()

    if not companies:
        print("❌ No active companies found")
        return

    print(f"Found {len(companies)} companies: {companies}")
    for cid in companies:
        migrate_company(cid, dry_run=dry_run)

    print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()
