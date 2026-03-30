"""phase2_models_autogen_reviewed

Revision ID: 2bd1b4bb466a
Revises: da58152b4322
Create Date: 2026-03-30 16:34:19.724119
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '2bd1b4bb466a'
down_revision: Union[str, None] = 'da58152b4322'
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
    # Additive drift-fix only: keep migration safe across mixed tenant states.
    _add_column_if_missing(
        "purchase_orders",
        sa.Column("effect_type", sa.String(length=20), nullable=True, server_default=sa.text("'discount'")),
    )
    _add_column_if_missing(
        "purchase_orders",
        sa.Column("effect_percentage", sa.Numeric(precision=5, scale=2), nullable=True, server_default=sa.text("0")),
    )
    _add_column_if_missing(
        "purchase_orders",
        sa.Column("markup_amount", sa.Numeric(precision=18, scale=4), nullable=True, server_default=sa.text("0")),
    )

    _add_column_if_missing(
        "payroll_entries",
        sa.Column("currency", sa.String(length=3), nullable=True),
    )
    _add_column_if_missing(
        "payroll_entries",
        sa.Column("exchange_rate", sa.Numeric(precision=18, scale=6), nullable=True, server_default=sa.text("1.0")),
    )
    _add_column_if_missing(
        "payroll_entries",
        sa.Column("net_salary_base", sa.Numeric(precision=18, scale=4), nullable=True, server_default=sa.text("0")),
    )

    _add_column_if_missing(
        "invoices",
        sa.Column("effect_type", sa.String(length=20), nullable=True, server_default=sa.text("'discount'")),
    )
    _add_column_if_missing(
        "invoices",
        sa.Column("effect_percentage", sa.Numeric(precision=5, scale=2), nullable=True, server_default=sa.text("0")),
    )
    _add_column_if_missing(
        "invoices",
        sa.Column("markup_amount", sa.Numeric(precision=18, scale=4), nullable=True, server_default=sa.text("0")),
    )

    _add_column_if_missing(
        "invoice_lines",
        sa.Column("markup", sa.Numeric(precision=18, scale=4), nullable=True, server_default=sa.text("0")),
    )

    _add_column_if_missing(
        "party_groups",
        sa.Column("effect_type", sa.String(length=20), nullable=True, server_default=sa.text("'discount'")),
    )
    _add_column_if_missing(
        "party_groups",
        sa.Column("application_scope", sa.String(length=20), nullable=True, server_default=sa.text("'total'")),
    )


def downgrade() -> None:
    _drop_column_if_exists("party_groups", "application_scope")
    _drop_column_if_exists("party_groups", "effect_type")
    _drop_column_if_exists("invoice_lines", "markup")
    _drop_column_if_exists("invoices", "markup_amount")
    _drop_column_if_exists("invoices", "effect_percentage")
    _drop_column_if_exists("invoices", "effect_type")
    _drop_column_if_exists("payroll_entries", "net_salary_base")
    _drop_column_if_exists("payroll_entries", "exchange_rate")
    _drop_column_if_exists("payroll_entries", "currency")
    _drop_column_if_exists("purchase_orders", "markup_amount")
    _drop_column_if_exists("purchase_orders", "effect_percentage")
    _drop_column_if_exists("purchase_orders", "effect_type")
