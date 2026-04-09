"""Create subscription billing tables.

Run via:
    cd backend && python migrations/create_subscription_tables.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings

DDL = """
-- Subscription Plans
CREATE TABLE IF NOT EXISTS subscription_plans (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    billing_frequency VARCHAR(20) NOT NULL DEFAULT 'monthly',
    base_amount     NUMERIC(18,4) NOT NULL DEFAULT 0,
    currency        VARCHAR(3) NOT NULL DEFAULT 'SAR',
    trial_period_days INTEGER NOT NULL DEFAULT 0,
    auto_renewal    BOOLEAN NOT NULL DEFAULT TRUE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_by      VARCHAR(50),
    updated_by      VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Subscription Enrollments
CREATE TABLE IF NOT EXISTS subscription_enrollments (
    id                  SERIAL PRIMARY KEY,
    customer_id         INTEGER NOT NULL,
    plan_id             INTEGER NOT NULL REFERENCES subscription_plans(id),
    enrollment_date     DATE NOT NULL DEFAULT CURRENT_DATE,
    trial_end_date      DATE,
    next_billing_date   DATE NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'active',
    cancelled_at        TIMESTAMPTZ,
    cancellation_reason TEXT,
    failed_payment_count INTEGER NOT NULL DEFAULT 0,
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    created_by          VARCHAR(50),
    updated_by          VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sub_enroll_customer ON subscription_enrollments(customer_id);
CREATE INDEX IF NOT EXISTS idx_sub_enroll_plan ON subscription_enrollments(plan_id);
CREATE INDEX IF NOT EXISTS idx_sub_enroll_status ON subscription_enrollments(status);

-- Subscription Invoices (link table)
CREATE TABLE IF NOT EXISTS subscription_invoices (
    id                      SERIAL PRIMARY KEY,
    enrollment_id           INTEGER NOT NULL REFERENCES subscription_enrollments(id),
    invoice_id              INTEGER,
    billing_period_start    DATE NOT NULL,
    billing_period_end      DATE NOT NULL,
    is_prorated             BOOLEAN NOT NULL DEFAULT FALSE,
    proration_details       JSONB,
    created_by              VARCHAR(50),
    updated_by              VARCHAR(50),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sub_inv_enrollment ON subscription_invoices(enrollment_id);
"""

def run():
    # Get all company databases
    eng = create_engine(settings.DATABASE_URL, isolation_level="AUTOCOMMIT")
    with eng.connect() as c:
        dbs = c.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aman_%'")).fetchall()
    eng.dispose()

    base_url = settings.DATABASE_URL.rsplit('/', 1)[0]

    for (db_name,) in dbs:
        url = f"{base_url}/{db_name}"
        db_eng = create_engine(url, isolation_level="AUTOCOMMIT")
        try:
            with db_eng.connect() as c:
                c.execute(text(DDL))
            print(f"✅ {db_name}: subscription tables created")
        except Exception as e:
            print(f"❌ {db_name}: {e}")
        finally:
            db_eng.dispose()

if __name__ == "__main__":
    run()
