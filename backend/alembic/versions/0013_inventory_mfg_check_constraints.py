"""INV-F2 + MFG-F2: DB-level CHECK constraints.

- INV-F2: stock movements / stock levels must not go negative.
  Adds CHECK (quantity >= 0) on inventory balance tables.
- MFG-F2: BOM components percentage must be bounded 0..100.
  Adds CHECK (percentage >= 0 AND percentage <= 100).

Uses IF NOT EXISTS / DO blocks so the migration is idempotent across tenants
that may or may not have every inventory/BOM table materialised.
"""
from alembic import op


revision = "0013_inventory_mfg_check_constraints"
down_revision = "0012_phase5_world_comparison"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- ── INV-F2: non-negative stock levels ─────────────────────────────────
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'stock_levels' AND table_schema = current_schema()
        ) AND NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_stock_levels_qty_nonneg'
        ) THEN
            BEGIN
                ALTER TABLE stock_levels
                    ADD CONSTRAINT ck_stock_levels_qty_nonneg
                    CHECK (quantity >= 0) NOT VALID;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'Skipping ck_stock_levels_qty_nonneg: %', SQLERRM;
            END;
        END IF;
    END $$;

    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'inventory_balances' AND table_schema = current_schema()
        ) AND NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_inventory_balances_qty_nonneg'
        ) THEN
            BEGIN
                ALTER TABLE inventory_balances
                    ADD CONSTRAINT ck_inventory_balances_qty_nonneg
                    CHECK (quantity_on_hand >= 0) NOT VALID;
            EXCEPTION WHEN others THEN
                RAISE NOTICE 'Skipping ck_inventory_balances_qty_nonneg: %', SQLERRM;
            END;
        END IF;
    END $$;

    -- ── MFG-F2: BOM percentage bounded 0..100 ─────────────────────────────
    DO $$
    DECLARE
        pct_col text;
        tbl text;
    BEGIN
        FOR tbl IN SELECT unnest(ARRAY['bom_items', 'bom_components', 'bill_of_materials_items']) LOOP
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = tbl AND table_schema = current_schema()
            ) THEN
                SELECT column_name INTO pct_col
                FROM information_schema.columns
                WHERE table_name = tbl
                  AND table_schema = current_schema()
                  AND column_name IN ('percentage', 'scrap_percentage', 'percent')
                LIMIT 1;

                IF pct_col IS NOT NULL AND NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'ck_' || tbl || '_pct_bounded'
                ) THEN
                    BEGIN
                        EXECUTE format(
                            'ALTER TABLE %I ADD CONSTRAINT %I CHECK (%I >= 0 AND %I <= 100) NOT VALID',
                            tbl, 'ck_' || tbl || '_pct_bounded', pct_col, pct_col
                        );
                    EXCEPTION WHEN others THEN
                        RAISE NOTICE 'Skipping ck_%_pct_bounded: %', tbl, SQLERRM;
                    END;
                END IF;
            END IF;
        END LOOP;
    END $$;
    """)


def downgrade() -> None:
    op.execute("""
    DO $$
    DECLARE
        c text;
    BEGIN
        FOR c IN SELECT conname FROM pg_constraint
                 WHERE conname IN (
                    'ck_stock_levels_qty_nonneg',
                    'ck_inventory_balances_qty_nonneg',
                    'ck_bom_items_pct_bounded',
                    'ck_bom_components_pct_bounded',
                    'ck_bill_of_materials_items_pct_bounded'
                 ) LOOP
            EXECUTE format(
                'ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I',
                (SELECT conrelid::regclass::text FROM pg_constraint WHERE conname = c),
                c
            );
        END LOOP;
    END $$;
    """)
