"""Phase 3 / TASK-026: Inventory-in-Transit bucket + GL account

Adds `inventory.in_transit_quantity` column (tracks stock dispatched from a
source warehouse but not yet received at destination) and provisions the
chart-of-accounts entry 1112 "Inventory In Transit" together with the
`acc_map_in_transit` mapping, mirroring the canonical SQL in
backend/database.py (create_company_tables).

NOTE: Fresh tenants are bootstrapped via the canonical SQL and `alembic stamp
head`; this migration only catches up pre-existing tenant databases.
"""
from alembic import op
import sqlalchemy as sa


revision = "0010_inventory_in_transit"
down_revision = "0009_phase2_locking_and_restrict"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Column on inventory
    conn.execute(sa.text("""
        ALTER TABLE inventory
        ADD COLUMN IF NOT EXISTS in_transit_quantity DECIMAL(18, 4) DEFAULT 0
    """))

    # 2) accounts row 1112 (parent = 11 Current Assets); idempotent
    conn.execute(sa.text("""
        INSERT INTO accounts
            (account_number, account_code, name, name_en, account_type, parent_id)
        SELECT '1112', 'INV-TRN', 'مخزون في الطريق', 'Inventory In Transit',
               'asset', p.id
        FROM accounts p
        WHERE p.account_number = '11'
          AND NOT EXISTS (
              SELECT 1 FROM accounts WHERE account_number = '1112'
          )
    """))

    # 3) company_settings mapping key
    conn.execute(sa.text("""
        INSERT INTO company_settings (setting_key, setting_value)
        SELECT 'acc_map_in_transit', a.id::text
        FROM accounts a
        WHERE a.account_number = '1112'
          AND NOT EXISTS (
              SELECT 1 FROM company_settings
              WHERE setting_key = 'acc_map_in_transit'
          )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DELETE FROM company_settings WHERE setting_key = 'acc_map_in_transit'"
    ))
    conn.execute(sa.text(
        "DELETE FROM accounts WHERE account_number = '1112'"
    ))
    conn.execute(sa.text(
        "ALTER TABLE inventory DROP COLUMN IF EXISTS in_transit_quantity"
    ))
