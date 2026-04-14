"""add demand forecast tables

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa


revision = "h3i4j5k6l7m8"
down_revision = "g2h3i4j5k6l7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "demand_forecasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=True),
        sa.Column("forecast_method", sa.String(50), nullable=False),
        sa.Column("generated_date", sa.Date(), nullable=False),
        sa.Column("generated_by", sa.Integer(), sa.ForeignKey("company_users.id"), nullable=False),
        sa.Column("history_months_used", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
    )
    op.create_index("ix_demand_forecasts_product_id", "demand_forecasts", ["product_id"])
    op.create_index("ix_demand_forecasts_generated_date", "demand_forecasts", ["generated_date"])

    op.create_table(
        "demand_forecast_periods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("forecast_id", sa.Integer(), sa.ForeignKey("demand_forecasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("projected_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("confidence_lower", sa.Numeric(18, 4), nullable=False),
        sa.Column("confidence_upper", sa.Numeric(18, 4), nullable=False),
        sa.Column("manual_adjustment", sa.Numeric(18, 4), server_default="0"),
        sa.Column("adjusted_quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
    )
    op.create_index("ix_demand_forecast_periods_forecast_id", "demand_forecast_periods", ["forecast_id"])


def downgrade() -> None:
    op.drop_table("demand_forecast_periods")
    op.drop_table("demand_forecasts")
