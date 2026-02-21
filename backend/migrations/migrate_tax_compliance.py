"""
Migration: Add Tax Compliance / Jurisdiction System
====================================================
Adds:
  1. tax_regimes          — master list of tax types per country
  2. branch_tax_settings  — per-branch tax jurisdiction overrides
  3. company_tax_settings  — company-level VAT/Zakat registration
  4. tax_returns.branch_id + jurisdiction_code  — link returns to jurisdiction
  5. Seed data for SA, SY, AE, EG, JO, KW, BH, OM, QA, IQ, LB, TR, US, GB, DE
"""

from sqlalchemy import text
from database import get_db_connection, engine as system_engine
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Country → Tax regime seed data
# ═══════════════════════════════════════════════════════════════════════════════
TAX_REGIMES_SEED = [
    # ── Saudi Arabia (SA) ─────────────────────────────────────────────────────
    ("SA", "vat",           "ضريبة القيمة المضافة",       "Value Added Tax (VAT)",          15.00, True,  "all",           "quarterly"),
    ("SA", "zakat",         "الزكاة",                     "Zakat",                           2.50, True,  "saudi_owned",   "annual"),
    ("SA", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           20.00, True,  "foreign_owned", "annual"),
    ("SA", "withholding",   "ضريبة الاستقطاع",            "Withholding Tax",                 5.00, False, "cross_border",  "monthly"),
    ("SA", "excise",        "الضريبة الانتقائية",          "Excise Tax",                     50.00, False, "specific_goods","quarterly"),
    ("SA", "real_estate",   "ضريبة التصرفات العقارية",     "Real Estate Transaction Tax",     5.00, False, "real_estate",   "per_transaction"),

    # ── Syria (SY) ────────────────────────────────────────────────────────────
    ("SY", "income_tax",    "ضريبة الدخل",                "Income Tax",                     22.00, True,  "all",           "annual"),
    ("SY", "salary_tax",    "ضريبة الرواتب والأجور",       "Salary Tax",                      0.00, True,  "all",           "monthly"),
    ("SY", "stamp_duty",    "رسوم الطوابع",               "Stamp Duty",                      0.60, False, "contracts",     "per_transaction"),
    ("SY", "rental_tax",    "ضريبة ريع العقارات",          "Rental Income Tax",              10.00, False, "rental_income", "annual"),
    ("SY", "customs",       "الرسوم الجمركية",             "Customs Duties",                  0.00, False, "imports",       "per_transaction"),

    # ── UAE (AE) ──────────────────────────────────────────────────────────────
    ("AE", "vat",           "ضريبة القيمة المضافة",       "Value Added Tax (VAT)",           5.00, True,  "all",           "quarterly"),
    ("AE", "corporate_tax", "ضريبة الشركات",              "Corporate Tax",                   9.00, True,  "all",           "annual"),
    ("AE", "excise",        "الضريبة الانتقائية",          "Excise Tax",                     50.00, False, "specific_goods","quarterly"),

    # ── Egypt (EG) ────────────────────────────────────────────────────────────
    ("EG", "vat",           "ضريبة القيمة المضافة",       "Value Added Tax (VAT)",          14.00, True,  "all",           "monthly"),
    ("EG", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           22.50, True,  "all",           "annual"),
    ("EG", "withholding",   "ضريبة الخصم من المنبع",       "Withholding Tax",                 5.00, False, "cross_border",  "quarterly"),
    ("EG", "stamp_duty",    "ضريبة الدمغة",               "Stamp Duty",                      0.90, False, "contracts",     "per_transaction"),
    ("EG", "social_dev",    "رسوم التنمية",               "Social Development Levy",         2.00, False, "all",           "annual"),

    # ── Jordan (JO) ───────────────────────────────────────────────────────────
    ("JO", "sales_tax",     "ضريبة المبيعات",             "General Sales Tax",              16.00, True,  "all",           "monthly"),
    ("JO", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           20.00, True,  "all",           "annual"),
    ("JO", "social_srv",    "ضريبة الخدمات الاجتماعية",    "Social Services Tax",             1.00, False, "all",           "annual"),

    # ── Kuwait (KW) ───────────────────────────────────────────────────────────
    ("KW", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           15.00, True,  "foreign_owned", "annual"),
    ("KW", "zakat",         "الزكاة",                     "Zakat (National Labour Support)", 1.00, True,  "all",           "annual"),
    ("KW", "nlst",          "ضريبة دعم العمالة",           "NLST",                            2.50, True,  "all",           "annual"),

    # ── Bahrain (BH) ──────────────────────────────────────────────────────────
    ("BH", "vat",           "ضريبة القيمة المضافة",       "Value Added Tax (VAT)",          10.00, True,  "all",           "quarterly"),

    # ── Oman (OM) ─────────────────────────────────────────────────────────────
    ("OM", "vat",           "ضريبة القيمة المضافة",       "Value Added Tax (VAT)",           5.00, True,  "all",           "quarterly"),
    ("OM", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           15.00, True,  "all",           "annual"),

    # ── Qatar (QA) ────────────────────────────────────────────────────────────
    ("QA", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           10.00, True,  "foreign_owned", "annual"),

    # ── Iraq (IQ) ─────────────────────────────────────────────────────────────
    ("IQ", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           15.00, True,  "all",           "annual"),
    ("IQ", "withholding",   "ضريبة الاستقطاع",            "Withholding Tax",                 5.00, False, "cross_border",  "per_transaction"),

    # ── Lebanon (LB) ──────────────────────────────────────────────────────────
    ("LB", "vat",           "ضريبة القيمة المضافة",       "Value Added Tax (VAT)",          11.00, True,  "all",           "quarterly"),
    ("LB", "income_tax",    "ضريبة الدخل",                "Corporate Income Tax",           17.00, True,  "all",           "annual"),

    # ── Turkey (TR) ───────────────────────────────────────────────────────────
    ("TR", "vat",           "ضريبة القيمة المضافة (KDV)", "Value Added Tax (KDV)",          20.00, True,  "all",           "monthly"),
    ("TR", "income_tax",    "ضريبة الشركات",              "Corporate Tax (Kurumlar)",       25.00, True,  "all",           "quarterly"),
    ("TR", "withholding",   "ضريبة الاستقطاع",            "Withholding Tax (Stopaj)",       15.00, False, "cross_border",  "monthly"),
]


def run_migration(company_id: str):
    """Run tax compliance migration for a single company."""
    db = get_db_connection(company_id)
    try:
        # ── 1. Create tax_regimes table ───────────────────────────────────────
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS tax_regimes (
                id SERIAL PRIMARY KEY,
                country_code VARCHAR(2) NOT NULL,
                tax_type VARCHAR(50) NOT NULL,
                name_ar VARCHAR(255) NOT NULL,
                name_en VARCHAR(255) NOT NULL,
                default_rate NUMERIC(10, 4) DEFAULT 0,
                is_required BOOLEAN DEFAULT FALSE,
                applies_to VARCHAR(50) DEFAULT 'all',
                filing_frequency VARCHAR(20) DEFAULT 'quarterly',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(country_code, tax_type)
            );
        """))

        # ── 2. Create branch_tax_settings table ──────────────────────────────
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS branch_tax_settings (
                id SERIAL PRIMARY KEY,
                branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
                tax_regime_id INTEGER NOT NULL REFERENCES tax_regimes(id) ON DELETE CASCADE,
                is_registered BOOLEAN DEFAULT FALSE,
                registration_number VARCHAR(100),
                custom_rate NUMERIC(10, 4),
                is_exempt BOOLEAN DEFAULT FALSE,
                exemption_reason TEXT,
                exemption_certificate VARCHAR(100),
                exemption_expiry DATE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(branch_id, tax_regime_id)
            );
        """))

        # ── 3. Create company_tax_settings table ─────────────────────────────
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS company_tax_settings (
                id SERIAL PRIMARY KEY,
                country_code VARCHAR(2) NOT NULL,
                is_vat_registered BOOLEAN DEFAULT FALSE,
                vat_number VARCHAR(50),
                zakat_number VARCHAR(50),
                tax_registration_number VARCHAR(100),
                commercial_registry VARCHAR(100),
                fiscal_year_start VARCHAR(5) DEFAULT '01-01',
                default_filing_frequency VARCHAR(20) DEFAULT 'quarterly',
                zatca_phase VARCHAR(20) DEFAULT 'none',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(country_code)
            );
        """))

        # ── 4. Add branch_id & jurisdiction_code to tax_returns ──────────────
        # Check if columns exist before adding
        cols = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'tax_returns'
        """)).fetchall()
        existing_cols = {r[0] for r in cols}

        if 'branch_id' not in existing_cols:
            db.execute(text("ALTER TABLE tax_returns ADD COLUMN branch_id INTEGER REFERENCES branches(id)"))
        if 'jurisdiction_code' not in existing_cols:
            db.execute(text("ALTER TABLE tax_returns ADD COLUMN jurisdiction_code VARCHAR(2)"))

        # ── 5. Add country_code to tax_rates (if not exists already) ─────────
        rate_cols = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'tax_rates'
        """)).fetchall()
        rate_existing = {r[0] for r in rate_cols}
        if 'jurisdiction_code' not in rate_existing:
            db.execute(text("ALTER TABLE tax_rates ADD COLUMN jurisdiction_code VARCHAR(2)"))

        # ── 6. Seed tax_regimes ───────────────────────────────────────────────
        existing_regimes = db.execute(text("SELECT COUNT(*) FROM tax_regimes")).scalar()
        if existing_regimes == 0:
            for regime in TAX_REGIMES_SEED:
                db.execute(text("""
                    INSERT INTO tax_regimes (country_code, tax_type, name_ar, name_en, default_rate, 
                                            is_required, applies_to, filing_frequency)
                    VALUES (:cc, :type, :ar, :en, :rate, :req, :applies, :freq)
                    ON CONFLICT (country_code, tax_type) DO NOTHING
                """), {
                    "cc": regime[0], "type": regime[1], "ar": regime[2], "en": regime[3],
                    "rate": regime[4], "req": regime[5], "applies": regime[6], "freq": regime[7]
                })

        # ── 7. Auto-setup company_tax_settings from company's country ────────
        company_country = db.execute(text(
            "SELECT setting_value FROM company_settings WHERE setting_key = 'company_country'"
        )).scalar()

        if company_country:
            db.execute(text("""
                INSERT INTO company_tax_settings (country_code) VALUES (:cc)
                ON CONFLICT (country_code) DO NOTHING
            """), {"cc": company_country})

            # Auto-register branch tax settings for the default branch
            default_branch = db.execute(text(
                "SELECT id, country_code FROM branches WHERE is_default = TRUE LIMIT 1"
            )).fetchone()
            if default_branch:
                branch_cc = default_branch.country_code or company_country
                required_regimes = db.execute(text("""
                    SELECT id FROM tax_regimes 
                    WHERE country_code = :cc AND is_required = TRUE AND is_active = TRUE
                """), {"cc": branch_cc}).fetchall()

                for regime in required_regimes:
                    db.execute(text("""
                        INSERT INTO branch_tax_settings (branch_id, tax_regime_id, is_registered, is_active)
                        VALUES (:bid, :rid, FALSE, TRUE)
                        ON CONFLICT (branch_id, tax_regime_id) DO NOTHING
                    """), {"bid": default_branch.id, "rid": regime.id})

        # ── 8. Indexes ───────────────────────────────────────────────────────
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_tax_regimes_country ON tax_regimes(country_code)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_branch_tax_settings_branch ON branch_tax_settings(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_branch_tax_settings_regime ON branch_tax_settings(tax_regime_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_tax_returns_branch ON tax_returns(branch_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_tax_returns_jurisdiction ON tax_returns(jurisdiction_code)"))

        db.commit()
        logger.info(f"✅ Tax compliance migration completed for company {company_id}")
        return True, "Tax compliance migration completed successfully"

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Tax compliance migration failed for {company_id}: {e}")
        return False, str(e)
    finally:
        db.close()


def run_for_all_companies():
    """Run migration for all active companies."""
    from sqlalchemy import create_engine
    from config import settings

    sys_engine = create_engine(settings.DATABASE_URL)
    with sys_engine.connect() as conn:
        companies = conn.execute(text(
            "SELECT id FROM system_companies WHERE status = 'active'"
        )).fetchall()
    sys_engine.dispose()

    results = []
    for company in companies:
        success, msg = run_migration(company.id)
        results.append({"company_id": company.id, "success": success, "message": msg})
        print(f"{'✅' if success else '❌'} {company.id}: {msg}")

    return results


if __name__ == "__main__":
    results = run_for_all_companies()
    total = len(results)
    ok = sum(1 for r in results if r["success"])
    print(f"\n{'═' * 50}")
    print(f"Migration complete: {ok}/{total} companies migrated successfully")
