"""Add three-way matching tables.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-02

"""
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "match_tolerances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("quantity_percent", sa.Numeric(5, 2), server_default="0"),
        sa.Column("quantity_absolute", sa.Numeric(18, 4), server_default="0"),
        sa.Column("price_percent", sa.Numeric(5, 2), server_default="0"),
        sa.Column("price_absolute", sa.Numeric(18, 4), server_default="0"),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("parties.id"), nullable=True),
        sa.Column("product_category_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )

    op.create_table(
        "three_way_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("match_status", sa.String(30), nullable=False, server_default="matched"),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("matched_by", sa.Integer(), nullable=True),
        sa.Column("exception_approved_by", sa.Integer(), nullable=True),
        sa.Column("exception_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_three_way_matches_status", "three_way_matches", ["match_status"])
    op.create_index("ix_three_way_matches_po", "three_way_matches", ["purchase_order_id"])
    op.create_index("ix_three_way_matches_invoice", "three_way_matches", ["invoice_id"])

    op.create_table(
        "three_way_match_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("three_way_matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("po_line_id", sa.Integer(), sa.ForeignKey("purchase_order_lines.id"), nullable=False),
        sa.Column("grn_ids", JSONB, nullable=True),
        sa.Column("invoice_line_id", sa.Integer(), nullable=True),
        sa.Column("po_quantity", sa.Numeric(18, 4), server_default="0"),
        sa.Column("received_quantity", sa.Numeric(18, 4), server_default="0"),
        sa.Column("invoiced_quantity", sa.Numeric(18, 4), server_default="0"),
        sa.Column("po_unit_price", sa.Numeric(18, 4), server_default="0"),
        sa.Column("invoiced_unit_price", sa.Numeric(18, 4), server_default="0"),
        sa.Column("quantity_variance_pct", sa.Numeric(5, 2), server_default="0"),
        sa.Column("quantity_variance_abs", sa.Numeric(18, 4), server_default="0"),
        sa.Column("price_variance_pct", sa.Numeric(5, 2), server_default="0"),
        sa.Column("price_variance_abs", sa.Numeric(18, 4), server_default="0"),
        sa.Column("tolerance_id", sa.Integer(), sa.ForeignKey("match_tolerances.id"), nullable=True),
        sa.Column("line_status", sa.String(30), nullable=False, server_default="matched"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_three_way_match_lines_match", "three_way_match_lines", ["match_id"])


def downgrade() -> None:
    op.drop_table("three_way_match_lines")
    op.drop_table("three_way_matches")
    op.drop_table("match_tolerances")
