"""migrate scheduled_reports recipients from TEXT to JSONB

Revision ID: a020_recipients_jsonb
Revises: None
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'a020_recipients_jsonb'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
        ALTER TABLE scheduled_reports 
        ALTER COLUMN recipients TYPE JSONB 
        USING COALESCE(to_jsonb(string_to_array(recipients, ',')), '[]'::jsonb);
    """)
    op.execute("""
        ALTER TABLE scheduled_reports 
        ALTER COLUMN recipients SET DEFAULT '[]'::jsonb;
    """)

def downgrade():
    op.execute("""
        ALTER TABLE scheduled_reports 
        ALTER COLUMN recipients TYPE TEXT 
        USING array_to_string(ARRAY(SELECT jsonb_array_elements_text(COALESCE(recipients, '[]'::jsonb))), ',');
    """)
    op.execute("""
        ALTER TABLE scheduled_reports 
        ALTER COLUMN recipients SET DEFAULT '';
    """)
