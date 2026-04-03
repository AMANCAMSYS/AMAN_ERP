"""Add unified notification fields and notification_preferences table

Revision ID: a1b2c3d4e5f6
Revises: f9b3c7d1e5a8
Create Date: 2026-04-02 00:00:00.000000
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f9b3c7d1e5a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Add new columns to existing notifications table
    # ------------------------------------------------------------------
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("channel", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("event_type", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("feature_source", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("body", sa.Text, nullable=True))
        batch_op.add_column(sa.Column("reference_type", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("reference_id", sa.Integer, nullable=True))
        batch_op.add_column(
            sa.Column("status", sa.String(20), nullable=True, server_default="pending")
        )
        batch_op.add_column(
            sa.Column(
                "sent_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )

    # ------------------------------------------------------------------
    # 2. Create notification_preferences table
    # ------------------------------------------------------------------
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("company_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column(
            "email_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "in_app_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "push_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.UniqueConstraint("user_id", "event_type", name="uq_notif_pref_user_event"),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")

    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_column("sent_at")
        batch_op.drop_column("status")
        batch_op.drop_column("reference_id")
        batch_op.drop_column("reference_type")
        batch_op.drop_column("body")
        batch_op.drop_column("feature_source")
        batch_op.drop_column("event_type")
        batch_op.drop_column("channel")
