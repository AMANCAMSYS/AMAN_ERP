"""add shop floor log table

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa


revision = "i4j5k6l7m8n9"
down_revision = "h3i4j5k6l7m8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shop_floor_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("routing_operation_id", sa.Integer(), sa.ForeignKey("manufacturing_operations.id"), nullable=False),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("employees.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("output_quantity", sa.Numeric(18, 4), server_default="0"),
        sa.Column("scrap_quantity", sa.Numeric(18, 4), server_default="0"),
        sa.Column("downtime_minutes", sa.Numeric(10, 2), server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_shop_floor_logs_work_order_id", "shop_floor_logs", ["work_order_id"])
    op.create_index("ix_shop_floor_logs_status", "shop_floor_logs", ["status"])


def downgrade() -> None:
    op.drop_table("shop_floor_logs")
