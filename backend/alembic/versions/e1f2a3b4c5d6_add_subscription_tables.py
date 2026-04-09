"""add subscription billing tables

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("billing_frequency", sa.String(20), server_default="'monthly'", nullable=False),
        sa.Column("base_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(3), server_default="'SAR'", nullable=False),
        sa.Column("trial_period_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("auto_renewal", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(100), nullable=True),
    )

    op.create_table(
        "subscription_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("parties.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("enrollment_date", sa.Date(), nullable=False),
        sa.Column("trial_end_date", sa.Date(), nullable=True),
        sa.Column("next_billing_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), server_default="'active'", nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("failed_payment_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(100), nullable=True),
    )

    op.create_table(
        "subscription_invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "enrollment_id",
            sa.Integer(),
            sa.ForeignKey("subscription_enrollments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            sa.Integer(),
            sa.ForeignKey("invoices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("billing_period_start", sa.Date(), nullable=False),
        sa.Column("billing_period_end", sa.Date(), nullable=False),
        sa.Column("is_prorated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("proration_details", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(100), nullable=True),
    )

    op.create_index(
        "ix_subscription_enrollments_customer_plan",
        "subscription_enrollments",
        ["customer_id", "plan_id"],
    )
    op.create_index(
        "ix_subscription_enrollments_next_billing",
        "subscription_enrollments",
        ["next_billing_date"],
    )
    op.create_index(
        "ix_subscription_invoices_enrollment",
        "subscription_invoices",
        ["enrollment_id"],
    )


def downgrade():
    op.drop_index("ix_subscription_invoices_enrollment", table_name="subscription_invoices")
    op.drop_index("ix_subscription_enrollments_next_billing", table_name="subscription_enrollments")
    op.drop_index("ix_subscription_enrollments_customer_plan", table_name="subscription_enrollments")
    op.drop_table("subscription_invoices")
    op.drop_table("subscription_enrollments")
    op.drop_table("subscription_plans")
