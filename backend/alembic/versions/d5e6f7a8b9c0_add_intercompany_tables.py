"""Add intercompany entity groups, transactions v2, and account mappings.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-04-03
"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("entity_groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company_id", sa.String(100), nullable=False),
        sa.Column("group_currency", sa.String(10), nullable=False, server_default="SAR"),
        sa.Column("consolidation_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_entity_groups_parent", "entity_groups", ["parent_id"])
    op.create_index("ix_entity_groups_company", "entity_groups", ["company_id"])

    op.create_table(
        "intercompany_transactions_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_entity_id", sa.Integer(), sa.ForeignKey("entity_groups.id"), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), sa.ForeignKey("entity_groups.id"), nullable=False),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("source_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("source_currency", sa.String(10), nullable=False),
        sa.Column("target_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("target_currency", sa.String(10), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 8), nullable=False, server_default="1"),
        sa.Column("source_journal_entry_id", sa.Integer(), nullable=True),
        sa.Column("target_journal_entry_id", sa.Integer(), nullable=True),
        sa.Column("elimination_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("elimination_journal_entry_id", sa.Integer(), nullable=True),
        sa.Column("reference_document", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.CheckConstraint("source_entity_id != target_entity_id", name="ck_ic_txn_diff_entities"),
    )
    op.create_index("ix_ic_txn_v2_source", "intercompany_transactions_v2", ["source_entity_id"])
    op.create_index("ix_ic_txn_v2_target", "intercompany_transactions_v2", ["target_entity_id"])
    op.create_index("ix_ic_txn_v2_status", "intercompany_transactions_v2", ["elimination_status"])

    op.create_table(
        "intercompany_account_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_entity_id", sa.Integer(), sa.ForeignKey("entity_groups.id"), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), sa.ForeignKey("entity_groups.id"), nullable=False),
        sa.Column("source_account_id", sa.Integer(), nullable=False),
        sa.Column("target_account_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_ic_mapping_entities", "intercompany_account_mappings", ["source_entity_id", "target_entity_id"])


def downgrade() -> None:
    op.drop_table("intercompany_account_mappings")
    op.drop_table("intercompany_transactions_v2")
    op.drop_table("entity_groups")
