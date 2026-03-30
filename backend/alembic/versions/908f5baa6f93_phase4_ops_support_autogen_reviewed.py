"""phase4_ops_support_autogen_reviewed

Revision ID: 908f5baa6f93
Revises: 786e754b8d34
Create Date: 2026-03-30 17:07:39.791912
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '908f5baa6f93'
down_revision: Union[str, None] = '786e754b8d34'
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
    # Additive drift-fix for service/document modules only.
    _add_column_if_missing(
        "service_requests",
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
    )
    _add_column_if_missing(
        "service_requests",
        sa.Column("completion_date", sa.Date(), nullable=True),
    )
    _add_column_if_missing(
        "service_requests",
        sa.Column("location", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "service_requests",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "service_requests",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    _add_column_if_missing(
        "service_request_costs",
        sa.Column("quantity", sa.Numeric(precision=10, scale=4), nullable=True, server_default=sa.text("1")),
    )
    _add_column_if_missing(
        "service_request_costs",
        sa.Column("unit_cost", sa.Numeric(precision=15, scale=2), nullable=True, server_default=sa.text("0")),
    )
    _add_column_if_missing(
        "service_request_costs",
        sa.Column("total_cost", sa.Numeric(precision=15, scale=2), nullable=True, server_default=sa.text("0")),
    )
    _add_column_if_missing(
        "service_request_costs",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    _add_column_if_missing(
        "documents",
        sa.Column("related_module", sa.String(length=100), nullable=True),
    )
    _add_column_if_missing(
        "documents",
        sa.Column("related_id", sa.Integer(), nullable=True),
    )
    _add_column_if_missing(
        "documents",
        sa.Column("current_version", sa.Integer(), nullable=True, server_default=sa.text("1")),
    )
    _add_column_if_missing(
        "documents",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    _add_column_if_missing(
        "document_versions",
        sa.Column("change_notes", sa.Text(), nullable=True),
    )
    _add_column_if_missing(
        "document_versions",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    _drop_column_if_exists("document_versions", "created_at")
    _drop_column_if_exists("document_versions", "change_notes")
    _drop_column_if_exists("documents", "updated_at")
    _drop_column_if_exists("documents", "current_version")
    _drop_column_if_exists("documents", "related_id")
    _drop_column_if_exists("documents", "related_module")
    _drop_column_if_exists("service_request_costs", "created_at")
    _drop_column_if_exists("service_request_costs", "total_cost")
    _drop_column_if_exists("service_request_costs", "unit_cost")
    _drop_column_if_exists("service_request_costs", "quantity")
    _drop_column_if_exists("service_requests", "updated_at")
    _drop_column_if_exists("service_requests", "notes")
    _drop_column_if_exists("service_requests", "location")
    _drop_column_if_exists("service_requests", "completion_date")
    _drop_column_if_exists("service_requests", "assigned_at")
