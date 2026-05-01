"""T1.5b: ZATCA CSID lifecycle tracking.

Audit item #7 (P0): "ZATCA: لا توجد إدارة CSID (Cryptographic Stamp Identifier).
شهادات التوقيع الإلكتروني لا تُجدَّد تلقائيًا ولا يوجد كشف لانتهاء صلاحيتها".

Before this migration the CSID was stored as a flat row in `company_settings`
under the key `zatca_csid` with no issuance date, no expiry, and no
renewal/alerting infrastructure. ZATCA Phase 2 PCSIDs expire — typically
after 12 months for production CSIDs and ~2 weeks for compliance CSIDs —
and an expired CSID causes EVERY subsequent invoice submission to be
rejected.

This table:
  * tracks the active and historical CSIDs per company (keyed by id only;
    multi-tenant isolation is provided by the per-company DB);
  * records `issued_at` / `expires_at` so a scheduler job can warn the
    operator at T-30 / T-7 / T-1 days;
  * stores `secret_encrypted` (AES-encrypted PCSID secret) so secrets are
    never written to disk in cleartext;
  * supports rotation history (`status` IN ('active','expired','revoked'))
    so an audit trail survives renewal.
"""
from alembic import op


revision = "0015_zatca_csid"
down_revision = "0014_backfill_treasury_balance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS zatca_csid (
        id              SERIAL PRIMARY KEY,
        environment     VARCHAR(20) NOT NULL DEFAULT 'production'
                        CHECK (environment IN ('compliance','production')),
        pcsid           TEXT NOT NULL,
        secret_encrypted TEXT NOT NULL,
        common_name     VARCHAR(200),
        serial_number   VARCHAR(80),
        issued_at       TIMESTAMPTZ NOT NULL,
        expires_at      TIMESTAMPTZ NOT NULL,
        status          VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','expired','revoked','superseded')),
        last_alert_at   TIMESTAMPTZ,
        last_alert_threshold_days INTEGER,
        renewed_to_id   INTEGER REFERENCES zatca_csid(id) ON DELETE SET NULL,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (expires_at > issued_at)
    );

    -- Only one ACTIVE production CSID at any moment; previous ones move to
    -- 'superseded'. Compliance and production tracks coexist.
    CREATE UNIQUE INDEX IF NOT EXISTS uq_zatca_csid_active
        ON zatca_csid (environment) WHERE status = 'active';

    CREATE INDEX IF NOT EXISTS ix_zatca_csid_expiring
        ON zatca_csid (expires_at) WHERE status = 'active';
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS zatca_csid CASCADE;")
