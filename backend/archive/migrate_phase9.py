"""
Migration: Add ZATCA columns to invoices + API keys + Webhooks + WHT + CRM tables
Phase 9 database expansion
"""

from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def run_migration(db):
    """Run all Phase 9 migrations."""
    
    migrations = [
        # ===================== ZATCA Columns =====================
        ("zatca_hash on invoices", """
            ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_hash TEXT;
        """),
        ("zatca_signature on invoices", """
            ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_signature TEXT;
        """),
        ("zatca_qr on invoices", """
            ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_qr TEXT;
        """),
        ("zatca_status on invoices", """
            ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_status VARCHAR(20) DEFAULT 'pending';
        """),
        ("zatca_submission_id on invoices", """
            ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_submission_id TEXT;
        """),
        
        # ===================== API Keys =====================
        ("api_keys table", """
            CREATE TABLE IF NOT EXISTS api_keys (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                key_hash VARCHAR(255) NOT NULL UNIQUE,
                key_prefix VARCHAR(10) NOT NULL,
                permissions JSONB DEFAULT '[]',
                rate_limit_per_minute INT DEFAULT 60,
                is_active BOOLEAN DEFAULT TRUE,
                created_by INT,
                expires_at TIMESTAMP,
                last_used_at TIMESTAMP,
                usage_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                notes TEXT
            );
        """),
        
        # ===================== Webhooks =====================
        ("webhooks table", """
            CREATE TABLE IF NOT EXISTS webhooks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                url TEXT NOT NULL,
                secret VARCHAR(255),
                events JSONB NOT NULL DEFAULT '[]',
                is_active BOOLEAN DEFAULT TRUE,
                retry_count INT DEFAULT 3,
                timeout_seconds INT DEFAULT 10,
                created_by INT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """),
        ("webhook_logs table", """
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id SERIAL PRIMARY KEY,
                webhook_id INT REFERENCES webhooks(id) ON DELETE CASCADE,
                event VARCHAR(100) NOT NULL,
                payload JSONB,
                response_status INT,
                response_body TEXT,
                success BOOLEAN DEFAULT FALSE,
                attempt INT DEFAULT 1,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """),
        
        # ===================== Withholding Tax (WHT) =====================
        ("wht_rates table", """
            CREATE TABLE IF NOT EXISTS wht_rates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                name_ar VARCHAR(100),
                rate DECIMAL(5,2) NOT NULL,
                category VARCHAR(50) DEFAULT 'general',
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """),
        ("wht_transactions table", """
            CREATE TABLE IF NOT EXISTS wht_transactions (
                id SERIAL PRIMARY KEY,
                invoice_id INT,
                payment_id INT,
                supplier_id INT NOT NULL,
                wht_rate_id INT REFERENCES wht_rates(id),
                gross_amount DECIMAL(15,2) NOT NULL,
                wht_rate DECIMAL(5,2) NOT NULL,
                wht_amount DECIMAL(15,2) NOT NULL,
                net_amount DECIMAL(15,2) NOT NULL,
                journal_entry_id INT,
                certificate_number VARCHAR(50),
                period_date DATE,
                created_by INT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """),
        ("wht default rates", """
            INSERT INTO wht_rates (name, name_ar, rate, category) VALUES 
                ('Management Fees', 'رسوم إدارية', 20.00, 'services'),
                ('Royalties', 'إتاوات', 15.00, 'royalties'),
                ('Rent - Real Estate', 'إيجار عقار', 5.00, 'rent'),
                ('Technical Services', 'خدمات فنية', 5.00, 'services'),
                ('Dividends', 'أرباح أسهم', 5.00, 'dividends'),
                ('Interest', 'فوائد', 5.00, 'interest'),
                ('Insurance', 'تأمين', 5.00, 'insurance'),
                ('International Transport', 'نقل دولي', 5.00, 'transport')
            ON CONFLICT DO NOTHING;
        """),
        
        # ===================== CRM: Sales Opportunities =====================
        ("sales_opportunities table", """
            CREATE TABLE IF NOT EXISTS sales_opportunities (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                customer_id INT REFERENCES parties(id),
                contact_name VARCHAR(100),
                contact_email VARCHAR(150),
                contact_phone VARCHAR(50),
                stage VARCHAR(30) DEFAULT 'lead',
                probability INT DEFAULT 10,
                expected_value DECIMAL(15,2) DEFAULT 0,
                expected_close_date DATE,
                currency VARCHAR(5) DEFAULT 'SAR',
                source VARCHAR(50),
                assigned_to INT,
                branch_id INT,
                notes TEXT,
                lost_reason TEXT,
                won_quotation_id INT,
                created_by INT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """),
        ("opportunity_activities table", """
            CREATE TABLE IF NOT EXISTS opportunity_activities (
                id SERIAL PRIMARY KEY,
                opportunity_id INT REFERENCES sales_opportunities(id) ON DELETE CASCADE,
                activity_type VARCHAR(30) NOT NULL,
                title VARCHAR(200),
                description TEXT,
                due_date TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_by INT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """),
        
        # ===================== CRM: Support Tickets =====================
        ("support_tickets table", """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(30) NOT NULL UNIQUE,
                subject VARCHAR(200) NOT NULL,
                description TEXT,
                customer_id INT REFERENCES parties(id),
                contact_name VARCHAR(100),
                contact_email VARCHAR(150),
                contact_phone VARCHAR(50),
                status VARCHAR(30) DEFAULT 'open',
                priority VARCHAR(20) DEFAULT 'medium',
                category VARCHAR(50),
                assigned_to INT,
                branch_id INT,
                sla_hours INT DEFAULT 24,
                resolution TEXT,
                resolved_at TIMESTAMP,
                closed_at TIMESTAMP,
                created_by INT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """),
        ("ticket_comments table", """
            CREATE TABLE IF NOT EXISTS ticket_comments (
                id SERIAL PRIMARY KEY,
                ticket_id INT REFERENCES support_tickets(id) ON DELETE CASCADE,
                comment TEXT NOT NULL,
                is_internal BOOLEAN DEFAULT FALSE,
                attachment_url TEXT,
                created_by INT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """),
        
        # ===================== Tax Calendar =====================
        ("tax_calendar table", """
            CREATE TABLE IF NOT EXISTS tax_calendar (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                tax_type VARCHAR(50) NOT NULL,
                due_date DATE NOT NULL,
                reminder_days JSONB DEFAULT '[7, 3, 1]',
                status VARCHAR(20) DEFAULT 'upcoming',
                notes TEXT,
                is_recurring BOOLEAN DEFAULT FALSE,
                recurrence_pattern VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """),
    ]
    
    success_count = 0
    for name, sql in migrations:
        try:
            db.execute(text(sql))
            db.commit()
            success_count += 1
            logger.info(f"✅ Migration: {name}")
        except Exception as e:
            db.rollback()
            err_str = str(e)
            if "already exists" in err_str or "duplicate" in err_str.lower():
                logger.info(f"⏭️ Migration (already exists): {name}")
                success_count += 1
            else:
                logger.warning(f"⚠️ Migration failed: {name} — {err_str[:120]}")
    
    logger.info(f"✅ Phase 9 migration complete: {success_count}/{len(migrations)} applied")
    return success_count
