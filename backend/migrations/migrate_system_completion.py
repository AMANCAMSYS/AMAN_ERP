"""
AMAN ERP — System Completion Migration
هجرة إكمال النظام: إضافة الجداول والأعمدة الناقصة لجميع الشركات

Tables added:
  - delivery_orders, delivery_order_lines
  - landed_costs, landed_cost_allocations
  - password_reset_tokens (system-level)
  - print_templates
  - bank_import_batches, bank_import_lines
  - zakat_calculations
  - backup_history

Columns added to employees:
  - nationality, is_saudi, eos_eligible, eos_amount, iqama_number, iqama_expiry

Columns added to production_orders:
  - actual_cost, variance_amount, variance_percentage, costing_status

Run:  python migrations/migrate_system_completion.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine, get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_completion")


# ─── NEW TABLES SQL ────────────────────────────────────────────────────────────

NEW_TABLES_SQL = """

-- ===== DELIVERY ORDERS =====
CREATE TABLE IF NOT EXISTS delivery_orders (
    id SERIAL PRIMARY KEY,
    delivery_number VARCHAR(50) UNIQUE NOT NULL,
    delivery_date DATE NOT NULL DEFAULT CURRENT_DATE,
    sales_order_id INTEGER REFERENCES sales_orders(id),
    invoice_id INTEGER REFERENCES invoices(id),
    party_id INTEGER REFERENCES parties(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    branch_id INTEGER REFERENCES branches(id),
    status VARCHAR(30) DEFAULT 'draft',  -- draft, confirmed, shipped, delivered, cancelled
    shipping_method VARCHAR(100),
    tracking_number VARCHAR(100),
    driver_name VARCHAR(100),
    driver_phone VARCHAR(50),
    vehicle_number VARCHAR(50),
    delivery_address TEXT,
    notes TEXT,
    total_items INTEGER DEFAULT 0,
    total_quantity NUMERIC(15,4) DEFAULT 0,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_by INTEGER REFERENCES company_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS delivery_order_lines (
    id SERIAL PRIMARY KEY,
    delivery_order_id INTEGER NOT NULL REFERENCES delivery_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    so_line_id INTEGER,  -- references sales_order_lines(id)
    description TEXT,
    ordered_qty NUMERIC(15,4) DEFAULT 0,
    delivered_qty NUMERIC(15,4) DEFAULT 0,
    unit VARCHAR(50),
    batch_number VARCHAR(100),
    serial_numbers TEXT,  -- JSON array of serial numbers
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===== LANDED COSTS =====
CREATE TABLE IF NOT EXISTS landed_costs (
    id SERIAL PRIMARY KEY,
    lc_number VARCHAR(50) UNIQUE NOT NULL,
    lc_date DATE NOT NULL DEFAULT CURRENT_DATE,
    purchase_order_id INTEGER REFERENCES purchase_orders(id),
    grn_id INTEGER,
    reference VARCHAR(100),
    description TEXT,
    total_amount NUMERIC(15,4) DEFAULT 0,
    allocation_method VARCHAR(30) DEFAULT 'by_value',  -- by_value, by_quantity, by_weight, equal
    status VARCHAR(20) DEFAULT 'draft',  -- draft, allocated, posted, cancelled
    currency VARCHAR(10) DEFAULT 'SAR',
    notes TEXT,
    branch_id INTEGER REFERENCES branches(id),
    created_by INTEGER REFERENCES company_users(id),
    journal_entry_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS landed_cost_items (
    id SERIAL PRIMARY KEY,
    landed_cost_id INTEGER NOT NULL REFERENCES landed_costs(id) ON DELETE CASCADE,
    cost_type VARCHAR(50) NOT NULL,  -- freight, customs, insurance, handling, other
    description TEXT,
    amount NUMERIC(15,4) NOT NULL DEFAULT 0,
    vendor_id INTEGER REFERENCES parties(id),
    invoice_ref VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS landed_cost_allocations (
    id SERIAL PRIMARY KEY,
    landed_cost_id INTEGER NOT NULL REFERENCES landed_costs(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    po_line_id INTEGER,
    original_cost NUMERIC(15,4) NOT NULL DEFAULT 0,
    allocated_amount NUMERIC(15,4) NOT NULL DEFAULT 0,
    new_cost NUMERIC(15,4) NOT NULL DEFAULT 0,
    allocation_basis NUMERIC(15,6) DEFAULT 0,
    allocation_share NUMERIC(15,6) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===== PRINT TEMPLATES =====
CREATE TABLE IF NOT EXISTS print_templates (
    id SERIAL PRIMARY KEY,
    template_type VARCHAR(50) NOT NULL,  -- invoice, quotation, receipt, delivery_order, purchase_order, payslip
    name VARCHAR(200) NOT NULL,
    html_template TEXT NOT NULL,
    css_styles TEXT,
    header_html TEXT,
    footer_html TEXT,
    paper_size VARCHAR(20) DEFAULT 'A4',  -- A4, A5, thermal_80mm, letter
    orientation VARCHAR(20) DEFAULT 'portrait',
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES company_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===== BANK IMPORT =====
CREATE TABLE IF NOT EXISTS bank_import_batches (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(300),
    bank_account_id INTEGER,
    total_lines INTEGER DEFAULT 0,
    imported_lines INTEGER DEFAULT 0,
    matched_lines INTEGER DEFAULT 0,
    total_debit NUMERIC(15,4) DEFAULT 0,
    total_credit NUMERIC(15,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, imported, partially_matched, fully_matched
    uploaded_by INTEGER REFERENCES company_users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bank_import_lines (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES bank_import_batches(id) ON DELETE CASCADE,
    line_number INTEGER DEFAULT 0,
    transaction_date DATE,
    description TEXT,
    reference VARCHAR(200),
    debit NUMERIC(15,4) DEFAULT 0,
    credit NUMERIC(15,4) DEFAULT 0,
    balance NUMERIC(15,4),
    status VARCHAR(20) DEFAULT 'unmatched',  -- unmatched, matched, ignored
    matched_transaction_id INTEGER,
    account_id INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===== ZAKAT CALCULATIONS =====
CREATE TABLE IF NOT EXISTS zakat_calculations (
    id SERIAL PRIMARY KEY,
    fiscal_year INTEGER NOT NULL UNIQUE,
    method VARCHAR(30) DEFAULT 'net_assets',  -- net_assets, adjusted_profit
    zakat_base NUMERIC(15,4) DEFAULT 0,
    zakat_rate NUMERIC(8,4) DEFAULT 2.5,
    zakat_amount NUMERIC(15,4) DEFAULT 0,
    details JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'calculated',  -- calculated, posted, paid
    journal_entry_id INTEGER,
    notes TEXT,
    calculated_by INTEGER REFERENCES company_users(id),
    calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===== FISCAL PERIOD LOCKS =====
CREATE TABLE IF NOT EXISTS fiscal_period_locks (
    id SERIAL PRIMARY KEY,
    period_name VARCHAR(100) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    locked_at TIMESTAMPTZ,
    locked_by INTEGER REFERENCES company_users(id),
    unlocked_at TIMESTAMPTZ,
    unlocked_by INTEGER REFERENCES company_users(id),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ===== BACKUP HISTORY =====
CREATE TABLE IF NOT EXISTS backup_history (
    id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20) DEFAULT 'manual',  -- manual, scheduled, auto
    file_name VARCHAR(300),
    file_size BIGINT DEFAULT 0,
    file_path TEXT,
    status VARCHAR(20) DEFAULT 'completed',  -- in_progress, completed, failed
    error_message TEXT,
    tables_included INTEGER DEFAULT 0,
    rows_exported BIGINT DEFAULT 0,
    created_by INTEGER REFERENCES company_users(id),
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

"""

# ─── ALTER TABLE statements for existing tables ─────────────────────────────────

ALTER_EMPLOYEES_SQL = """
-- Saudization / Nationality tracking
DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS nationality VARCHAR(5) DEFAULT 'SA';
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_saudi BOOLEAN DEFAULT TRUE;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS eos_eligible BOOLEAN DEFAULT TRUE;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS eos_amount NUMERIC(15,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS iqama_number VARCHAR(20);
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS iqama_expiry DATE;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS passport_number VARCHAR(30);
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE employees ADD COLUMN IF NOT EXISTS sponsor VARCHAR(200);
EXCEPTION WHEN others THEN NULL; END $$;
"""

ALTER_PRODUCTION_ORDERS_SQL = """
-- Actual Manufacturing Costing
DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS actual_material_cost NUMERIC(15,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS actual_labor_cost NUMERIC(15,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS actual_overhead_cost NUMERIC(15,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS actual_total_cost NUMERIC(15,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS standard_cost NUMERIC(15,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS variance_amount NUMERIC(15,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS variance_percentage NUMERIC(8,4) DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN IF NOT EXISTS costing_status VARCHAR(20) DEFAULT 'pending';
EXCEPTION WHEN others THEN NULL; END $$;
"""

ALTER_INVOICES_SQL = """
-- Link invoice to delivery order
DO $$ BEGIN
    ALTER TABLE invoices ADD COLUMN IF NOT EXISTS delivery_order_id INTEGER;
EXCEPTION WHEN others THEN NULL; END $$;
"""

SYSTEM_TABLES_SQL = """
-- Password reset tokens (system-level table)
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    company_id VARCHAR(50),
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_prt_token ON password_reset_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_prt_username ON password_reset_tokens(username);

-- Backup history (system-level)
CREATE TABLE IF NOT EXISTS system_backup_history (
    id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    backup_type VARCHAR(20) DEFAULT 'manual',
    file_name VARCHAR(300),
    file_size BIGINT DEFAULT 0,
    file_path TEXT,
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);
"""


def migrate_system_tables():
    """Create system-level tables in the main postgres database"""
    logger.info("🔧 Creating system-level tables...")
    with engine.connect() as conn:
        conn.execute(text(SYSTEM_TABLES_SQL))
        conn.commit()
    logger.info("✅ System tables created")


def migrate_company(company_id: str):
    """Apply migration to a single company database"""
    logger.info(f"📦 Migrating company: {company_id}")
    db = get_db_connection(company_id)
    try:
        # 1. Create new tables
        db.execute(text(NEW_TABLES_SQL))
        db.commit()
        logger.info(f"  ✅ New tables created for {company_id}")

        # 2. Alter existing tables
        db.execute(text(ALTER_EMPLOYEES_SQL))
        db.commit()
        logger.info(f"  ✅ Employees table updated for {company_id}")

        db.execute(text(ALTER_PRODUCTION_ORDERS_SQL))
        db.commit()
        logger.info(f"  ✅ Production orders table updated for {company_id}")

        db.execute(text(ALTER_INVOICES_SQL))
        db.commit()
        logger.info(f"  ✅ Invoices table updated for {company_id}")

        # 3. Add triggers for new tables
        triggers_sql = """
        DROP TRIGGER IF EXISTS update_delivery_orders_updated_at ON delivery_orders;
        CREATE TRIGGER update_delivery_orders_updated_at BEFORE UPDATE ON delivery_orders
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_landed_costs_updated_at ON landed_costs;
        CREATE TRIGGER update_landed_costs_updated_at BEFORE UPDATE ON landed_costs
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_print_templates_updated_at ON print_templates;
        CREATE TRIGGER update_print_templates_updated_at BEFORE UPDATE ON print_templates
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        db.execute(text(triggers_sql))
        db.commit()
        logger.info(f"  ✅ Triggers created for {company_id}")

        # 4. Add default account mappings
        default_mappings = {
            "acc_map_landed_costs": "1103",  # inventory
            "acc_map_freight": "5204",  # transportation expense
            "acc_map_customs": "5206",  # government fees
            "acc_map_eos_provision": "2202",  # end of service provision
            "acc_map_eos_expense": "5221",  # end of service expense
            "acc_map_zakat_expense": "5206",  # zakat expense = government fees
            "acc_map_zakat_payable": "2111",  # zakat payable
        }
        for key, code in default_mappings.items():
            # Find account ID by code
            acct = db.execute(text("SELECT id FROM accounts WHERE account_code = :code"), {"code": code}).fetchone()
            if acct:
                db.execute(text("""
                    INSERT INTO company_settings (setting_key, setting_value)
                    VALUES (:key, :val)
                    ON CONFLICT (setting_key) DO NOTHING
                """), {"key": key, "val": str(acct[0])})
        db.commit()
        logger.info(f"  ✅ Default account mappings added for {company_id}")

        # 5. Insert default print templates
        db.execute(text("""
            INSERT INTO print_templates (template_type, name, html_template, is_default)
            SELECT 'invoice', 'فاتورة مبيعات افتراضية', '<div>{{invoice_data}}</div>', TRUE
            WHERE NOT EXISTS (SELECT 1 FROM print_templates WHERE template_type = 'invoice' AND is_default = TRUE)
        """))
        db.commit()
        logger.info(f"  ✅ Default print templates for {company_id}")

    except Exception as e:
        logger.error(f"  ❌ Error migrating {company_id}: {e}")
        try:
            db.rollback()
        except:
            pass
    finally:
        db.close()


def main():
    # 1. System tables
    migrate_system_tables()

    # 2. Get all companies
    with engine.connect() as conn:
        companies = conn.execute(text(
            "SELECT id FROM system_companies WHERE status = 'active'"
        )).fetchall()

    logger.info(f"📋 Found {len(companies)} active companies to migrate")

    # 3. Migrate each company
    for company in companies:
        migrate_company(company[0])

    logger.info("🎉 Migration complete!")


if __name__ == "__main__":
    main()
