"""T1.2: backfill UFX-GAIN / UFX-LOSS accounts for existing tenants.

The currency revaluation endpoint (`POST /currencies/revaluate`) requires
two GL accounts:
  - 42021 Unrealized FX Gains  (legacy code: UFX-GAIN)
  - 71011 Unrealized FX Losses (legacy code: UFX-LOSS)

Newer companies created via `services/industry_coa_templates.py` will receive
these via the seed (added in the same change as this migration). This
migration backfills tenants whose COA was seeded before the templates were
updated.

Idempotent: only inserts when the account_number does not already exist.
"""
from alembic import op


revision = "0013_add_ufx_accounts"
down_revision = "0012_phase5_world_comparison"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        -- Resolve parent ids by account_number; only insert when missing.
        WITH parents AS (
            SELECT
                (SELECT id FROM accounts WHERE account_number = '42' LIMIT 1) AS parent_42,
                (SELECT id FROM accounts WHERE account_number = '7'  LIMIT 1) AS parent_7
        )
        INSERT INTO accounts (account_number, account_code, name, name_en, account_type, parent_id, is_header, is_active)
        SELECT v.account_number, v.account_code, v.name, v.name_en, v.account_type, v.parent_id, FALSE, TRUE
        FROM (
            SELECT '42021' AS account_number, '42021' AS account_code,
                   'أرباح فروق عملة (غير محققة)' AS name, 'Unrealized FX Gains' AS name_en,
                   'revenue' AS account_type, p.parent_42 AS parent_id
            FROM parents p
            UNION ALL
            SELECT '71011', '71011',
                   'خسائر فروق عملة (غير محققة)', 'Unrealized FX Losses',
                   'expense', p.parent_7
            FROM parents p
        ) AS v
        WHERE NOT EXISTS (
            SELECT 1 FROM accounts a WHERE a.account_number = v.account_number
        );

        -- Also ensure the legacy code rows (if a tenant created them via the
        -- old database.py default seed) remain reachable: nothing to do.
        """
    )


def downgrade() -> None:
    # Safe to remove only if no journal lines reference these accounts.
    op.execute(
        """
        DELETE FROM accounts
        WHERE account_number IN ('42021', '71011')
          AND id NOT IN (SELECT DISTINCT account_id FROM journal_lines WHERE account_id IS NOT NULL);
        """
    )
