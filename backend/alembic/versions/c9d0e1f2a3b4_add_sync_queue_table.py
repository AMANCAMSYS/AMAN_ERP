"""add sync_queue table for mobile offline sync

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_queue",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("device_id", sa.String(255), nullable=False, index=True),
        sa.Column("user_id", sa.Integer, nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("operation", sa.String(20), nullable=False, comment="create | update"),
        sa.Column("payload", JSONB, server_default="{}"),
        sa.Column("device_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("server_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_status", sa.String(20), nullable=False, server_default="pending",
                  comment="pending | synced | conflict | resolved"),
        sa.Column("conflict_resolution", JSONB, nullable=True),
        # AuditMixin columns
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_sync_queue_device_status", "sync_queue", ["device_id", "sync_status"])


def downgrade() -> None:
    op.drop_index("ix_sync_queue_device_status", table_name="sync_queue")
    op.drop_table("sync_queue")
