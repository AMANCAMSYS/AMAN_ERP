"""Phase 5: TASK-034/035/036/037/038/039/040 schema additions

- TASK-034 Multi-Book: `ledgers` table + `journal_entries.ledger_id`
- TASK-035 Dimensions: 6 dim_* columns on `journal_lines`
- TASK-036 IFRS 15:   `revenue_contracts`, `performance_obligations`
- TASK-037 IFRS 9:    `ecl_rate_matrix` (seeded), `ecl_provisions`
- TASK-038 IAS 2:     `inventory_nrv_tests`
- TASK-039 IAS 36:    `cash_generating_units`, `impairment_tests`
- TASK-040 E-Invoice: `e_invoice_submissions`

Mirrors the canonical SQL in backend/database.py so existing tenants are
upgraded without waiting for a bootstrap re-run.
"""
from alembic import op


revision = "0012_phase5_world_comparison"
down_revision = "0011_je_source_composite_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- ── TASK-034 Multi-Book ────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS ledgers (
        id SERIAL PRIMARY KEY,
        code VARCHAR(30) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        is_primary BOOLEAN DEFAULT FALSE,
        framework VARCHAR(30),
        currency VARCHAR(10),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    INSERT INTO ledgers (code, name, is_primary, framework)
    VALUES ('primary', 'Primary Ledger', TRUE, 'local_gaap')
    ON CONFLICT (code) DO NOTHING;

    ALTER TABLE journal_entries
        ADD COLUMN IF NOT EXISTS ledger_id INTEGER REFERENCES ledgers(id);
    UPDATE journal_entries SET ledger_id = (SELECT id FROM ledgers WHERE code='primary')
        WHERE ledger_id IS NULL;
    CREATE INDEX IF NOT EXISTS idx_je_ledger_date ON journal_entries (ledger_id, entry_date);

    -- ── TASK-035 Dimensions ────────────────────────────────────────────────
    ALTER TABLE journal_lines
        ADD COLUMN IF NOT EXISTS dim_segment        VARCHAR(50),
        ADD COLUMN IF NOT EXISTS dim_project        VARCHAR(50),
        ADD COLUMN IF NOT EXISTS dim_product_line   VARCHAR(50),
        ADD COLUMN IF NOT EXISTS dim_customer_group VARCHAR(50),
        ADD COLUMN IF NOT EXISTS dim_employee       VARCHAR(50),
        ADD COLUMN IF NOT EXISTS dim_custom_1       VARCHAR(50);
    CREATE INDEX IF NOT EXISTS idx_jl_dim_project ON journal_lines (dim_project) WHERE dim_project IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_jl_dim_segment ON journal_lines (dim_segment) WHERE dim_segment IS NOT NULL;

    -- ── TASK-037 IFRS 9 ECL ────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS ecl_rate_matrix (
        id SERIAL PRIMARY KEY,
        bucket_label VARCHAR(50) NOT NULL,
        min_days_overdue INTEGER NOT NULL,
        max_days_overdue INTEGER,
        loss_rate DECIMAL(7, 4) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    INSERT INTO ecl_rate_matrix (bucket_label, min_days_overdue, max_days_overdue, loss_rate) VALUES
        ('current',    0,    0,    0.0050),
        ('1-30',       1,    30,   0.0150),
        ('31-60',      31,   60,   0.0500),
        ('61-90',      61,   90,   0.1500),
        ('91-180',     91,   180,  0.3500),
        ('181-365',    181,  365,  0.6000),
        ('over_1y',    366,  NULL, 1.0000)
    ON CONFLICT DO NOTHING;

    CREATE TABLE IF NOT EXISTS ecl_provisions (
        id SERIAL PRIMARY KEY,
        as_of_date DATE NOT NULL,
        customer_id INTEGER,
        total_exposure DECIMAL(18, 2) NOT NULL,
        provision_amount DECIMAL(18, 2) NOT NULL,
        details JSONB,
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_ecl_prov_date ON ecl_provisions (as_of_date);

    -- ── TASK-038 IAS 2 NRV ─────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS inventory_nrv_tests (
        id SERIAL PRIMARY KEY,
        as_of_date DATE NOT NULL,
        product_id INTEGER,
        warehouse_id INTEGER,
        cost_value DECIMAL(18, 4) NOT NULL,
        nrv_value DECIMAL(18, 4) NOT NULL,
        writedown_amount DECIMAL(18, 4) NOT NULL DEFAULT 0,
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_nrv_date ON inventory_nrv_tests (as_of_date);

    -- ── TASK-039 IAS 36 Impairment ─────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS cash_generating_units (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(200) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS impairment_tests (
        id SERIAL PRIMARY KEY,
        cgu_id INTEGER NOT NULL REFERENCES cash_generating_units(id),
        as_of_date DATE NOT NULL,
        carrying_amount DECIMAL(18, 2) NOT NULL,
        value_in_use DECIMAL(18, 2),
        fair_value_less_costs DECIMAL(18, 2),
        recoverable_amount DECIMAL(18, 2) NOT NULL,
        impairment_loss DECIMAL(18, 2) NOT NULL DEFAULT 0,
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        details JSONB,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_impairment_cgu_date ON impairment_tests (cgu_id, as_of_date);

    -- ── TASK-036 IFRS 15 / ASC 606 ─────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS revenue_contracts (
        id SERIAL PRIMARY KEY,
        contract_number VARCHAR(100) UNIQUE NOT NULL,
        customer_id INTEGER,
        total_transaction_price DECIMAL(18, 2) NOT NULL,
        currency VARCHAR(10) DEFAULT 'SAR',
        start_date DATE,
        end_date DATE,
        status VARCHAR(30) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS performance_obligations (
        id SERIAL PRIMARY KEY,
        contract_id INTEGER NOT NULL REFERENCES revenue_contracts(id) ON DELETE CASCADE,
        description TEXT NOT NULL,
        standalone_selling_price DECIMAL(18, 2),
        allocated_price DECIMAL(18, 2),
        recognition_method VARCHAR(30) DEFAULT 'point_in_time',
        satisfied_pct DECIMAL(7, 4) DEFAULT 0,
        revenue_recognized DECIMAL(18, 2) DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_po_contract ON performance_obligations (contract_id);

    -- ── TASK-040 E-Invoicing ───────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS e_invoice_submissions (
        id SERIAL PRIMARY KEY,
        jurisdiction VARCHAR(10) NOT NULL,
        invoice_type VARCHAR(20) NOT NULL,
        invoice_id INTEGER NOT NULL,
        document_uuid VARCHAR(100),
        submission_status VARCHAR(30) DEFAULT 'pending',
        submitted_at TIMESTAMPTZ,
        response_payload JSONB,
        error_message TEXT,
        retry_count INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_einv_jurisdiction_status
        ON e_invoice_submissions (jurisdiction, submission_status);
    CREATE INDEX IF NOT EXISTS idx_einv_invoice
        ON e_invoice_submissions (invoice_type, invoice_id);
    """)


def downgrade() -> None:
    # Phase 5 additions are additive and safe to leave; downgrade only drops
    # the explicitly-added tables/columns. Reverting seed rows is not useful.
    op.execute("""
        DROP TABLE IF EXISTS e_invoice_submissions;
        DROP TABLE IF EXISTS performance_obligations;
        DROP TABLE IF EXISTS revenue_contracts;
        DROP TABLE IF EXISTS impairment_tests;
        DROP TABLE IF EXISTS cash_generating_units;
        DROP TABLE IF EXISTS inventory_nrv_tests;
        DROP TABLE IF EXISTS ecl_provisions;
        DROP TABLE IF EXISTS ecl_rate_matrix;
        ALTER TABLE journal_lines
            DROP COLUMN IF EXISTS dim_segment,
            DROP COLUMN IF EXISTS dim_project,
            DROP COLUMN IF EXISTS dim_product_line,
            DROP COLUMN IF EXISTS dim_customer_group,
            DROP COLUMN IF EXISTS dim_employee,
            DROP COLUMN IF EXISTS dim_custom_1;
        ALTER TABLE journal_entries DROP COLUMN IF EXISTS ledger_id;
        DROP TABLE IF EXISTS ledgers;
    """)
