"""phase3_treasury_tax_projects_autogen_reviewed

Revision ID: 786e754b8d34
Revises: 2bd1b4bb466a
Create Date: 2026-03-30 16:55:32.793005
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '786e754b8d34'
down_revision: Union[str, None] = '2bd1b4bb466a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = :table_name
                )
                """
            ),
            {"table_name": table_name},
        ).scalar()
    )


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                      AND column_name = :column_name
                )
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar()
    )


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if _table_exists(table_name) and not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def _drop_column_if_exists(table_name: str, column_name: str) -> None:
    if _table_exists(table_name) and _column_exists(table_name, column_name):
        op.drop_column(table_name, column_name)


def upgrade() -> None:
    # Additive drift-fix only for Phase 3 modeled modules.
    _add_column_if_missing(
        "projects",
        sa.Column("party_id", sa.Integer(), nullable=True),
    )
    _add_column_if_missing(
        "projects",
        sa.Column("retainer_amount", sa.Numeric(precision=18, scale=4), nullable=True, server_default=sa.text("0")),
    )
    _add_column_if_missing(
        "projects",
        sa.Column("billing_cycle", sa.String(length=20), nullable=True, server_default=sa.text("'monthly'")),
    )
    _add_column_if_missing(
        "projects",
        sa.Column("last_billed_date", sa.Date(), nullable=True),
    )
    _add_column_if_missing(
        "projects",
        sa.Column("next_billing_date", sa.Date(), nullable=True),
    )

    _add_column_if_missing(
        "tax_rates",
        sa.Column("jurisdiction_code", sa.String(length=2), nullable=True),
    )
    _add_column_if_missing(
        "tax_rates",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    _drop_column_if_exists("tax_rates", "updated_at")
    _drop_column_if_exists("tax_rates", "jurisdiction_code")
    _drop_column_if_exists("projects", "next_billing_date")
    _drop_column_if_exists("projects", "last_billed_date")
    _drop_column_if_exists("projects", "billing_cycle")
    _drop_column_if_exists("projects", "retainer_amount")
    _drop_column_if_exists("projects", "party_id")
