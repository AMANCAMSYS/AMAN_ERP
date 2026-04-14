"""Enhance routing tables — add bom_id, is_default, name, labor_rate_per_hour

Revision ID: j5k6l7m8n9o0
Revises: i4j5k6l7m8n9
Create Date: 2026-04-13

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "j5k6l7m8n9o0"
down_revision = "i4j5k6l7m8n9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # manufacturing_routes: add bom_id, is_default
    op.add_column("manufacturing_routes", sa.Column("bom_id", sa.Integer(), nullable=True))
    op.add_column("manufacturing_routes", sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=True))
    op.create_foreign_key(
        "fk_routes_bom_id",
        "manufacturing_routes",
        "bill_of_materials",
        ["bom_id"],
        ["id"],
    )

    # manufacturing_operations: add name, labor_rate_per_hour, updated_at
    op.add_column("manufacturing_operations", sa.Column("name", sa.String(255), nullable=True))
    op.add_column("manufacturing_operations", sa.Column("labor_rate_per_hour", sa.Numeric(18, 4), server_default=sa.text("0"), nullable=True))
    op.add_column("manufacturing_operations", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))


def downgrade() -> None:
    op.drop_column("manufacturing_operations", "updated_at")
    op.drop_column("manufacturing_operations", "labor_rate_per_hour")
    op.drop_column("manufacturing_operations", "name")
    op.drop_constraint("fk_routes_bom_id", "manufacturing_routes", type_="foreignkey")
    op.drop_column("manufacturing_routes", "is_default")
    op.drop_column("manufacturing_routes", "bom_id")
