"""phase5_targeted_missing_tables

Revision ID: e1c5a8b6d6f2
Revises: 908f5baa6f93
Create Date: 2026-03-30 18:10:00.000000

Create missing service/document detail tables for specific tenants only.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1c5a8b6d6f2"
down_revision: Union[str, None] = "908f5baa6f93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TARGET_DATABASES = {"aman_8f3e504b", "aman_fcfa5fae"}


def _current_database() -> str:
    bind = op.get_bind()
    return str(bind.execute(sa.text("SELECT current_database()")).scalar())


def _is_target_database() -> bool:
    return _current_database() in TARGET_DATABASES


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


def upgrade() -> None:
    if not _is_target_database():
        return

    if not _table_exists("service_request_costs"):
        op.create_table(
            "service_request_costs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "service_request_id",
                sa.Integer(),
                sa.ForeignKey("service_requests.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("cost_type", sa.String(length=50), nullable=True, server_default=sa.text("'other'")),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("quantity", sa.Numeric(precision=10, scale=4), nullable=True, server_default=sa.text("1")),
            sa.Column("unit_cost", sa.Numeric(precision=15, scale=2), nullable=True, server_default=sa.text("0")),
            sa.Column("total_cost", sa.Numeric(precision=15, scale=2), nullable=True, server_default=sa.text("0")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.CheckConstraint(
                "cost_type IN ('labor', 'parts', 'travel', 'other')",
                name="ck_service_request_costs_cost_type",
            ),
        )

    if not _table_exists("document_versions"):
        op.create_table(
            "document_versions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "document_id",
                sa.Integer(),
                sa.ForeignKey("documents.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column("version_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
            sa.Column("file_name", sa.String(length=255), nullable=True),
            sa.Column("file_path", sa.Text(), nullable=True),
            sa.Column("file_size", sa.Integer(), nullable=True),
            sa.Column("change_notes", sa.Text(), nullable=True),
            sa.Column(
                "uploaded_by",
                sa.Integer(),
                sa.ForeignKey("company_users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )


def downgrade() -> None:
    if not _is_target_database():
        return

    if _table_exists("document_versions"):
        op.drop_table("document_versions")

    if _table_exists("service_request_costs"):
        op.drop_table("service_request_costs")
