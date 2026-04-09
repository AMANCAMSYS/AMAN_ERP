"""add push_devices table for mobile push notifications

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa

revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "push_devices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("platform", sa.String(10), nullable=False),
        sa.Column("fcm_token", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("device_id", "user_id", name="uq_push_devices_device_user"),
        sa.CheckConstraint("platform IN ('ios', 'android')", name="ck_push_devices_platform"),
    )
    op.create_index("ix_push_devices_user_active", "push_devices", ["user_id", "is_active"])
    op.create_index("ix_push_devices_fcm_token", "push_devices", ["fcm_token"])


def downgrade() -> None:
    op.drop_index("ix_push_devices_fcm_token")
    op.drop_index("ix_push_devices_user_active")
    op.drop_table("push_devices")
