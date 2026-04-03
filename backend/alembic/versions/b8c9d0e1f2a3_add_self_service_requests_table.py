"""add self_service_requests table

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "self_service_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employee_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=False, index=True),
        sa.Column("request_type", sa.String(30), nullable=False, comment="leave | profile_update | document_request"),
        sa.Column("details", JSONB, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft", comment="draft | pending | approved | rejected | completed"),
        sa.Column("approver_id", sa.Integer, sa.ForeignKey("employees.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        # AuditMixin columns
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_self_service_requests_status", "self_service_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_self_service_requests_status", table_name="self_service_requests")
    op.drop_table("self_service_requests")
