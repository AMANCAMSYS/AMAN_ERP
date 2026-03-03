"""Initial baseline — existing schema snapshot

Revision ID: 0001_baseline
Revises: None
Create Date: 2026-03-03

This migration establishes the Alembic version tracking.
All existing tables are assumed to be in place (CREATE TABLE IF NOT EXISTS).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline — no changes, just marks the schema as tracked."""
    pass


def downgrade() -> None:
    pass
