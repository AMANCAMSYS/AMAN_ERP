"""expense_policies_created_by_drift_fix

Revision ID: a4b2c9d8e6f1
Revises: f3a1d9c42b7e
Create Date: 2026-03-30 22:05:00.000000

Normalize expense_policies across tenants by adding missing created_by.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4b2c9d8e6f1"
down_revision: Union[str, None] = "f3a1d9c42b7e"
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


def upgrade() -> None:
    if not _table_exists("expense_policies"):
        return

    if not _column_exists("expense_policies", "created_by"):
        op.add_column(
            "expense_policies",
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("company_users.id"), nullable=True),
        )


def downgrade() -> None:
    # Intentional no-op: some tenants already had this column before this revision.
    # Dropping it in downgrade would remove canonical schema from those tenants.
    pass
