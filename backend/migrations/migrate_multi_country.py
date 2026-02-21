"""
Migration: Multi-Country Support
=================================
Adds country_code, default_currency to branches table.
Adds country_code to tax_rates table.
Adds company_country setting to company_settings.
Sets existing branches to use company's base currency.

Usage:
    python -c "
    from database import get_db_connection
    from migrations.migrate_multi_country import run_migration
    db = get_db_connection('COMPANY_ID')
    run_migration(db)
    db.close()
    "
"""

from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def run_migration(db):
    """Run multi-country migration on a company database."""
    
    migrations = [
        # 1. Add country_code column to branches
        ("ALTER TABLE branches ADD COLUMN IF NOT EXISTS country_code VARCHAR(5) DEFAULT NULL",
         "branches.country_code"),
        
        # 2. Add default_currency column to branches
        ("ALTER TABLE branches ADD COLUMN IF NOT EXISTS default_currency VARCHAR(3) DEFAULT NULL",
         "branches.default_currency"),
        
        # 3. Add country_code column to tax_rates
        ("ALTER TABLE tax_rates ADD COLUMN IF NOT EXISTS country_code VARCHAR(5) DEFAULT NULL",
         "tax_rates.country_code"),
    ]
    
    applied = 0
    for sql, desc in migrations:
        try:
            db.execute(text(sql))
            db.commit()
            logger.info(f"✅ Applied: {desc}")
            applied += 1
        except Exception as e:
            db.rollback()
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                logger.info(f"⏭️ Skipped (exists): {desc}")
                applied += 1
            else:
                logger.error(f"❌ Failed: {desc} - {e}")
    
    # 4. Detect company currency from system or settings
    try:
        currency_res = db.execute(
            text("SELECT setting_value FROM company_settings WHERE setting_key = 'default_currency'")
        ).scalar()
        company_currency = currency_res or "SAR"
        
        # Infer country from currency
        currency_to_country = {
            "SAR": "SA", "SYP": "SY", "AED": "AE", "EGP": "EG",
            "KWD": "KW", "TRY": "TR", "USD": "US", "EUR": "EU", "GBP": "GB"
        }
        company_country = currency_to_country.get(company_currency, "SA")
        
        # 5. Add company_country setting if missing
        existing = db.execute(
            text("SELECT 1 FROM company_settings WHERE setting_key = 'company_country'")
        ).scalar()
        if not existing:
            db.execute(text("""
                INSERT INTO company_settings (setting_key, setting_value) VALUES ('company_country', :country)
            """), {"country": company_country})
            db.commit()
            logger.info(f"✅ Added company_country = {company_country}")
            applied += 1
        else:
            logger.info("⏭️ company_country setting already exists")
            applied += 1
        
        # 6. Update existing branches that have NULL country_code or default_currency
        db.execute(text("""
            UPDATE branches 
            SET country_code = COALESCE(country_code, :country),
                default_currency = COALESCE(default_currency, :currency)
            WHERE country_code IS NULL OR default_currency IS NULL
        """), {"country": company_country, "currency": company_currency})
        db.commit()
        logger.info(f"✅ Updated branches with country_code={company_country}, default_currency={company_currency}")
        applied += 1
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed setting defaults: {e}")
    
    logger.info(f"🏁 Multi-country migration complete: {applied} operations applied")
    return applied
