"""widen asset money columns from NUMERIC(15,2) to DECIMAL(18,4)

Revision ID: 0005_widen_asset_money_columns
Revises: 0004_add_updated_at_columns
Create Date: 2026-04-20

Widen 7 monetary columns across 4 asset-related tables from
NUMERIC(15,2) to DECIMAL(18,4) to comply with Constitution I
(no float for money, use DECIMAL(18,4) for all monetary fields).

Tables affected: asset_transfers, asset_revaluations,
asset_insurance, asset_maintenance.

Constitution XXVIII: Applied together with database.py CREATE TABLE update.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_widen_asset_money_columns"
down_revision = "0004_add_updated_at_columns"
branch_labels = None
depends_on = None

# (table, column) pairs to widen
_COLUMNS = [
    ("asset_transfers", "book_value_at_transfer"),
    ("asset_revaluations", "old_value"),
    ("asset_revaluations", "new_value"),
    ("asset_revaluations", "difference"),
    ("asset_insurance", "premium_amount"),
    ("asset_insurance", "coverage_amount"),
    ("asset_maintenance", "cost"),
]


def upgrade():
    for table, column in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.Numeric(18, 4),
            existing_type=sa.Numeric(15, 2),
        )


def downgrade():
    for table, column in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.Numeric(15, 2),
            existing_type=sa.Numeric(18, 4),
        )
