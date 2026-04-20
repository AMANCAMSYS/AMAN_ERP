"""fix approval and reports schema integrity

Revision ID: a020_fix_schema
Revises: None
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'a020_fix_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # --- T020: Add missing audit columns ---
    op.execute("ALTER TABLE shared_reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP")
    op.execute("ALTER TABLE report_templates ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP")
    op.execute("ALTER TABLE report_templates ADD COLUMN IF NOT EXISTS created_by INTEGER")

    # FK for report_templates.created_by
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_report_templates_created_by') THEN
                ALTER TABLE report_templates ADD CONSTRAINT fk_report_templates_created_by
                    FOREIGN KEY (created_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # --- T021: Add missing FK constraints ---

    # approval_requests.current_approver_id -> company_users
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_approval_requests_current_approver') THEN
                ALTER TABLE approval_requests ADD CONSTRAINT fk_approval_requests_current_approver
                    FOREIGN KEY (current_approver_id) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # approval_requests.escalated_to -> company_users
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_approval_requests_escalated_to') THEN
                ALTER TABLE approval_requests ADD CONSTRAINT fk_approval_requests_escalated_to
                    FOREIGN KEY (escalated_to) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # approval_actions.actioned_by -> company_users
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_approval_actions_actioned_by') THEN
                ALTER TABLE approval_actions ADD CONSTRAINT fk_approval_actions_actioned_by
                    FOREIGN KEY (actioned_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # analytics_dashboards: created_by VARCHAR(100) -> INTEGER with FK
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'analytics_dashboards' AND column_name = 'created_by'
                  AND data_type = 'character varying'
            ) THEN
                ALTER TABLE analytics_dashboards ADD COLUMN created_by_int INTEGER;
                UPDATE analytics_dashboards SET created_by_int = CAST(created_by AS INTEGER)
                    WHERE created_by ~ '^\\d+$';
                ALTER TABLE analytics_dashboards DROP COLUMN created_by;
                ALTER TABLE analytics_dashboards RENAME COLUMN created_by_int TO created_by;
            END IF;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_analytics_dashboards_created_by') THEN
                ALTER TABLE analytics_dashboards ADD CONSTRAINT fk_analytics_dashboards_created_by
                    FOREIGN KEY (created_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # analytics_dashboards: updated_by VARCHAR(100) -> INTEGER with FK
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'analytics_dashboards' AND column_name = 'updated_by'
                  AND data_type = 'character varying'
            ) THEN
                ALTER TABLE analytics_dashboards ADD COLUMN updated_by_int INTEGER;
                UPDATE analytics_dashboards SET updated_by_int = CAST(updated_by AS INTEGER)
                    WHERE updated_by ~ '^\\d+$';
                ALTER TABLE analytics_dashboards DROP COLUMN updated_by;
                ALTER TABLE analytics_dashboards RENAME COLUMN updated_by_int TO updated_by;
            END IF;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_analytics_dashboards_updated_by') THEN
                ALTER TABLE analytics_dashboards ADD CONSTRAINT fk_analytics_dashboards_updated_by
                    FOREIGN KEY (updated_by) REFERENCES company_users(id);
            END IF;
        END $$
    """)

    # --- T022: Add missing indexes ---
    op.execute("CREATE INDEX IF NOT EXISTS idx_approval_requests_workflow ON approval_requests(workflow_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_approval_requests_requested_by ON approval_requests(requested_by)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_report_templates_type ON report_templates(template_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_approval_workflows_doc_type ON approval_workflows(document_type)")


def downgrade():
    # --- Reverse T022: Drop indexes ---
    op.execute("DROP INDEX IF EXISTS idx_approval_workflows_doc_type")
    op.execute("DROP INDEX IF EXISTS idx_report_templates_type")
    op.execute("DROP INDEX IF EXISTS idx_approval_requests_requested_by")
    op.execute("DROP INDEX IF EXISTS idx_approval_requests_workflow")

    # --- Reverse T021: Drop FK constraints ---
    op.execute("ALTER TABLE analytics_dashboards DROP CONSTRAINT IF EXISTS fk_analytics_dashboards_updated_by")
    # Revert updated_by back to VARCHAR
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'analytics_dashboards' AND column_name = 'updated_by'
                  AND data_type = 'integer'
            ) THEN
                ALTER TABLE analytics_dashboards ADD COLUMN updated_by_varchar VARCHAR(100);
                UPDATE analytics_dashboards SET updated_by_varchar = CAST(updated_by AS VARCHAR)
                    WHERE updated_by IS NOT NULL;
                ALTER TABLE analytics_dashboards DROP COLUMN updated_by;
                ALTER TABLE analytics_dashboards RENAME COLUMN updated_by_varchar TO updated_by;
            END IF;
        END $$
    """)

    op.execute("ALTER TABLE analytics_dashboards DROP CONSTRAINT IF EXISTS fk_analytics_dashboards_created_by")
    # Revert created_by back to VARCHAR
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'analytics_dashboards' AND column_name = 'created_by'
                  AND data_type = 'integer'
            ) THEN
                ALTER TABLE analytics_dashboards ADD COLUMN created_by_varchar VARCHAR(100);
                UPDATE analytics_dashboards SET created_by_varchar = CAST(created_by AS VARCHAR)
                    WHERE created_by IS NOT NULL;
                ALTER TABLE analytics_dashboards DROP COLUMN created_by;
                ALTER TABLE analytics_dashboards RENAME COLUMN created_by_varchar TO created_by;
            END IF;
        END $$
    """)

    op.execute("ALTER TABLE approval_actions DROP CONSTRAINT IF EXISTS fk_approval_actions_actioned_by")
    op.execute("ALTER TABLE approval_requests DROP CONSTRAINT IF EXISTS fk_approval_requests_escalated_to")
    op.execute("ALTER TABLE approval_requests DROP CONSTRAINT IF EXISTS fk_approval_requests_current_approver")

    # --- Reverse T020: Drop added columns ---
    op.execute("ALTER TABLE report_templates DROP CONSTRAINT IF EXISTS fk_report_templates_created_by")
    op.execute("ALTER TABLE report_templates DROP COLUMN IF EXISTS created_by")
    op.execute("ALTER TABLE report_templates DROP COLUMN IF EXISTS updated_at")
    op.execute("ALTER TABLE shared_reports DROP COLUMN IF EXISTS updated_at")
