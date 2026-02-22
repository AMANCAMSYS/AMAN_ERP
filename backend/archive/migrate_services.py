"""
Migration: Service Management & Document Management tables
SVC-001: service_requests + service_request_costs
SVC-002: documents + document_versions
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import get_db_connection, get_system_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIGRATION_SQL = """
-- =============================================
-- SVC-001: Service / Maintenance Requests
-- =============================================
CREATE TABLE IF NOT EXISTS service_requests (
    id SERIAL PRIMARY KEY,
    request_number VARCHAR(30) UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'maintenance',     -- maintenance, repair, installation, inspection, other
    priority VARCHAR(20) DEFAULT 'medium',           -- critical, high, medium, low
    status VARCHAR(30) DEFAULT 'pending',            -- pending, assigned, in_progress, on_hold, completed, cancelled
    customer_id INTEGER REFERENCES parties(id),
    asset_id INTEGER,                                 -- optional: related fixed asset
    assigned_to INTEGER REFERENCES company_users(id),  -- technician
    assigned_at TIMESTAMP,
    estimated_hours NUMERIC(8,2),
    actual_hours NUMERIC(8,2),
    estimated_cost NUMERIC(14,2) DEFAULT 0,
    actual_cost NUMERIC(14,2) DEFAULT 0,
    scheduled_date DATE,
    completion_date DATE,
    location VARCHAR(255),
    notes TEXT,
    created_by INTEGER REFERENCES company_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS service_request_costs (
    id SERIAL PRIMARY KEY,
    service_request_id INTEGER NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
    cost_type VARCHAR(50) NOT NULL,                   -- labor, parts, travel, other
    description VARCHAR(255),
    quantity NUMERIC(10,2) DEFAULT 1,
    unit_cost NUMERIC(14,2) DEFAULT 0,
    total_cost NUMERIC(14,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auto-generate request number
CREATE OR REPLACE FUNCTION generate_service_request_number()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
    year_str VARCHAR(4);
BEGIN
    year_str := TO_CHAR(CURRENT_DATE, 'YYYY');
    SELECT COALESCE(MAX(
        CAST(SUBSTRING(request_number FROM 'SRQ-' || year_str || '-([0-9]+)') AS INTEGER)
    ), 0) + 1 INTO next_num
    FROM service_requests
    WHERE request_number LIKE 'SRQ-' || year_str || '-%';
    NEW.request_number := 'SRQ-' || year_str || '-' || LPAD(next_num::TEXT, 4, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_service_request_number ON service_requests;
CREATE TRIGGER trg_service_request_number
    BEFORE INSERT ON service_requests
    FOR EACH ROW
    WHEN (NEW.request_number IS NULL)
    EXECUTE FUNCTION generate_service_request_number();

-- =============================================
-- SVC-002: Document Management
-- =============================================
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    doc_number VARCHAR(30) UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',          -- contract, invoice, report, policy, manual, general
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER DEFAULT 0,
    mime_type VARCHAR(100),
    current_version INTEGER DEFAULT 1,
    tags TEXT,                                        -- comma-separated tags for search
    access_level VARCHAR(20) DEFAULT 'company',      -- public, company, department, private
    related_module VARCHAR(50),                       -- optional: sales, purchases, hr, etc.
    related_id INTEGER,                               -- optional: ID in related module
    created_by INTEGER REFERENCES company_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER DEFAULT 0,
    change_notes TEXT,
    uploaded_by INTEGER REFERENCES company_users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auto-generate document number
CREATE OR REPLACE FUNCTION generate_document_number()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
    year_str VARCHAR(4);
BEGIN
    year_str := TO_CHAR(CURRENT_DATE, 'YYYY');
    SELECT COALESCE(MAX(
        CAST(SUBSTRING(doc_number FROM 'DOC-' || year_str || '-([0-9]+)') AS INTEGER)
    ), 0) + 1 INTO next_num
    FROM documents
    WHERE doc_number LIKE 'DOC-' || year_str || '-%';
    NEW.doc_number := 'DOC-' || year_str || '-' || LPAD(next_num::TEXT, 4, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_document_number ON documents;
CREATE TRIGGER trg_document_number
    BEFORE INSERT ON documents
    FOR EACH ROW
    WHEN (NEW.doc_number IS NULL)
    EXECUTE FUNCTION generate_document_number();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_service_requests_customer ON service_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_assigned ON service_requests(assigned_to);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_created_by ON documents(created_by);
CREATE INDEX IF NOT EXISTS idx_document_versions_doc ON document_versions(document_id);
"""


def run_migration():
    """Run migration on all company databases."""
    sys_db = get_system_db()
    try:
        rows = sys_db.execute(text("SELECT database_name FROM system_companies WHERE database_name IS NOT NULL")).fetchall()
        # database_name is like "aman_80b0ada0"; get_db_connection expects "80b0ada0"
        databases = [r[0].replace("aman_", "", 1) if r[0].startswith("aman_") else r[0] for r in rows]
    finally:
        sys_db.close()

    if not databases:
        logger.warning("No company databases found")
        return

    for db_name in databases:
        logger.info(f"Migrating aman_{db_name}...")
        try:
            conn = get_db_connection(db_name)
            conn.execute(text(MIGRATION_SQL))
            conn.commit()
            logger.info(f"  ✅ aman_{db_name} migrated successfully")
        except Exception as e:
            logger.error(f"  ❌ aman_{db_name} failed: {e}")
            try:
                conn.rollback()
            except:
                pass
        finally:
            try:
                conn.close()
            except:
                pass


if __name__ == "__main__":
    run_migration()
