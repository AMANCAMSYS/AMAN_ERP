"""Add POS session unique index + alembic version tracking

Revision ID: 0002_pos_session_unique
Revises: 0001_baseline
Create Date: 2026-03-03

Adds a UNIQUE partial index to prevent TOCTOU race condition
on pos_sessions — only one open session per user allowed.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_pos_session_unique'
down_revision: Union[str, None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only apply if pos_sessions table exists
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pos_sessions')"
    ))
    if result.scalar():
        op.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pos_sessions_user_open
            ON pos_sessions (user_id)
            WHERE status = 'opened'
        """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_pos_sessions_user_open")
