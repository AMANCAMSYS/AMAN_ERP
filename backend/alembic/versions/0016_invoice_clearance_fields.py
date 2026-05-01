"""T1.5c: invoice ZATCA clearance lifecycle fields.

Audit item #6 (P0): "ZATCA: لا يوجد تدفق clearance إلزامي (Phase 2)".

The pre-existing column `invoices.zatca_status` (added in an earlier
migration) tracks LOCAL artefact generation: hash, signature, and QR
were computed and stored. It does NOT reflect whether the invoice was
actually accepted by ZATCA's clearance/reporting endpoint.

This migration introduces an orthogonal lifecycle for the *remote*
clearance result so the two concerns (local artefact generation vs.
remote acceptance) cannot be confused. The new `zatca_clearance_status`
defaults to ``'not_required'`` because the surrounding feature flag
(``ZATCA_PHASE2_ENFORCE``, see ``backend/config.py``) is off by default;
older rows therefore remain semantically valid without any backfill.
"""
from alembic import op


revision = "0016_invoice_clearance_fields"
down_revision = "0015_zatca_csid"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE invoices
        ADD COLUMN IF NOT EXISTS zatca_clearance_status VARCHAR(30)
            NOT NULL DEFAULT 'not_required'
            CHECK (zatca_clearance_status IN (
                'not_required',     -- enforcement off or non-SA tenant
                'pending_clearance',-- queued; outbox will retry
                'cleared',          -- ZATCA accepted (B2B clearance)
                'reported',         -- ZATCA accepted (B2C reporting)
                'rejected'          -- ZATCA rejected definitively
            )),
        ADD COLUMN IF NOT EXISTS zatca_cleared_at      TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS zatca_cleared_uuid    VARCHAR(80),
        ADD COLUMN IF NOT EXISTS zatca_clearance_error TEXT;

    CREATE INDEX IF NOT EXISTS ix_invoices_zatca_clearance_status
        ON invoices (zatca_clearance_status)
        WHERE zatca_clearance_status IN ('pending_clearance','rejected');
    """)


def downgrade() -> None:
    op.execute("""
    DROP INDEX IF EXISTS ix_invoices_zatca_clearance_status;
    ALTER TABLE invoices
        DROP COLUMN IF EXISTS zatca_clearance_error,
        DROP COLUMN IF EXISTS zatca_cleared_uuid,
        DROP COLUMN IF EXISTS zatca_cleared_at,
        DROP COLUMN IF EXISTS zatca_clearance_status;
    """)
