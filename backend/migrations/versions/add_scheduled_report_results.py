"""add scheduled_report_results table

Revision ID: a020_report_results
Revises: None
Create Date: 2026-04-20
"""
from alembic import op

revision = 'a020_report_results'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_report_results (
            id SERIAL PRIMARY KEY,
            scheduled_report_id INTEGER REFERENCES scheduled_reports(id) ON DELETE CASCADE,
            report_data JSONB NOT NULL,
            generated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'completed'
        );
        CREATE INDEX IF NOT EXISTS idx_report_results_schedule ON scheduled_report_results(scheduled_report_id);
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_report_results_schedule;")
    op.execute("DROP TABLE IF EXISTS scheduled_report_results;")
