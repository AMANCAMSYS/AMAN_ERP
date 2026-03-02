#!/usr/bin/env python3
"""
Re-initialize company b08f3451 with exact same company_id.
This script directly uses the database functions to recreate the company.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import create_company_database, create_company_tables, initialize_company_default_data, get_system_db
from sqlalchemy import text
from datetime import datetime, timezone

COMPANY_ID = "b08f3451"
ADMIN_USERNAME = "omar"
ADMIN_EMAIL = "omar@aman-erp.com"
ADMIN_PASSWORD = "As123321"
ADMIN_FULL_NAME = "عمر المدير"
CURRENCY = "SAR"
COUNTRY = "SA"
TIMEZONE = "Asia/Riyadh"

def main():
    print(f"🚀 Re-initializing company {COMPANY_ID}...")
    
    # 1. Create database
    print("📦 Creating database...")
    success, message, db_name, db_user = create_company_database(COMPANY_ID, ADMIN_PASSWORD)
    if not success:
        print(f"❌ Failed to create database: {message}")
        sys.exit(1)
    print(f"✅ Database created: {db_name}")
    
    # 2. Create tables
    print("📋 Creating tables...")
    success, message = create_company_tables(COMPANY_ID, CURRENCY)
    if not success:
        print(f"❌ Failed to create tables: {message}")
        sys.exit(1)
    print(f"✅ Tables created")
    
    # 3. Initialize default data
    print("🔧 Initializing default data...")
    success, message = initialize_company_default_data(
        COMPANY_ID, ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD,
        ADMIN_FULL_NAME, TIMEZONE, CURRENCY, COUNTRY
    )
    if not success:
        print(f"⚠️ Warning: {message}")
    else:
        print(f"✅ Default data initialized")
    
    # 4. Register in system database
    print("📝 Registering in system database...")
    db = get_system_db()
    try:
        # Get general template modules
        tpl = db.execute(text("SELECT id, enabled_modules FROM industry_templates WHERE key = 'general'")).fetchone()
        tpl_id = tpl[0] if tpl else None
        import json
        enabled_modules = json.dumps(tpl[1]) if tpl and tpl[1] else None
        
        db.execute(text("""
            INSERT INTO system_companies 
            (id, company_name, company_name_en, commercial_registry, tax_number, 
             phone, email, address, database_name, database_user, currency, 
             status, plan_type, template_id, enabled_modules, created_at, activated_at)
            VALUES 
            (:id, :name, :name_en, :registry, :tax, :phone, :email, :address, 
             :db_name, :db_user, :currency, 'active', 'enterprise', :tpl_id, :modules, :now, :now)
        """), {
            "id": COMPANY_ID,
            "name": "شركة أمان للتجارة",
            "name_en": "Aman Trading Company",
            "registry": "1010999888",
            "tax": "300999888800003",
            "phone": "+966501234567",
            "email": ADMIN_EMAIL,
            "address": "الرياض، المملكة العربية السعودية",
            "db_name": db_name,
            "db_user": db_user,
            "currency": CURRENCY,
            "tpl_id": tpl_id,
            "modules": enabled_modules,
            "now": datetime.now(timezone.utc)
        })
        db.commit()
        print(f"✅ Company registered in system database")
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to register: {e}")
        sys.exit(1)
    finally:
        db.close()
    
    print(f"\n✅ Company {COMPANY_ID} re-initialized successfully!")
    print(f"   Login: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"   Database: {db_name}")

if __name__ == "__main__":
    main()
