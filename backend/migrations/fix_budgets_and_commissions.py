"""
Migration: Fix budgets table schema + add budget_items, commission_rules, sales_commissions tables.

Addresses:
- budgets table missing columns: name, description, cost_center_id, budget_type
- budget_items table missing entirely (router references it)
- commission_rules table missing
- sales_commissions table missing
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_company(company_id: str):
    url = settings.get_company_database_url(company_id)
    engine = create_engine(url, isolation_level="AUTOCOMMIT")

    with engine.connect() as conn:
        # --- 1. Add missing columns to budgets table ---
        alter_statements = [
            ("name", "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS name VARCHAR(255)"),
            ("description", "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS description TEXT"),
            ("cost_center_id", "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS cost_center_id INTEGER REFERENCES cost_centers(id)"),
            ("budget_type", "ALTER TABLE budgets ADD COLUMN IF NOT EXISTS budget_type VARCHAR(30) DEFAULT 'annual'"),
        ]
        for col, sql in alter_statements:
            try:
                conn.execute(text(sql))
                logger.info(f"  budgets.{col}: added/exists")
            except Exception as e:
                logger.warning(f"  budgets.{col}: {e}")

        # Backfill name from budget_name for existing rows
        try:
            conn.execute(text("UPDATE budgets SET name = budget_name WHERE name IS NULL AND budget_name IS NOT NULL"))
            logger.info("  Backfilled budgets.name from budget_name")
        except Exception as e:
            logger.warning(f"  Backfill name: {e}")

        # --- 2. Create budget_items table ---
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS budget_items (
                    id SERIAL PRIMARY KEY,
                    budget_id INTEGER REFERENCES budgets(id) ON DELETE CASCADE,
                    account_id INTEGER REFERENCES accounts(id),
                    planned_amount DECIMAL(18, 4) DEFAULT 0,
                    actual_amount DECIMAL(18, 4) DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("  budget_items table: created/exists")
        except Exception as e:
            logger.error(f"  budget_items: {e}")

        # --- 3. Create commission_rules table ---
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS commission_rules (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    salesperson_id INTEGER,
                    product_id INTEGER,
                    category_id INTEGER,
                    rate_type VARCHAR(20) DEFAULT 'percentage',
                    rate DECIMAL(10, 4) DEFAULT 0,
                    min_amount DECIMAL(18, 4) DEFAULT 0,
                    max_amount DECIMAL(18, 4),
                    is_active BOOLEAN DEFAULT TRUE,
                    branch_id INTEGER REFERENCES branches(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("  commission_rules table: created/exists")
        except Exception as e:
            logger.error(f"  commission_rules: {e}")

        # --- 4. Create sales_commissions table ---
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sales_commissions (
                    id SERIAL PRIMARY KEY,
                    salesperson_id INTEGER,
                    salesperson_name VARCHAR(255),
                    invoice_id INTEGER,
                    invoice_number VARCHAR(50),
                    invoice_date DATE,
                    invoice_total DECIMAL(18, 4) DEFAULT 0,
                    commission_rate DECIMAL(10, 4) DEFAULT 0,
                    commission_amount DECIMAL(18, 4) DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'pending',
                    paid_date DATE,
                    branch_id INTEGER REFERENCES branches(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(invoice_id, salesperson_id)
                )
            """))
            logger.info("  sales_commissions table: created/exists")
        except Exception as e:
            logger.error(f"  sales_commissions: {e}")

    engine.dispose()
    logger.info(f"Migration completed for company {company_id}")


if __name__ == "__main__":
    company_id = sys.argv[1] if len(sys.argv) > 1 else "ea65de46"
    logger.info(f"Running migration for company: {company_id}")
    migrate_company(company_id)
