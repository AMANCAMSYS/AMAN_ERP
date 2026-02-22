"""
Migration: Phases 8.10-8.15 — POS, Purchases, Sales, Budgets, Assets, HR
Creates all new tables and columns for the remaining Phase 8 improvements.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_company_ids():
    root_url = settings.get_company_database_url("postgres").replace("/aman_postgres", "/postgres")
    eng = create_engine(root_url, isolation_level="AUTOCOMMIT")
    with eng.connect() as conn:
        result = conn.execute(text(
            "SELECT datname FROM pg_database WHERE datname LIKE 'aman_%' AND datistemplate = false"
        ))
        ids = [row[0].replace("aman_", "") for row in result]
    eng.dispose()
    return ids


def get_company_conn(company_id):
    url = settings.get_company_database_url(company_id)
    eng = create_engine(url)
    return eng.connect(), eng


PHASE_TABLES = {
    # ======================== 8.10 POS ========================
    "pos_promotions": """
        CREATE TABLE IF NOT EXISTS pos_promotions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            promotion_type VARCHAR(50) NOT NULL DEFAULT 'percentage',
            value NUMERIC(15,2) NOT NULL DEFAULT 0,
            buy_qty INTEGER,
            get_qty INTEGER,
            coupon_code VARCHAR(100),
            applicable_products TEXT,
            applicable_categories TEXT,
            min_order_amount NUMERIC(15,2) DEFAULT 0,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            branch_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "pos_loyalty_programs": """
        CREATE TABLE IF NOT EXISTS pos_loyalty_programs (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            points_per_unit NUMERIC(10,4) DEFAULT 1,
            currency_per_point NUMERIC(10,4) DEFAULT 0.01,
            min_points_redeem INTEGER DEFAULT 100,
            tier_rules JSONB DEFAULT '[]'::jsonb,
            is_active BOOLEAN DEFAULT TRUE,
            branch_id INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "pos_loyalty_points": """
        CREATE TABLE IF NOT EXISTS pos_loyalty_points (
            id SERIAL PRIMARY KEY,
            program_id INTEGER REFERENCES pos_loyalty_programs(id),
            party_id INTEGER,
            points_earned NUMERIC(12,2) DEFAULT 0,
            points_redeemed NUMERIC(12,2) DEFAULT 0,
            balance NUMERIC(12,2) DEFAULT 0,
            tier VARCHAR(50) DEFAULT 'standard',
            last_activity_at TIMESTAMP DEFAULT NOW(),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "pos_loyalty_transactions": """
        CREATE TABLE IF NOT EXISTS pos_loyalty_transactions (
            id SERIAL PRIMARY KEY,
            loyalty_id INTEGER REFERENCES pos_loyalty_points(id),
            order_id INTEGER,
            txn_type VARCHAR(20) NOT NULL,
            points NUMERIC(12,2) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "pos_tables": """
        CREATE TABLE IF NOT EXISTS pos_tables (
            id SERIAL PRIMARY KEY,
            table_number VARCHAR(50) NOT NULL,
            table_name VARCHAR(100),
            floor VARCHAR(50) DEFAULT 'main',
            capacity INTEGER DEFAULT 4,
            status VARCHAR(20) DEFAULT 'available',
            shape VARCHAR(20) DEFAULT 'square',
            pos_x NUMERIC(8,2) DEFAULT 0,
            pos_y NUMERIC(8,2) DEFAULT 0,
            branch_id INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "pos_table_orders": """
        CREATE TABLE IF NOT EXISTS pos_table_orders (
            id SERIAL PRIMARY KEY,
            table_id INTEGER REFERENCES pos_tables(id),
            order_id INTEGER,
            seated_at TIMESTAMP DEFAULT NOW(),
            cleared_at TIMESTAMP,
            guests INTEGER DEFAULT 1,
            waiter_id INTEGER,
            status VARCHAR(20) DEFAULT 'seated'
        )
    """,
    "pos_kitchen_orders": """
        CREATE TABLE IF NOT EXISTS pos_kitchen_orders (
            id SERIAL PRIMARY KEY,
            order_id INTEGER,
            order_line_id INTEGER,
            product_id INTEGER,
            product_name VARCHAR(255),
            quantity NUMERIC(12,3),
            notes TEXT,
            station VARCHAR(100) DEFAULT 'main',
            status VARCHAR(30) DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            sent_at TIMESTAMP DEFAULT NOW(),
            accepted_at TIMESTAMP,
            ready_at TIMESTAMP,
            served_at TIMESTAMP,
            branch_id INTEGER
        )
    """,

    # ======================== 8.11 Purchases ========================
    "request_for_quotations": """
        CREATE TABLE IF NOT EXISTS request_for_quotations (
            id SERIAL PRIMARY KEY,
            rfq_number VARCHAR(50) UNIQUE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(30) DEFAULT 'draft',
            deadline TIMESTAMP,
            branch_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "rfq_lines": """
        CREATE TABLE IF NOT EXISTS rfq_lines (
            id SERIAL PRIMARY KEY,
            rfq_id INTEGER REFERENCES request_for_quotations(id) ON DELETE CASCADE,
            product_id INTEGER,
            product_name VARCHAR(255),
            quantity NUMERIC(12,3) NOT NULL,
            unit VARCHAR(50),
            specifications TEXT
        )
    """,
    "rfq_responses": """
        CREATE TABLE IF NOT EXISTS rfq_responses (
            id SERIAL PRIMARY KEY,
            rfq_id INTEGER REFERENCES request_for_quotations(id) ON DELETE CASCADE,
            supplier_id INTEGER,
            supplier_name VARCHAR(255),
            unit_price NUMERIC(15,2),
            total_price NUMERIC(15,2),
            delivery_days INTEGER,
            notes TEXT,
            is_selected BOOLEAN DEFAULT FALSE,
            submitted_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "supplier_ratings": """
        CREATE TABLE IF NOT EXISTS supplier_ratings (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER NOT NULL,
            po_id INTEGER,
            quality_score NUMERIC(3,1) DEFAULT 0,
            delivery_score NUMERIC(3,1) DEFAULT 0,
            price_score NUMERIC(3,1) DEFAULT 0,
            service_score NUMERIC(3,1) DEFAULT 0,
            overall_score NUMERIC(3,1) DEFAULT 0,
            comments TEXT,
            rated_by INTEGER,
            rated_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "purchase_agreements": """
        CREATE TABLE IF NOT EXISTS purchase_agreements (
            id SERIAL PRIMARY KEY,
            agreement_number VARCHAR(50) UNIQUE,
            supplier_id INTEGER NOT NULL,
            agreement_type VARCHAR(30) DEFAULT 'blanket',
            title VARCHAR(255),
            start_date DATE,
            end_date DATE,
            total_amount NUMERIC(15,2) DEFAULT 0,
            consumed_amount NUMERIC(15,2) DEFAULT 0,
            status VARCHAR(30) DEFAULT 'draft',
            branch_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "purchase_agreement_lines": """
        CREATE TABLE IF NOT EXISTS purchase_agreement_lines (
            id SERIAL PRIMARY KEY,
            agreement_id INTEGER REFERENCES purchase_agreements(id) ON DELETE CASCADE,
            product_id INTEGER,
            product_name VARCHAR(255),
            quantity NUMERIC(12,3),
            unit_price NUMERIC(15,2),
            delivered_qty NUMERIC(12,3) DEFAULT 0
        )
    """,

    # ======================== 8.12 Sales ========================
    "sales_commissions": """
        CREATE TABLE IF NOT EXISTS sales_commissions (
            id SERIAL PRIMARY KEY,
            salesperson_id INTEGER NOT NULL,
            salesperson_name VARCHAR(255),
            invoice_id INTEGER,
            invoice_number VARCHAR(100),
            invoice_date DATE,
            invoice_total NUMERIC(15,2) DEFAULT 0,
            commission_rate NUMERIC(6,3) DEFAULT 0,
            commission_amount NUMERIC(15,2) DEFAULT 0,
            status VARCHAR(30) DEFAULT 'pending',
            paid_date DATE,
            branch_id INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "commission_rules": """
        CREATE TABLE IF NOT EXISTS commission_rules (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            salesperson_id INTEGER,
            product_id INTEGER,
            category_id INTEGER,
            rate_type VARCHAR(20) DEFAULT 'percentage',
            rate NUMERIC(6,3) DEFAULT 0,
            min_amount NUMERIC(15,2) DEFAULT 0,
            max_amount NUMERIC(15,2),
            is_active BOOLEAN DEFAULT TRUE,
            branch_id INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,

    # ======================== 8.14 Assets ========================
    "asset_transfers": """
        CREATE TABLE IF NOT EXISTS asset_transfers (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            from_branch_id INTEGER,
            to_branch_id INTEGER,
            transfer_date DATE NOT NULL,
            reason TEXT,
            book_value_at_transfer NUMERIC(15,2),
            status VARCHAR(30) DEFAULT 'pending',
            approved_by INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "asset_revaluations": """
        CREATE TABLE IF NOT EXISTS asset_revaluations (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            revaluation_date DATE NOT NULL,
            old_value NUMERIC(15,2) NOT NULL,
            new_value NUMERIC(15,2) NOT NULL,
            difference NUMERIC(15,2) NOT NULL,
            reason TEXT,
            journal_entry_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "asset_insurance": """
        CREATE TABLE IF NOT EXISTS asset_insurance (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            policy_number VARCHAR(100),
            insurer VARCHAR(255),
            coverage_type VARCHAR(100),
            premium_amount NUMERIC(15,2) DEFAULT 0,
            coverage_amount NUMERIC(15,2) DEFAULT 0,
            start_date DATE,
            end_date DATE,
            status VARCHAR(30) DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "asset_maintenance": """
        CREATE TABLE IF NOT EXISTS asset_maintenance (
            id SERIAL PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            maintenance_type VARCHAR(50) DEFAULT 'preventive',
            description TEXT,
            scheduled_date DATE,
            completed_date DATE,
            cost NUMERIC(15,2) DEFAULT 0,
            vendor VARCHAR(255),
            status VARCHAR(30) DEFAULT 'scheduled',
            notes TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,

    # ======================== 8.15 HR ========================
    "job_openings": """
        CREATE TABLE IF NOT EXISTS job_openings (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            department_id INTEGER,
            position_id INTEGER,
            description TEXT,
            requirements TEXT,
            employment_type VARCHAR(50) DEFAULT 'full_time',
            vacancies INTEGER DEFAULT 1,
            status VARCHAR(30) DEFAULT 'open',
            branch_id INTEGER,
            published_at TIMESTAMP,
            closing_date DATE,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "job_applications": """
        CREATE TABLE IF NOT EXISTS job_applications (
            id SERIAL PRIMARY KEY,
            opening_id INTEGER REFERENCES job_openings(id),
            applicant_name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            phone VARCHAR(50),
            resume_url TEXT,
            cover_letter TEXT,
            stage VARCHAR(50) DEFAULT 'applied',
            rating INTEGER DEFAULT 0,
            interview_date TIMESTAMP,
            interviewer_id INTEGER,
            notes TEXT,
            status VARCHAR(30) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """,
    "leave_carryover": """
        CREATE TABLE IF NOT EXISTS leave_carryover (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            leave_type VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL,
            entitled_days NUMERIC(6,1) DEFAULT 0,
            used_days NUMERIC(6,1) DEFAULT 0,
            carried_days NUMERIC(6,1) DEFAULT 0,
            expired_days NUMERIC(6,1) DEFAULT 0,
            max_carryover NUMERIC(6,1) DEFAULT 5,
            calculated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(employee_id, leave_type, year)
        )
    """,
}

# Additional ALTER TABLE statements  
ALTER_STATEMENTS = [
    # 8.10 POS: add discount columns to pos_orders
    "ALTER TABLE pos_orders ADD COLUMN IF NOT EXISTS promotion_id INTEGER",
    "ALTER TABLE pos_orders ADD COLUMN IF NOT EXISTS coupon_code VARCHAR(100)",
    "ALTER TABLE pos_orders ADD COLUMN IF NOT EXISTS loyalty_points_earned NUMERIC(12,2) DEFAULT 0",
    "ALTER TABLE pos_orders ADD COLUMN IF NOT EXISTS loyalty_points_redeemed NUMERIC(12,2) DEFAULT 0",
    "ALTER TABLE pos_orders ADD COLUMN IF NOT EXISTS table_id INTEGER",

    # 8.12 Sales: add commission + partial invoice columns
    "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS salesperson_id INTEGER",
    "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS commission_rate NUMERIC(6,3) DEFAULT 0",
    "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS is_partial BOOLEAN DEFAULT FALSE",
    "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS parent_order_id INTEGER",
    "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS shipped_amount NUMERIC(15,2) DEFAULT 0",

    # 8.12 Sales: credit limit on parties
    "ALTER TABLE parties ADD COLUMN IF NOT EXISTS credit_limit NUMERIC(15,2) DEFAULT 0",
    "ALTER TABLE parties ADD COLUMN IF NOT EXISTS credit_used NUMERIC(15,2) DEFAULT 0",

    # 8.13 Budgets: cost center + multi-year
    "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS cost_center_id INTEGER",
    "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS budget_type VARCHAR(30) DEFAULT 'annual'",
    "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS fiscal_year INTEGER",

    # 8.14 Assets: extra depreciation methods
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS total_units NUMERIC(15,2)",
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS used_units NUMERIC(15,2) DEFAULT 0",
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS qr_code TEXT",
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS barcode VARCHAR(100)",
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS insurance_policy_id INTEGER",
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS last_maintenance_date DATE",

    # 8.15 HR: leave carryover + payslip
    "ALTER TABLE employees ADD COLUMN IF NOT EXISTS annual_leave_entitlement NUMERIC(6,1) DEFAULT 30",
    "ALTER TABLE employees ADD COLUMN IF NOT EXISTS leave_carryover_max NUMERIC(6,1) DEFAULT 5",

    # Quotation conversion tracking
    "ALTER TABLE sales_quotations ADD COLUMN IF NOT EXISTS converted_to_order_id INTEGER",
    "ALTER TABLE sales_quotations ADD COLUMN IF NOT EXISTS conversion_date TIMESTAMP",
    "ALTER TABLE sales_orders ADD COLUMN IF NOT EXISTS source_quotation_id INTEGER",
]


def run_migration(company_id: str):
    conn, eng = get_company_conn(company_id)
    changes = 0
    try:
        for tbl_name, ddl in PHASE_TABLES.items():
            try:
                exists = conn.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
                ), {"t": tbl_name}).fetchone()
                if not exists:
                    conn.execute(text(ddl))
                    conn.commit()
                    logger.info(f"  [+] Created table: {tbl_name}")
                    changes += 1
                else:
                    logger.info(f"  [=] Table exists: {tbl_name}")
            except Exception as e:
                conn.rollback()
                logger.warning(f"  [!] Table {tbl_name}: {e}")

        for stmt in ALTER_STATEMENTS:
            try:
                conn.execute(text(stmt))
                conn.commit()
                changes += 1
            except Exception as e:
                conn.rollback()
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    logger.warning(f"  [!] ALTER: {e}")

        logger.info(f"  Company {company_id}: {changes} changes applied")
        return changes
    finally:
        conn.close()
        eng.dispose()


def main():
    """Run migration for all companies."""
    companies = get_company_ids()
    logger.info(f"Found {len(companies)} companies: {companies}")

    total = 0
    for cid in companies:
        logger.info(f"\n=== Migrating company: {cid} ===")
        try:
            c = run_migration(cid)
            total += c
            logger.info(f"  {cid} OK ({c} changes)")
        except Exception as e:
            logger.error(f"  {cid} FAILED: {e}")

    logger.info(f"\n=== Done. Total changes: {total} ===")


if __name__ == "__main__":
    main()
