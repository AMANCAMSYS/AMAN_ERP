"""fix subscriptions, services, and expenses schema integrity

Revision ID: a021_fix_sub_svc_exp
Revises: a020_fix_schema
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'a021_fix_sub_svc_exp'
down_revision = 'a020_fix_schema'
branch_labels = None
depends_on = None


def _varchar_to_integer_fk(table, column, fk_name):
    """Convert a VARCHAR column to INTEGER with FK to company_users(id)."""
    op.execute(f"""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column}'
                  AND data_type = 'character varying'
            ) THEN
                ALTER TABLE {table} ADD COLUMN {column}_int INTEGER;
                UPDATE {table} SET {column}_int = CAST({column} AS INTEGER)
                    WHERE {column} ~ '^\\d+$';
                ALTER TABLE {table} DROP COLUMN {column};
                ALTER TABLE {table} RENAME COLUMN {column}_int TO {column};
            END IF;
        END $$
    """)
    op.execute(f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{fk_name}') THEN
                ALTER TABLE {table} ADD CONSTRAINT {fk_name}
                    FOREIGN KEY ({column}) REFERENCES company_users(id);
            END IF;
        END $$
    """)


def upgrade():
    # =====================================================
    # 1. SUBSCRIPTION TABLES — VARCHAR(100) -> INTEGER FK
    # =====================================================

    # subscription_plans: created_by, updated_by
    _varchar_to_integer_fk('subscription_plans', 'created_by', 'fk_sub_plans_created_by')
    _varchar_to_integer_fk('subscription_plans', 'updated_by', 'fk_sub_plans_updated_by')

    # subscription_enrollments: created_by, updated_by
    _varchar_to_integer_fk('subscription_enrollments', 'created_by', 'fk_sub_enrollments_created_by')
    _varchar_to_integer_fk('subscription_enrollments', 'updated_by', 'fk_sub_enrollments_updated_by')

    # subscription_invoices: created_by, updated_by
    _varchar_to_integer_fk('subscription_invoices', 'created_by', 'fk_sub_invoices_created_by')
    _varchar_to_integer_fk('subscription_invoices', 'updated_by', 'fk_sub_invoices_updated_by')

    # =====================================================
    # 2. SUBSCRIPTION ENROLLMENTS — Add missing columns
    # =====================================================
    op.execute("ALTER TABLE subscription_enrollments ADD COLUMN IF NOT EXISTS trial_end_date DATE")
    op.execute("ALTER TABLE subscription_enrollments ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ")
    op.execute("ALTER TABLE subscription_enrollments ADD COLUMN IF NOT EXISTS cancellation_reason TEXT")

    # Partial unique index: one active/paused enrollment per customer+plan
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_sub_enrollments_active_unique
        ON subscription_enrollments(customer_id, plan_id)
        WHERE status IN ('active', 'paused')
    """)

    # =====================================================
    # 3. SUBSCRIPTION INVOICES — Add GL/tax columns
    # =====================================================
    op.execute("ALTER TABLE subscription_invoices ADD COLUMN IF NOT EXISTS journal_entry_id INTEGER")
    op.execute("ALTER TABLE subscription_invoices ADD COLUMN IF NOT EXISTS tax_rate NUMERIC(5,2)")
    op.execute("ALTER TABLE subscription_invoices ADD COLUMN IF NOT EXISTS tax_amount NUMERIC(18,4) DEFAULT 0")
    op.execute("ALTER TABLE subscription_invoices ADD COLUMN IF NOT EXISTS currency VARCHAR(3)")

    # FK for journal_entry_id
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sub_invoices_journal_entry') THEN
                ALTER TABLE subscription_invoices ADD CONSTRAINT fk_sub_invoices_journal_entry
                    FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id);
            END IF;
        END $$
    """)

    # =====================================================
    # 4. EXPENSE POLICIES — Add missing audit/soft-delete
    # =====================================================
    op.execute("ALTER TABLE expense_policies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP")
    op.execute("ALTER TABLE expense_policies ADD COLUMN IF NOT EXISTS updated_by INTEGER")
    op.execute("ALTER TABLE expense_policies ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false")

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_expense_policies_updated_by') THEN
                ALTER TABLE expense_policies ADD CONSTRAINT fk_expense_policies_updated_by
                    FOREIGN KEY (updated_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # =====================================================
    # 5. EXPENSES — Add missing columns and indexes
    # =====================================================
    op.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS currency VARCHAR(3)")
    op.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(18,6) DEFAULT 1")
    op.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS policy_id INTEGER")
    op.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS updated_by INTEGER")
    op.execute("ALTER TABLE expenses ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false")

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_expenses_policy_id') THEN
                ALTER TABLE expenses ADD CONSTRAINT fk_expenses_policy_id
                    FOREIGN KEY (policy_id) REFERENCES expense_policies(id);
            END IF;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_expenses_updated_by') THEN
                ALTER TABLE expenses ADD CONSTRAINT fk_expenses_updated_by
                    FOREIGN KEY (updated_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_expenses_expense_date ON expenses(expense_date)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_expenses_approval_status ON expenses(approval_status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_expenses_branch_id ON expenses(branch_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_expenses_created_by ON expenses(created_by)")

    # =====================================================
    # 6. DOCUMENTS — Add soft-delete, updated_by, tags JSONB
    # =====================================================
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS updated_by INTEGER")

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_documents_updated_by') THEN
                ALTER TABLE documents ADD CONSTRAINT fk_documents_updated_by
                    FOREIGN KEY (updated_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # Migrate tags TEXT -> JSONB
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'documents' AND column_name = 'tags'
                  AND data_type = 'text'
            ) THEN
                ALTER TABLE documents ADD COLUMN tags_jsonb JSONB DEFAULT '[]';
                UPDATE documents SET tags_jsonb = CASE
                    WHEN tags IS NULL OR tags = '' THEN '[]'::jsonb
                    ELSE to_jsonb(string_to_array(tags, ','))
                END;
                ALTER TABLE documents DROP COLUMN tags;
                ALTER TABLE documents RENAME COLUMN tags_jsonb TO tags;
            END IF;
        END $$
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_related ON documents(related_module, related_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_created_by ON documents(created_by)")

    # =====================================================
    # 7. SERVICE REQUESTS — Add soft-delete, branch_id, updated_by
    # =====================================================
    op.execute("ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS branch_id INTEGER")
    op.execute("ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS updated_by INTEGER")

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_service_requests_branch_id') THEN
                ALTER TABLE service_requests ADD CONSTRAINT fk_service_requests_branch_id
                    FOREIGN KEY (branch_id) REFERENCES branches(id);
            END IF;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_service_requests_updated_by') THEN
                ALTER TABLE service_requests ADD CONSTRAINT fk_service_requests_updated_by
                    FOREIGN KEY (updated_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # =====================================================
    # 8. SERVICE REQUEST COSTS — Add soft-delete, updated_by
    # =====================================================
    op.execute("ALTER TABLE service_request_costs ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false")
    op.execute("ALTER TABLE service_request_costs ADD COLUMN IF NOT EXISTS updated_by INTEGER")

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_service_request_costs_updated_by') THEN
                ALTER TABLE service_request_costs ADD CONSTRAINT fk_service_request_costs_updated_by
                    FOREIGN KEY (updated_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # =====================================================
    # 9. CREATE deferred_revenue_schedules TABLE
    # =====================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS deferred_revenue_schedules (
            id SERIAL PRIMARY KEY,
            subscription_invoice_id INTEGER NOT NULL REFERENCES subscription_invoices(id),
            enrollment_id INTEGER NOT NULL REFERENCES subscription_enrollments(id),
            recognition_date DATE NOT NULL,
            amount NUMERIC(18,4) NOT NULL,
            journal_entry_id INTEGER REFERENCES journal_entries(id),
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'posted', 'skipped')),
            created_by INTEGER REFERENCES company_users(id),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER REFERENCES company_users(id)
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_deferred_rev_enrollment ON deferred_revenue_schedules(enrollment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_deferred_rev_recognition ON deferred_revenue_schedules(recognition_date, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_deferred_rev_invoice ON deferred_revenue_schedules(subscription_invoice_id)")


def downgrade():
    # --- Drop deferred_revenue_schedules ---
    op.execute("DROP INDEX IF EXISTS ix_deferred_rev_invoice")
    op.execute("DROP INDEX IF EXISTS ix_deferred_rev_recognition")
    op.execute("DROP INDEX IF EXISTS ix_deferred_rev_enrollment")
    op.execute("DROP TABLE IF EXISTS deferred_revenue_schedules")

    # --- service_request_costs: revert ---
    op.execute("ALTER TABLE service_request_costs DROP CONSTRAINT IF EXISTS fk_service_request_costs_updated_by")
    op.execute("ALTER TABLE service_request_costs DROP COLUMN IF EXISTS updated_by")
    op.execute("ALTER TABLE service_request_costs DROP COLUMN IF EXISTS is_deleted")

    # --- service_requests: revert ---
    op.execute("ALTER TABLE service_requests DROP CONSTRAINT IF EXISTS fk_service_requests_updated_by")
    op.execute("ALTER TABLE service_requests DROP CONSTRAINT IF EXISTS fk_service_requests_branch_id")
    op.execute("ALTER TABLE service_requests DROP COLUMN IF EXISTS updated_by")
    op.execute("ALTER TABLE service_requests DROP COLUMN IF EXISTS branch_id")
    op.execute("ALTER TABLE service_requests DROP COLUMN IF EXISTS is_deleted")

    # --- documents: revert ---
    op.execute("DROP INDEX IF EXISTS idx_documents_created_by")
    op.execute("DROP INDEX IF EXISTS idx_documents_related")
    # Revert tags JSONB -> TEXT
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'documents' AND column_name = 'tags'
                  AND data_type = 'jsonb'
            ) THEN
                ALTER TABLE documents ADD COLUMN tags_text TEXT;
                UPDATE documents SET tags_text = CASE
                    WHEN tags IS NULL OR tags = '[]'::jsonb THEN NULL
                    ELSE array_to_string(ARRAY(SELECT jsonb_array_elements_text(tags)), ',')
                END;
                ALTER TABLE documents DROP COLUMN tags;
                ALTER TABLE documents RENAME COLUMN tags_text TO tags;
            END IF;
        END $$
    """)
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS fk_documents_updated_by")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS updated_by")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS is_deleted")

    # --- expenses: revert ---
    op.execute("DROP INDEX IF EXISTS idx_expenses_created_by")
    op.execute("DROP INDEX IF EXISTS idx_expenses_branch_id")
    op.execute("DROP INDEX IF EXISTS idx_expenses_approval_status")
    op.execute("DROP INDEX IF EXISTS idx_expenses_expense_date")
    op.execute("ALTER TABLE expenses DROP CONSTRAINT IF EXISTS fk_expenses_updated_by")
    op.execute("ALTER TABLE expenses DROP CONSTRAINT IF EXISTS fk_expenses_policy_id")
    op.execute("ALTER TABLE expenses DROP COLUMN IF EXISTS is_deleted")
    op.execute("ALTER TABLE expenses DROP COLUMN IF EXISTS updated_by")
    op.execute("ALTER TABLE expenses DROP COLUMN IF EXISTS policy_id")
    op.execute("ALTER TABLE expenses DROP COLUMN IF EXISTS exchange_rate")
    op.execute("ALTER TABLE expenses DROP COLUMN IF EXISTS currency")

    # --- expense_policies: revert ---
    op.execute("ALTER TABLE expense_policies DROP CONSTRAINT IF EXISTS fk_expense_policies_updated_by")
    op.execute("ALTER TABLE expense_policies DROP COLUMN IF EXISTS is_deleted")
    op.execute("ALTER TABLE expense_policies DROP COLUMN IF EXISTS updated_by")
    op.execute("ALTER TABLE expense_policies DROP COLUMN IF EXISTS updated_at")

    # --- subscription_invoices: revert ---
    op.execute("ALTER TABLE subscription_invoices DROP CONSTRAINT IF EXISTS fk_sub_invoices_journal_entry")
    op.execute("ALTER TABLE subscription_invoices DROP COLUMN IF EXISTS currency")
    op.execute("ALTER TABLE subscription_invoices DROP COLUMN IF EXISTS tax_amount")
    op.execute("ALTER TABLE subscription_invoices DROP COLUMN IF EXISTS tax_rate")
    op.execute("ALTER TABLE subscription_invoices DROP COLUMN IF EXISTS journal_entry_id")

    # --- subscription_enrollments: revert ---
    op.execute("DROP INDEX IF EXISTS ix_sub_enrollments_active_unique")
    op.execute("ALTER TABLE subscription_enrollments DROP COLUMN IF EXISTS cancellation_reason")
    op.execute("ALTER TABLE subscription_enrollments DROP COLUMN IF EXISTS cancelled_at")
    op.execute("ALTER TABLE subscription_enrollments DROP COLUMN IF EXISTS trial_end_date")

    # --- Revert VARCHAR columns (all 3 subscription tables) ---
    # This is lossy but maintains schema compatibility
    for table in ['subscription_invoices', 'subscription_enrollments', 'subscription_plans']:
        for col in ['updated_by', 'created_by']:
            fk_name = f"fk_sub_{'plans' if 'plans' in table else 'enrollments' if 'enrollments' in table else 'invoices'}_{col}"
            op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {fk_name}")
            op.execute(f"""
                DO $$ BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '{table}' AND column_name = '{col}'
                          AND data_type = 'integer'
                    ) THEN
                        ALTER TABLE {table} ADD COLUMN {col}_varchar VARCHAR(100);
                        UPDATE {table} SET {col}_varchar = CAST({col} AS VARCHAR)
                            WHERE {col} IS NOT NULL;
                        ALTER TABLE {table} DROP COLUMN {col};
                        ALTER TABLE {table} RENAME COLUMN {col}_varchar TO {col};
                    END IF;
                END $$
            """)
