
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator, Tuple
from contextlib import contextmanager
from passlib.context import CryptContext
import uuid

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    isolation_level="AUTOCOMMIT",
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_engines = {}

def _get_engine(company_id: str):
    """Internal helper to get or create a cached engine"""
    if not company_id:
        raise ValueError("company_id is required")
    if company_id not in _engines:
        db_url = settings.get_company_database_url(company_id)
        _engines[company_id] = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20
        )
    return _engines[company_id]

def get_db_connection(company_id: str):
    """Returns a connection to the company specific database with engine caching
    
    Note: Caller is responsible for closing the connection with db.close()
    For safer usage, use db_connection() context manager instead.
    """
    return _get_engine(company_id).connect()

@contextmanager
def db_connection(company_id: str):
    """Context manager for safe database connection handling
    
    Usage:
        with db_connection(company_id) as db:
            result = db.execute(...)
            # connection automatically closed
    """
    conn = _get_engine(company_id).connect()
    try:
        yield conn
    finally:
        if not conn.closed:
            conn.close()

def get_company_db(company_id: str) -> Generator[Session, None, None]:
    """Returns a session to the company specific database using cached engine"""
    engine = _get_engine(company_id)
    CompanySession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = CompanySession()
    try:
        yield db
    finally:
        db.close()


def get_system_db() -> Session:
    return SessionLocal()


def generate_company_id() -> str:
    length = settings.COMPANY_ID_LENGTH
    return str(uuid.uuid4()).replace('-', '')[:length]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_company_database(company_id: str, admin_password: str) -> Tuple[bool, str, str, str]:
    db_name = f"aman_{company_id}"
    db_user = f"company_{company_id}"
    
    try:
        db = get_system_db()
        
        result = db.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": db_name}
        ).fetchone()
        
        if result:
            return False, "قاعدة البيانات موجودة", "", ""
        
        db.execute(text(f'CREATE DATABASE "{db_name}"'))
        db.execute(text(f"CREATE USER {db_user} WITH PASSWORD :password"), {"password": admin_password})
        db.execute(text(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO {db_user}'))
        db.execute(text(f'ALTER DATABASE "{db_name}" OWNER TO {db_user}'))
        
        db.commit()
        logger.info(f"✅ Created database: {db_name}")
        return True, "تم إنشاء قاعدة البيانات", db_name, db_user
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        db.rollback()
        return False, str(e), "", ""
    finally:
        db.close()


def get_all_table_sql() -> str:
    """Returns SQL for all 91 tables"""
    return """
    -- ===== CORE TABLES (7) =====
    CREATE TABLE IF NOT EXISTS company_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE,
        full_name VARCHAR(255),
        role VARCHAR(50) DEFAULT 'user',
        permissions JSONB DEFAULT '{}',
        is_active BOOLEAN DEFAULT TRUE,
        last_login TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS branches (
        id SERIAL PRIMARY KEY,
        branch_code VARCHAR(50) UNIQUE,
        branch_name VARCHAR(255) NOT NULL,
        branch_name_en VARCHAR(255),
        branch_type VARCHAR(50) DEFAULT 'branch',
        address TEXT,
        city VARCHAR(100),
        country VARCHAR(100),
        country_code VARCHAR(5) DEFAULT NULL,
        default_currency VARCHAR(3) DEFAULT NULL,
        phone VARCHAR(50),
        email VARCHAR(255),
        manager_id INTEGER,
        is_default BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS user_branches (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES company_users(id) ON DELETE CASCADE,
        branch_id INTEGER REFERENCES branches(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, branch_id)
    );

    -- ===== PARTIES (Consolidated) =====
    CREATE TABLE IF NOT EXISTS party_groups (
        id SERIAL PRIMARY KEY,
        group_code VARCHAR(50) UNIQUE,
        group_name VARCHAR(255) NOT NULL,
        group_name_en VARCHAR(255),
        branch_id INTEGER REFERENCES branches(id),
        discount_percentage DECIMAL(5, 2) DEFAULT 0,
        payment_days INTEGER DEFAULT 30,
        description TEXT,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS parties (
        id SERIAL PRIMARY KEY,
        party_type VARCHAR(20) DEFAULT 'individual', -- individual/company
        party_code VARCHAR(50) UNIQUE,
        name VARCHAR(255) NOT NULL,
        name_en VARCHAR(255),
        
        -- Contact Info
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        fax VARCHAR(50),
        website VARCHAR(255),
        
        -- Address
        address TEXT,
        city VARCHAR(100),
        country VARCHAR(100),
        postal_code VARCHAR(20),
        
        -- Financial & Legal
        tax_number VARCHAR(50),
        commercial_register VARCHAR(50),
        tax_exempt BOOLEAN DEFAULT FALSE,
        currency VARCHAR(3),
        
        -- Classification
        is_customer BOOLEAN DEFAULT FALSE,
        is_supplier BOOLEAN DEFAULT FALSE,
        party_group_id INTEGER REFERENCES party_groups(id),
        branch_id INTEGER REFERENCES branches(id),
        
        -- Commercial Terms
        price_list_id INTEGER, 
        payment_terms VARCHAR(100),
        credit_limit DECIMAL(18, 4) DEFAULT 0,
        
        -- Balances (Denormalized)
        current_balance DECIMAL(18, 4) DEFAULT 0,
        
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS party_transactions (
        id SERIAL PRIMARY KEY,
        party_id INTEGER REFERENCES parties(id),
        transaction_type VARCHAR(50) NOT NULL,
        reference_number VARCHAR(100),
        transaction_date DATE NOT NULL,
        description TEXT,
        debit DECIMAL(18, 4) DEFAULT 0,
        credit DECIMAL(18, 4) DEFAULT 0,
        balance DECIMAL(18, 4) DEFAULT 0,
        payment_id INTEGER, -- Link to payment_vouchers if needed
        invoice_id INTEGER, -- Link to invoices if needed
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    
    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        account_number VARCHAR(50) UNIQUE NOT NULL,
        account_code VARCHAR(20),
        name VARCHAR(255) NOT NULL,
        name_en VARCHAR(255),
        account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
        parent_id INTEGER REFERENCES accounts(id),
        balance DECIMAL(18, 4) DEFAULT 0,
        balance_currency DECIMAL(18, 4) DEFAULT 0,
        currency VARCHAR(3) DEFAULT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS treasury_accounts (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        name_en VARCHAR(255),
        account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('cash', 'bank')),
        currency VARCHAR(3) DEFAULT NULL,
        current_balance DECIMAL(18, 4) DEFAULT 0,
        gl_account_id INTEGER REFERENCES accounts(id),
        branch_id INTEGER REFERENCES branches(id),
        bank_name VARCHAR(255),
        account_number VARCHAR(100),
        iban VARCHAR(100),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- bank_accounts table removed (ARCH-006): merged into treasury_accounts
    
    CREATE TABLE IF NOT EXISTS journal_entries (
        id SERIAL PRIMARY KEY,
        entry_number VARCHAR(50) UNIQUE NOT NULL,
        entry_date DATE NOT NULL,
        reference VARCHAR(100),
        description TEXT,
        status VARCHAR(20) DEFAULT 'draft',
        currency VARCHAR(10) DEFAULT 'SAR',
        exchange_rate DECIMAL(18, 6) DEFAULT 1.0,
        branch_id INTEGER REFERENCES branches(id),
        source VARCHAR(100),
        source_id INTEGER,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        posted_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS journal_lines (
        id SERIAL PRIMARY KEY,
        journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
        account_id INTEGER NOT NULL REFERENCES accounts(id),
        debit DECIMAL(18, 4) DEFAULT 0,
        credit DECIMAL(18, 4) DEFAULT 0,
        cost_center_id INTEGER,
        amount_currency DECIMAL(18, 4) DEFAULT 0,
        currency VARCHAR(3) DEFAULT NULL,
        description TEXT,
        is_reconciled BOOLEAN DEFAULT FALSE,
        reconciliation_id INTEGER,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS invoices (
        id SERIAL PRIMARY KEY,
        invoice_number VARCHAR(50) UNIQUE NOT NULL,
        invoice_type VARCHAR(20) NOT NULL,
        party_id INTEGER REFERENCES parties(id),
        customer_id INTEGER, -- Deprecated
        supplier_id INTEGER, -- Deprecated
        invoice_date DATE NOT NULL,
        due_date DATE,
        subtotal DECIMAL(18, 4) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) DEFAULT 0,
        paid_amount DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        notes TEXT,
        down_payment_method VARCHAR(20),
        branch_id INTEGER REFERENCES branches(id),
        warehouse_id INTEGER,
        related_invoice_id INTEGER,
        currency VARCHAR(3) DEFAULT 'SAR',
        exchange_rate DECIMAL(18, 6) DEFAULT 1.0,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS invoice_lines (
        id SERIAL PRIMARY KEY,
        invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
        product_id INTEGER,
        description VARCHAR(500),
        quantity DECIMAL(18, 4) DEFAULT 1,
        unit_price DECIMAL(18, 4) DEFAULT 0,
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS company_settings (
        id SERIAL PRIMARY KEY,
        setting_key VARCHAR(100) UNIQUE NOT NULL,
        setting_value TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
-- ===== SUPPLIERS TABLES (Legacy/Deprecated) =====
    CREATE TABLE IF NOT EXISTS supplier_groups (
        id SERIAL PRIMARY KEY,
        group_code VARCHAR(50) UNIQUE,
        group_name VARCHAR(255) NOT NULL,
        group_name_en VARCHAR(255),
        description TEXT,
        parent_id INTEGER REFERENCES supplier_groups(id),
        branch_id INTEGER REFERENCES branches(id),
        discount_percentage DECIMAL(5, 2) DEFAULT 0,
        payment_days INTEGER DEFAULT 30,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS suppliers (
        id SERIAL PRIMARY KEY,
        supplier_code VARCHAR(50) UNIQUE,
        supplier_name VARCHAR(255) NOT NULL,
        supplier_name_en VARCHAR(255),
        tax_number VARCHAR(50),
        commercial_register VARCHAR(50),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        fax VARCHAR(50),
        website VARCHAR(255),
        address TEXT,
        city VARCHAR(100),
        country VARCHAR(100),
        postal_code VARCHAR(20),
        supplier_group_id INTEGER REFERENCES supplier_groups(id),
        branch_id INTEGER REFERENCES branches(id),
        payment_terms VARCHAR(100),
        credit_limit DECIMAL(18, 4) DEFAULT 0,
        current_balance DECIMAL(18, 4) DEFAULT 0,
        currency VARCHAR(3) DEFAULT NULL,
        tax_exempt BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS supplier_contacts (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
        contact_name VARCHAR(255) NOT NULL,
        contact_name_en VARCHAR(255),
        position VARCHAR(100),
        department VARCHAR(100),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        is_primary BOOLEAN DEFAULT FALSE,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS supplier_bank_accounts (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
        bank_name VARCHAR(255) NOT NULL,
        bank_name_en VARCHAR(255),
        account_number VARCHAR(50),
        iban VARCHAR(50),
        swift_code VARCHAR(20),
        branch_name VARCHAR(255),
        branch_code VARCHAR(50),
        account_holder VARCHAR(255),
        is_default BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS supplier_transactions (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER REFERENCES suppliers(id),
        transaction_type VARCHAR(50) NOT NULL,
        reference_number VARCHAR(100),
        transaction_date DATE NOT NULL,
        description TEXT,
        debit DECIMAL(18, 4) DEFAULT 0,
        credit DECIMAL(18, 4) DEFAULT 0,
        balance DECIMAL(18, 4) DEFAULT 0,
        payment_id INTEGER,
        invoice_id INTEGER,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS supplier_payments (
        id SERIAL PRIMARY KEY,
        payment_number VARCHAR(50) UNIQUE,
        supplier_id INTEGER REFERENCES suppliers(id),
        payment_date DATE NOT NULL,
        payment_method VARCHAR(50),
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(3) DEFAULT NULL,
        exchange_rate DECIMAL(10, 6) DEFAULT 1,
        bank_account_id INTEGER,
        reference VARCHAR(100),
        notes TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """


def get_additional_tables_sql() -> str:
    """Returns SQL for remaining tables"""
    return """
    -- ===== CUSTOMERS TABLES (7) =====
    CREATE TABLE IF NOT EXISTS customer_groups (
        id SERIAL PRIMARY KEY,
        group_code VARCHAR(50) UNIQUE,
        group_name VARCHAR(255) NOT NULL,
        group_name_en VARCHAR(255),
        description TEXT,
        parent_id INTEGER REFERENCES customer_groups(id),
        branch_id INTEGER REFERENCES branches(id),
        discount_percentage DECIMAL(5, 2) DEFAULT 0,
        price_list_id INTEGER,
        payment_days INTEGER DEFAULT 30,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        customer_code VARCHAR(50) UNIQUE,
        customer_name VARCHAR(255) NOT NULL,
        customer_name_en VARCHAR(255),
        customer_type VARCHAR(50) DEFAULT 'individual',
        tax_number VARCHAR(50),
        commercial_register VARCHAR(50),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        fax VARCHAR(50),
        website VARCHAR(255),
        address TEXT,
        city VARCHAR(100),
        country VARCHAR(100),
        postal_code VARCHAR(20),
        customer_group_id INTEGER REFERENCES customer_groups(id),
        branch_id INTEGER REFERENCES branches(id),
        payment_terms VARCHAR(100),
        credit_limit DECIMAL(18, 4) DEFAULT 0,
        current_balance DECIMAL(18, 4) DEFAULT 0,
        currency VARCHAR(3) DEFAULT NULL,
        price_list_id INTEGER,
        tax_exempt BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS customer_contacts (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
        contact_name VARCHAR(255) NOT NULL,
        contact_name_en VARCHAR(255),
        position VARCHAR(100),
        department VARCHAR(100),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        is_primary BOOLEAN DEFAULT FALSE,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS customer_bank_accounts (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
        bank_name VARCHAR(255) NOT NULL,
        bank_name_en VARCHAR(255),
        account_number VARCHAR(50),
        iban VARCHAR(50),
        swift_code VARCHAR(20),
        branch_name VARCHAR(255),
        account_holder VARCHAR(255),
        is_default BOOLEAN DEFAULT FALSE,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS customer_transactions (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id),
        transaction_type VARCHAR(50) NOT NULL,
        reference_number VARCHAR(100),
        transaction_date DATE NOT NULL,
        description TEXT,
        debit DECIMAL(18, 4) DEFAULT 0,
        credit DECIMAL(18, 4) DEFAULT 0,
        balance DECIMAL(18, 4) DEFAULT 0,
        receipt_id INTEGER,
        invoice_id INTEGER,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS customer_receipts (
        id SERIAL PRIMARY KEY,
        receipt_number VARCHAR(50) UNIQUE,
        customer_id INTEGER REFERENCES customers(id),
        receipt_date DATE NOT NULL,
        receipt_method VARCHAR(50),
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(3) DEFAULT NULL,
        exchange_rate DECIMAL(10, 6) DEFAULT 1,
        bank_account_id INTEGER,
        reference VARCHAR(100),
        notes TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS customer_price_lists (
        id SERIAL PRIMARY KEY,
        price_list_code VARCHAR(50) UNIQUE,
        price_list_name VARCHAR(255) NOT NULL,
        price_list_name_en VARCHAR(255),
        customer_group_id INTEGER REFERENCES customer_groups(id),
        currency VARCHAR(3) DEFAULT NULL,
        discount_type VARCHAR(20) DEFAULT 'percentage',
        discount_value DECIMAL(10, 4) DEFAULT 0,
        valid_from DATE,
        valid_to DATE,
        status VARCHAR(20) DEFAULT 'active',
        is_default BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    -- ===== PRODUCTS & INVENTORY TABLES (7) =====
    CREATE TABLE IF NOT EXISTS product_categories (
        id SERIAL PRIMARY KEY,
        category_code VARCHAR(50) UNIQUE,
        category_name VARCHAR(255) NOT NULL,
        category_name_en VARCHAR(255),
        description TEXT,
        parent_id INTEGER REFERENCES product_categories(id),
        branch_id INTEGER REFERENCES branches(id),
        image_url TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS product_units (
        id SERIAL PRIMARY KEY,
        unit_code VARCHAR(20) UNIQUE,
        unit_name VARCHAR(100) NOT NULL,
        unit_name_en VARCHAR(100),
        abbreviation VARCHAR(10),
        base_unit_id INTEGER REFERENCES product_units(id),
        conversion_factor DECIMAL(10, 6) DEFAULT 1,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        product_code VARCHAR(50) UNIQUE,
        product_name VARCHAR(255) NOT NULL,
        product_name_en VARCHAR(255),
        product_type VARCHAR(50) DEFAULT 'product',
        category_id INTEGER REFERENCES product_categories(id),
        unit_id INTEGER REFERENCES product_units(id),
        barcode VARCHAR(100),
        description TEXT,
        short_description VARCHAR(500),
        brand VARCHAR(100),
        manufacturer VARCHAR(100),
        origin_country VARCHAR(100),
        weight DECIMAL(10, 4),
        volume DECIMAL(10, 4),
        dimensions VARCHAR(100),
        cost_price DECIMAL(18, 4) DEFAULT 0,
        last_purchase_price DECIMAL(18, 4) DEFAULT 0,
        selling_price DECIMAL(18, 4) DEFAULT 0,
        wholesale_price DECIMAL(18, 4) DEFAULT 0,
        min_price DECIMAL(18, 4) DEFAULT 0,
        max_price DECIMAL(18, 4) DEFAULT 0,
        sku VARCHAR(100) UNIQUE,
        tax_rate DECIMAL(5, 2) DEFAULT 15,
        is_taxable BOOLEAN DEFAULT TRUE,
        is_active BOOLEAN DEFAULT TRUE,
        is_track_inventory BOOLEAN DEFAULT TRUE,
        reorder_level DECIMAL(18, 4) DEFAULT 0,
        reorder_quantity DECIMAL(18, 4) DEFAULT 0,
        image_url TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS customer_price_list_items (
        id SERIAL PRIMARY KEY,
        price_list_id INTEGER NOT NULL,
        product_id INTEGER REFERENCES products(id),
        price DECIMAL(18, 4) NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS warehouses (
        id SERIAL PRIMARY KEY,
        warehouse_code VARCHAR(50) UNIQUE,
        warehouse_name VARCHAR(255) NOT NULL,
        warehouse_name_en VARCHAR(255),
        location VARCHAR(255),
        address TEXT,
        city VARCHAR(100),
        country VARCHAR(100),
        branch_id INTEGER REFERENCES branches(id),
        manager_id INTEGER REFERENCES company_users(id),
        is_default BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS inventory (
        id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        quantity DECIMAL(18, 4) DEFAULT 0,
        reserved_quantity DECIMAL(18, 4) DEFAULT 0,
        available_quantity DECIMAL(18, 4) DEFAULT 0,
        average_cost DECIMAL(18, 4) DEFAULT 0, -- Total company-wide or per-wh cost
        policy_version INTEGER DEFAULT 1,
        last_costing_update TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        last_movement_date TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(product_id, warehouse_id)
    );
    
    CREATE TABLE IF NOT EXISTS inventory_transactions (
        id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        transaction_type VARCHAR(50) NOT NULL,
        reference_type VARCHAR(50),
        reference_id INTEGER,
        reference_document VARCHAR(100),
        quantity DECIMAL(18, 4) NOT NULL,
        balance_before DECIMAL(18, 4) DEFAULT 0,
        balance_after DECIMAL(18, 4) DEFAULT 0,
        unit_cost DECIMAL(18, 4) DEFAULT 0,
        total_cost DECIMAL(18, 4) DEFAULT 0,
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS stock_adjustments (
        id SERIAL PRIMARY KEY,
        adjustment_number VARCHAR(50) UNIQUE,
        warehouse_id INTEGER REFERENCES warehouses(id),
        adjustment_type VARCHAR(50) NOT NULL,
        reason VARCHAR(255),
        product_id INTEGER REFERENCES products(id),
        old_quantity DECIMAL(18, 4) DEFAULT 0,
        new_quantity DECIMAL(18, 4) DEFAULT 0,
        difference DECIMAL(18, 4) DEFAULT 0,
        notes TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== STOCK SHIPMENTS (2) =====
    CREATE TABLE IF NOT EXISTS stock_shipments (
        id SERIAL PRIMARY KEY,
        shipment_ref VARCHAR(50) UNIQUE,
        source_warehouse_id INTEGER REFERENCES warehouses(id),
        destination_warehouse_id INTEGER REFERENCES warehouses(id),
        status VARCHAR(20) DEFAULT 'pending', -- pending, shipped, received, cancelled
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        shipped_at TIMESTAMPTZ,
        received_at TIMESTAMPTZ,
        received_by INTEGER REFERENCES company_users(id)
    );

    CREATE TABLE IF NOT EXISTS stock_shipment_items (
        id SERIAL PRIMARY KEY,
        shipment_id INTEGER REFERENCES stock_shipments(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        quantity DECIMAL(18, 4) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS stock_transfer_log (
        id SERIAL PRIMARY KEY,
        shipment_id INTEGER,
        product_id INTEGER REFERENCES products(id),
        from_warehouse_id INTEGER REFERENCES warehouses(id),
        to_warehouse_id INTEGER REFERENCES warehouses(id),
        quantity DECIMAL(18, 4) DEFAULT 0,
        transfer_cost DECIMAL(18, 4) DEFAULT 0,
        from_avg_cost_before DECIMAL(18, 4) DEFAULT 0,
        to_avg_cost_before DECIMAL(18, 4) DEFAULT 0,
        to_avg_cost_after DECIMAL(18, 4) DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS purchase_orders (
        id SERIAL PRIMARY KEY,
        po_number VARCHAR(50) UNIQUE NOT NULL,
        party_id INTEGER REFERENCES parties(id),
        supplier_id INTEGER, -- Deprecated
        branch_id INTEGER REFERENCES branches(id),
        order_date DATE NOT NULL,
        expected_date DATE,
        subtotal DECIMAL(18, 4) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft', -- draft, confirmed, received, cancelled
        notes TEXT,
        currency VARCHAR(3) DEFAULT 'SAR',
        exchange_rate DECIMAL(18, 6) DEFAULT 1.0,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS purchase_order_lines (
        id SERIAL PRIMARY KEY,
        po_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        description VARCHAR(500),
        quantity DECIMAL(18, 4) DEFAULT 1,
        unit_price DECIMAL(18, 4) DEFAULT 0,
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) DEFAULT 0,
        received_quantity DECIMAL(18, 4) DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );


    CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES company_users(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        message TEXT,
        link VARCHAR(255),
        is_read BOOLEAN DEFAULT FALSE,
        type VARCHAR(20) DEFAULT 'info',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS custom_reports (
        id SERIAL PRIMARY KEY,
        report_name VARCHAR(255) NOT NULL,
        description TEXT,
        config JSONB DEFAULT '{}',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS scheduled_reports (
        id SERIAL PRIMARY KEY,
        report_type VARCHAR(50) NOT NULL,
        frequency VARCHAR(20) NOT NULL,
        recipients TEXT NOT NULL,
        format VARCHAR(10) DEFAULT 'pdf',
        branch_id INTEGER REFERENCES branches(id),
        next_run_at TIMESTAMPTZ,
        last_run_at TIMESTAMPTZ,
        is_active BOOLEAN DEFAULT TRUE,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sales_quotations (
        id SERIAL PRIMARY KEY,
        sq_number VARCHAR(50) UNIQUE NOT NULL,
        party_id INTEGER REFERENCES parties(id),
        customer_id INTEGER, -- Deprecated
        branch_id INTEGER REFERENCES branches(id),
        quotation_date DATE NOT NULL,
        expiry_date DATE,
        subtotal DECIMAL(18, 4) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        notes TEXT,
        terms_conditions TEXT,
        currency VARCHAR(3) DEFAULT 'SAR',
        exchange_rate DECIMAL(18, 6) DEFAULT 1.0,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sales_quotation_lines (
        id SERIAL PRIMARY KEY,
        sq_id INTEGER REFERENCES sales_quotations(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        description TEXT,
        quantity DECIMAL(18, 4) NOT NULL,
        unit_price DECIMAL(18, 4) NOT NULL,
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sales_orders (
        id SERIAL PRIMARY KEY,
        so_number VARCHAR(50) UNIQUE NOT NULL,
        party_id INTEGER REFERENCES parties(id),
        customer_id INTEGER, -- Deprecated
        branch_id INTEGER REFERENCES branches(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        quotation_id INTEGER REFERENCES sales_quotations(id),
        order_date DATE NOT NULL,
        expected_delivery_date DATE,
        subtotal DECIMAL(18, 4) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        notes TEXT,
        currency VARCHAR(3) DEFAULT 'SAR',
        exchange_rate DECIMAL(18, 6) DEFAULT 1.0,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sales_order_lines (
        id SERIAL PRIMARY KEY,
        so_id INTEGER REFERENCES sales_orders(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        description TEXT,
        quantity DECIMAL(18, 4) NOT NULL,
        unit_price DECIMAL(18, 4) NOT NULL,
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        discount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) NOT NULL
    );



    CREATE TABLE IF NOT EXISTS sales_returns (
        id SERIAL PRIMARY KEY,
        return_number VARCHAR(50) UNIQUE NOT NULL,
        party_id INTEGER REFERENCES parties(id),
        customer_id INTEGER, -- Deprecated
        branch_id INTEGER REFERENCES branches(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        invoice_id INTEGER REFERENCES invoices(id),
        return_date DATE NOT NULL,
        subtotal DECIMAL(18, 4) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        total DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        notes TEXT,
        refund_method VARCHAR(20),
        refund_amount DECIMAL(18, 4) DEFAULT 0,
        bank_account_id INTEGER, -- legacy, use treasury_account_id
        treasury_account_id INTEGER REFERENCES treasury_accounts(id),
        check_number VARCHAR(50),
        check_date DATE,
        exchange_rate DECIMAL(10, 6) DEFAULT 1.0,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sales_return_lines (
        id SERIAL PRIMARY KEY,
        return_id INTEGER REFERENCES sales_returns(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        description TEXT,
        quantity DECIMAL(18, 4) NOT NULL,
        unit_price DECIMAL(18, 4) NOT NULL,
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        total DECIMAL(18, 4) NOT NULL,
        reason TEXT
    );

    CREATE TABLE IF NOT EXISTS payment_vouchers (
        id SERIAL PRIMARY KEY,
        voucher_number VARCHAR(50) UNIQUE NOT NULL,
        branch_id INTEGER REFERENCES branches(id),
        voucher_type VARCHAR(20) NOT NULL, -- receipt, payment
        voucher_date DATE NOT NULL,
        party_type VARCHAR(20) NOT NULL, -- customer, supplier
        party_id INTEGER NOT NULL, -- References parties(id) now effectively
        amount DECIMAL(18, 4) NOT NULL,
        payment_method VARCHAR(20) NOT NULL, -- cash, bank, check
        bank_account_id INTEGER, -- legacy, use treasury_account_id
        treasury_account_id INTEGER REFERENCES treasury_accounts(id),
        check_number VARCHAR(50),
        check_date DATE,
        reference VARCHAR(100),
        notes TEXT,
        currency VARCHAR(3) DEFAULT 'SAR',
        exchange_rate DECIMAL(18, 6) DEFAULT 1.0,
        status VARCHAR(20) DEFAULT 'posted',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS payment_allocations (
        id SERIAL PRIMARY KEY,
        voucher_id INTEGER REFERENCES payment_vouchers(id) ON DELETE CASCADE,
        invoice_id INTEGER REFERENCES invoices(id),
        allocated_amount DECIMAL(18, 4) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== SALES COMMISSIONS =====
    CREATE TABLE IF NOT EXISTS commission_rules (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        salesperson_id INTEGER,
        product_id INTEGER,
        category_id INTEGER,
        rate_type VARCHAR(20) DEFAULT 'percentage',
        rate DECIMAL(10, 4) DEFAULT 0,
        min_amount DECIMAL(18, 4) DEFAULT 0,
        max_amount DECIMAL(18, 4),
        is_active BOOLEAN DEFAULT TRUE,
        branch_id INTEGER REFERENCES branches(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sales_commissions (
        id SERIAL PRIMARY KEY,
        salesperson_id INTEGER,
        salesperson_name VARCHAR(255),
        invoice_id INTEGER,
        invoice_number VARCHAR(50),
        invoice_date DATE,
        invoice_total DECIMAL(18, 4) DEFAULT 0,
        commission_rate DECIMAL(10, 4) DEFAULT 0,
        commission_amount DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        paid_date DATE,
        branch_id INTEGER REFERENCES branches(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(invoice_id, salesperson_id)
    );

    -- ===== REQUEST FOR QUOTATIONS =====
    CREATE TABLE IF NOT EXISTS request_for_quotations (
        id SERIAL PRIMARY KEY,
        rfq_number VARCHAR(50) UNIQUE,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        status VARCHAR(30) DEFAULT 'draft',
        deadline TIMESTAMPTZ,
        branch_id INTEGER REFERENCES branches(id),
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS rfq_lines (
        id SERIAL PRIMARY KEY,
        rfq_id INTEGER REFERENCES request_for_quotations(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        product_name VARCHAR(255),
        quantity NUMERIC(12, 3) NOT NULL,
        unit VARCHAR(50),
        specifications TEXT
    );

    CREATE TABLE IF NOT EXISTS rfq_responses (
        id SERIAL PRIMARY KEY,
        rfq_id INTEGER REFERENCES request_for_quotations(id) ON DELETE CASCADE,
        supplier_id INTEGER,
        supplier_name VARCHAR(255),
        unit_price NUMERIC(15, 2),
        total_price NUMERIC(15, 2),
        delivery_days INTEGER,
        notes TEXT,
        is_selected BOOLEAN DEFAULT FALSE,
        submitted_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- ===== SUPPLIER RATINGS =====
    CREATE TABLE IF NOT EXISTS supplier_ratings (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER NOT NULL,
        po_id INTEGER,
        quality_score NUMERIC(3, 1) DEFAULT 0,
        delivery_score NUMERIC(3, 1) DEFAULT 0,
        price_score NUMERIC(3, 1) DEFAULT 0,
        service_score NUMERIC(3, 1) DEFAULT 0,
        overall_score NUMERIC(3, 1) DEFAULT 0,
        comments TEXT,
        rated_by INTEGER REFERENCES company_users(id),
        rated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- ===== PURCHASE AGREEMENTS =====
    CREATE TABLE IF NOT EXISTS purchase_agreements (
        id SERIAL PRIMARY KEY,
        agreement_number VARCHAR(50) UNIQUE,
        supplier_id INTEGER NOT NULL,
        agreement_type VARCHAR(30) DEFAULT 'blanket',
        title VARCHAR(255),
        start_date DATE,
        end_date DATE,
        total_amount NUMERIC(15, 2) DEFAULT 0,
        consumed_amount NUMERIC(15, 2) DEFAULT 0,
        status VARCHAR(30) DEFAULT 'draft',
        branch_id INTEGER REFERENCES branches(id),
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS purchase_agreement_lines (
        id SERIAL PRIMARY KEY,
        agreement_id INTEGER REFERENCES purchase_agreements(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        product_name VARCHAR(255),
        quantity NUMERIC(12, 3),
        unit_price NUMERIC(15, 2),
        delivered_qty NUMERIC(12, 3) DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_rfq_status ON request_for_quotations(status);
    CREATE INDEX IF NOT EXISTS idx_supplier_ratings_supplier ON supplier_ratings(supplier_id);
    CREATE INDEX IF NOT EXISTS idx_purchase_agreements_status ON purchase_agreements(status);
    """


def get_organization_tables_sql() -> str:
    """Organization and HR tables"""
    return """
    -- ===== BRANCHES & EMPLOYEES (5) =====

    -- MOVED HERE TO FIX CIRCULAR DEPENDENCY
    CREATE TABLE IF NOT EXISTS payroll_periods (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        payment_date DATE,
        status VARCHAR(20) DEFAULT 'draft',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS departments (
        id SERIAL PRIMARY KEY,
        department_code VARCHAR(50) UNIQUE,
        department_name VARCHAR(255) NOT NULL,
        department_name_en VARCHAR(255),
        parent_id INTEGER REFERENCES departments(id),
        branch_id INTEGER REFERENCES branches(id),
        manager_id INTEGER,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS employee_positions (
        id SERIAL PRIMARY KEY,
        position_code VARCHAR(50) UNIQUE,
        position_name VARCHAR(255) NOT NULL,
        position_name_en VARCHAR(255),
        department_id INTEGER REFERENCES departments(id),
        description TEXT,
        level INTEGER DEFAULT 1,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        role_name VARCHAR(50) UNIQUE NOT NULL,
        role_name_ar VARCHAR(50),
        description TEXT,
        permissions JSONB DEFAULT '[]',
        is_system_role BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        username VARCHAR(100),
        action VARCHAR(100),
        resource_type VARCHAR(50),
        resource_id VARCHAR(50),
        details JSONB,
        ip_address VARCHAR(50),
        branch_id INTEGER REFERENCES branches(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
        
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        employee_code VARCHAR(50) UNIQUE,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        first_name_en VARCHAR(100),
        last_name_en VARCHAR(100),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        gender VARCHAR(10),
        birth_date DATE,
        hire_date DATE,
        termination_date DATE,
        department_id INTEGER REFERENCES departments(id),
        position_id INTEGER REFERENCES employee_positions(id),
        branch_id INTEGER REFERENCES branches(id),
        manager_id INTEGER REFERENCES employees(id),
        employment_type VARCHAR(50) DEFAULT 'full_time',
        status VARCHAR(20) DEFAULT 'active',
        salary DECIMAL(18, 4) DEFAULT 0,
        housing_allowance DECIMAL(18, 4) DEFAULT 0,
        transport_allowance DECIMAL(18, 4) DEFAULT 0,
        other_allowances DECIMAL(18, 4) DEFAULT 0,
        hourly_cost DECIMAL(18, 4) DEFAULT 0,
        currency VARCHAR(3) DEFAULT NULL,
        user_id INTEGER REFERENCES company_users(id),
        account_id INTEGER REFERENCES accounts(id),
        bank_account_id INTEGER,
        tax_id VARCHAR(50),
        social_security VARCHAR(50),
        address TEXT,
        emergency_contact TEXT,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS cost_centers (
        id SERIAL PRIMARY KEY,
        center_code VARCHAR(50) UNIQUE,
        center_name VARCHAR(255) NOT NULL,
        center_name_en VARCHAR(255),
        department_id INTEGER REFERENCES departments(id),
        manager_id INTEGER REFERENCES employees(id),
        budget DECIMAL(18, 4) DEFAULT 0,
        currency VARCHAR(3) DEFAULT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id),
        date DATE NOT NULL,
        check_in TIMESTAMPTZ,
        check_out TIMESTAMPTZ,
        status VARCHAR(20) DEFAULT 'present',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employee_loans (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id),
        amount DECIMAL(18, 4) NOT NULL,
        total_installments INTEGER DEFAULT 1,
        monthly_installment DECIMAL(18, 4) NOT NULL,
        paid_amount DECIMAL(18, 4) DEFAULT 0,
        start_date DATE,
        status VARCHAR(20) DEFAULT 'pending',
        reason TEXT,
        approved_by INTEGER REFERENCES company_users(id),
        branch_id INTEGER REFERENCES branches(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS leave_requests (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id),
        leave_type VARCHAR(50) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        reason TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        approved_by INTEGER REFERENCES company_users(id),
        attachment_url TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== ADVANCED HR TABLES (Phase 4) =====

    CREATE TABLE IF NOT EXISTS salary_structures (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        name_en VARCHAR(255),
        description TEXT,
        base_type VARCHAR(50) DEFAULT 'monthly',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS salary_components (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        name_en VARCHAR(255),
        component_type VARCHAR(20) NOT NULL CHECK (component_type IN ('earning', 'deduction')),
        calculation_type VARCHAR(20) NOT NULL DEFAULT 'fixed' CHECK (calculation_type IN ('fixed', 'percentage', 'formula')),
        percentage_of VARCHAR(50),
        percentage_value DECIMAL(8, 4) DEFAULT 0,
        formula TEXT,
        is_taxable BOOLEAN DEFAULT TRUE,
        is_gosi_applicable BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        sort_order INTEGER DEFAULT 0,
        structure_id INTEGER REFERENCES salary_structures(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employee_salary_components (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        component_id INTEGER REFERENCES salary_components(id) ON DELETE CASCADE,
        amount DECIMAL(18, 4) DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        effective_date DATE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(employee_id, component_id)
    );

    CREATE TABLE IF NOT EXISTS overtime_requests (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id),
        request_date DATE NOT NULL,
        overtime_date DATE NOT NULL,
        hours DECIMAL(5, 2) NOT NULL,
        overtime_type VARCHAR(20) DEFAULT 'normal' CHECK (overtime_type IN ('normal', 'holiday', 'weekend')),
        multiplier DECIMAL(4, 2) DEFAULT 1.5,
        calculated_amount DECIMAL(18, 4) DEFAULT 0,
        reason TEXT,
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'processed')),
        approved_by INTEGER REFERENCES company_users(id),
        approved_at TIMESTAMPTZ,
        branch_id INTEGER REFERENCES branches(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS gosi_settings (
        id SERIAL PRIMARY KEY,
        employee_share_percentage DECIMAL(5, 2) DEFAULT 9.75,
        employer_share_percentage DECIMAL(5, 2) DEFAULT 11.75,
        occupational_hazard_percentage DECIMAL(5, 2) DEFAULT 2.0,
        max_contributable_salary DECIMAL(18, 4) DEFAULT 45000,
        is_active BOOLEAN DEFAULT TRUE,
        effective_date DATE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employee_documents (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('passport', 'iqama', 'license', 'certificate', 'contract', 'other')),
        document_number VARCHAR(100),
        issue_date DATE,
        expiry_date DATE,
        issuing_authority VARCHAR(255),
        file_url TEXT,
        notes TEXT,
        alert_days INTEGER DEFAULT 30,
        status VARCHAR(20) DEFAULT 'valid' CHECK (status IN ('valid', 'expired', 'expiring_soon')),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS performance_reviews (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        reviewer_id INTEGER REFERENCES employees(id),
        review_period VARCHAR(50) NOT NULL,
        review_date DATE NOT NULL,
        review_type VARCHAR(30) DEFAULT 'annual' CHECK (review_type IN ('quarterly', 'semi_annual', 'annual', 'probation')),
        overall_rating DECIMAL(3, 1) DEFAULT 0,
        strengths TEXT,
        weaknesses TEXT,
        goals TEXT,
        self_rating DECIMAL(3, 1),
        self_comments TEXT,
        manager_comments TEXT,
        status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'self_review', 'manager_review', 'completed')),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS training_programs (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        name_en VARCHAR(255),
        description TEXT,
        trainer VARCHAR(255),
        location VARCHAR(255),
        start_date DATE,
        end_date DATE,
        max_participants INTEGER,
        cost DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'in_progress', 'completed', 'cancelled')),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS training_participants (
        id SERIAL PRIMARY KEY,
        training_id INTEGER REFERENCES training_programs(id) ON DELETE CASCADE,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        attendance_status VARCHAR(20) DEFAULT 'registered' CHECK (attendance_status IN ('registered', 'attended', 'absent', 'completed')),
        certificate_issued BOOLEAN DEFAULT FALSE,
        score DECIMAL(5, 2),
        feedback TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(training_id, employee_id)
    );

    CREATE TABLE IF NOT EXISTS employee_violations (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        violation_date DATE NOT NULL,
        violation_type VARCHAR(100) NOT NULL,
        severity VARCHAR(20) DEFAULT 'minor' CHECK (severity IN ('minor', 'major', 'critical')),
        description TEXT,
        action_taken VARCHAR(100),
        penalty_amount DECIMAL(18, 4) DEFAULT 0,
        deduct_from_salary BOOLEAN DEFAULT FALSE,
        payroll_period_id INTEGER REFERENCES payroll_periods(id),
        reported_by INTEGER REFERENCES company_users(id),
        status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'appealed', 'dismissed')),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employee_custody (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
        item_name VARCHAR(255) NOT NULL,
        item_type VARCHAR(50) CHECK (item_type IN ('mobile', 'laptop', 'vehicle', 'key', 'equipment', 'other')),
        serial_number VARCHAR(100),
        assigned_date DATE NOT NULL,
        return_date DATE,
        condition_on_assign VARCHAR(50) DEFAULT 'new',
        condition_on_return VARCHAR(50),
        value DECIMAL(18, 4) DEFAULT 0,
        notes TEXT,
        status VARCHAR(20) DEFAULT 'assigned' CHECK (status IN ('assigned', 'returned', 'lost', 'damaged')),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );


    CREATE TABLE IF NOT EXISTS payroll_entries (
        id SERIAL PRIMARY KEY,
        period_id INTEGER REFERENCES payroll_periods(id) ON DELETE CASCADE,
        employee_id INTEGER REFERENCES employees(id),
        basic_salary DECIMAL(18, 4) DEFAULT 0,
        housing_allowance DECIMAL(18, 4) DEFAULT 0,
        transport_allowance DECIMAL(18, 4) DEFAULT 0,
        other_allowances DECIMAL(18, 4) DEFAULT 0,
        salary_components_earning DECIMAL(18, 4) DEFAULT 0,
        salary_components_deduction DECIMAL(18, 4) DEFAULT 0,
        overtime_amount DECIMAL(18, 4) DEFAULT 0,
        gosi_employee_share DECIMAL(18, 4) DEFAULT 0,
        gosi_employer_share DECIMAL(18, 4) DEFAULT 0,
        violation_deduction DECIMAL(18, 4) DEFAULT 0,
        loan_deduction DECIMAL(18, 4) DEFAULT 0,
        deductions DECIMAL(18, 4) DEFAULT 0,
        net_salary DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== JOB OPENINGS & APPLICATIONS (HR Recruitment) =====
    CREATE TABLE IF NOT EXISTS job_openings (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        department_id INTEGER REFERENCES departments(id),
        position_id INTEGER,
        description TEXT,
        requirements TEXT,
        employment_type VARCHAR(50) DEFAULT 'full_time',
        vacancies INTEGER DEFAULT 1,
        status VARCHAR(30) DEFAULT 'open',
        branch_id INTEGER REFERENCES branches(id),
        published_at TIMESTAMPTZ,
        closing_date DATE,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS job_applications (
        id SERIAL PRIMARY KEY,
        opening_id INTEGER REFERENCES job_openings(id),
        applicant_name VARCHAR(255) NOT NULL,
        email VARCHAR(255),
        phone VARCHAR(50),
        resume_url TEXT,
        cover_letter TEXT,
        stage VARCHAR(50) DEFAULT 'applied',
        rating INTEGER DEFAULT 0,
        interview_date TIMESTAMPTZ,
        interviewer_id INTEGER REFERENCES company_users(id),
        notes TEXT,
        status VARCHAR(30) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- ===== LEAVE CARRYOVER =====
    CREATE TABLE IF NOT EXISTS leave_carryover (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES employees(id),
        leave_type VARCHAR(50) NOT NULL,
        year INTEGER NOT NULL,
        entitled_days NUMERIC(6, 1) DEFAULT 0,
        used_days NUMERIC(6, 1) DEFAULT 0,
        carried_days NUMERIC(6, 1) DEFAULT 0,
        expired_days NUMERIC(6, 1) DEFAULT 0,
        max_carryover NUMERIC(6, 1) DEFAULT 5,
        calculated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(employee_id, leave_type, year)
    );

    CREATE INDEX IF NOT EXISTS idx_job_openings_status ON job_openings(status);
    CREATE INDEX IF NOT EXISTS idx_job_applications_opening ON job_applications(opening_id);
    CREATE INDEX IF NOT EXISTS idx_leave_carryover_emp ON leave_carryover(employee_id, year);
    """


def get_financial_tables_sql() -> str:
    """Financial, Assets, Tax, Projects tables"""
    return """
    -- ===== AR/AP TABLES (6) =====
    CREATE TABLE IF NOT EXISTS customer_balances (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id) UNIQUE,
        currency VARCHAR(3) DEFAULT NULL,
        total_receivable DECIMAL(18, 4) DEFAULT 0,
        total_paid DECIMAL(18, 4) DEFAULT 0,
        outstanding_balance DECIMAL(18, 4) DEFAULT 0,
        overdue_amount DECIMAL(18, 4) DEFAULT 0,
        aging_30 DECIMAL(18, 4) DEFAULT 0,
        aging_60 DECIMAL(18, 4) DEFAULT 0,
        aging_90 DECIMAL(18, 4) DEFAULT 0,
        aging_120 DECIMAL(18, 4) DEFAULT 0,
        aging_120_plus DECIMAL(18, 4) DEFAULT 0,
        last_payment_date DATE,
        last_invoice_date DATE,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS supplier_balances (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER REFERENCES suppliers(id) UNIQUE,
        currency VARCHAR(3) DEFAULT NULL,
        total_payable DECIMAL(18, 4) DEFAULT 0,
        total_paid DECIMAL(18, 4) DEFAULT 0,
        outstanding_balance DECIMAL(18, 4) DEFAULT 0,
        overdue_amount DECIMAL(18, 4) DEFAULT 0,
        aging_30 DECIMAL(18, 4) DEFAULT 0,
        aging_60 DECIMAL(18, 4) DEFAULT 0,
        aging_90 DECIMAL(18, 4) DEFAULT 0,
        aging_120 DECIMAL(18, 4) DEFAULT 0,
        aging_120_plus DECIMAL(18, 4) DEFAULT 0,
        last_payment_date DATE,
        last_invoice_date DATE,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS receipts (
        id SERIAL PRIMARY KEY,
        receipt_number VARCHAR(50) UNIQUE,
        receipt_type VARCHAR(50) NOT NULL,
        customer_id INTEGER REFERENCES customers(id),
        supplier_id INTEGER REFERENCES suppliers(id),
        receipt_date DATE NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(3) DEFAULT NULL,
        exchange_rate DECIMAL(10, 6) DEFAULT 1,
        payment_method VARCHAR(50),
        bank_account_id INTEGER,
        reference VARCHAR(100),
        check_number VARCHAR(50),
        check_date DATE,
        notes TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        payment_number VARCHAR(50) UNIQUE,
        payment_type VARCHAR(50) NOT NULL,
        customer_id INTEGER REFERENCES customers(id),
        supplier_id INTEGER REFERENCES suppliers(id),
        payment_date DATE NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(3) DEFAULT NULL,
        exchange_rate DECIMAL(10, 6) DEFAULT 1,
        payment_method VARCHAR(50),
        bank_account_id INTEGER,
        reference VARCHAR(100),
        check_number VARCHAR(50),
        check_date DATE,
        notes TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS pending_receivables (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id),
        invoice_id INTEGER REFERENCES invoices(id),
        invoice_number VARCHAR(50),
        due_date DATE,
        amount DECIMAL(18, 4) DEFAULT 0,
        paid_amount DECIMAL(18, 4) DEFAULT 0,
        outstanding_amount DECIMAL(18, 4) DEFAULT 0,
        days_overdue INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS pending_payables (
        id SERIAL PRIMARY KEY,
        supplier_id INTEGER REFERENCES suppliers(id),
        invoice_id INTEGER REFERENCES invoices(id),
        invoice_number VARCHAR(50),
        due_date DATE,
        amount DECIMAL(18, 4) DEFAULT 0,
        paid_amount DECIMAL(18, 4) DEFAULT 0,
        outstanding_amount DECIMAL(18, 4) DEFAULT 0,
        days_overdue INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== FISCAL YEARS =====
    CREATE TABLE IF NOT EXISTS fiscal_years (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL UNIQUE,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed')),
        retained_earnings_account_id INTEGER REFERENCES accounts(id),
        closing_entry_id INTEGER,  -- references journal_entries(id) after closing
        closed_by INTEGER REFERENCES company_users(id),
        closed_at TIMESTAMPTZ,
        reopened_by INTEGER REFERENCES company_users(id),
        reopened_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== RECURRING JOURNAL TEMPLATES (ACC-003) =====
    CREATE TABLE IF NOT EXISTS recurring_journal_templates (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        reference VARCHAR(100),
        frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
        start_date DATE NOT NULL,
        end_date DATE,
        next_run_date DATE NOT NULL,
        last_run_date DATE,
        is_active BOOLEAN DEFAULT TRUE,
        auto_post BOOLEAN DEFAULT FALSE,
        branch_id INTEGER REFERENCES branches(id),
        currency VARCHAR(10) DEFAULT 'SAR',
        exchange_rate DECIMAL(18,6) DEFAULT 1.0,
        run_count INTEGER DEFAULT 0,
        max_runs INTEGER,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS recurring_journal_lines (
        id SERIAL PRIMARY KEY,
        template_id INTEGER NOT NULL REFERENCES recurring_journal_templates(id) ON DELETE CASCADE,
        account_id INTEGER NOT NULL REFERENCES accounts(id),
        debit DECIMAL(18,4) DEFAULT 0,
        credit DECIMAL(18,4) DEFAULT 0,
        description TEXT,
        cost_center_id INTEGER
    );

    -- ===== FISCAL PERIODS =====
    CREATE TABLE IF NOT EXISTS fiscal_periods (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        fiscal_year INTEGER,
        is_closed BOOLEAN DEFAULT FALSE,
        closed_by INTEGER REFERENCES company_users(id),
        closed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );



    -- ===== BUDGETS & REPORTS (5) =====
    CREATE TABLE IF NOT EXISTS budgets (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        budget_code VARCHAR(50) UNIQUE,
        budget_name VARCHAR(255),
        budget_name_en VARCHAR(255),
        description TEXT,
        fiscal_year INTEGER,
        branch_id INTEGER REFERENCES branches(id),
        department_id INTEGER REFERENCES departments(id),
        cost_center_id INTEGER REFERENCES cost_centers(id),
        budget_type VARCHAR(30) DEFAULT 'annual',
        status VARCHAR(20) DEFAULT 'draft',
        total_budget DECIMAL(18, 4) DEFAULT 0,
        used_budget DECIMAL(18, 4) DEFAULT 0,
        remaining_budget DECIMAL(18, 4) DEFAULT 0,
        start_date DATE,
        end_date DATE,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS budget_items (
        id SERIAL PRIMARY KEY,
        budget_id INTEGER REFERENCES budgets(id) ON DELETE CASCADE,
        account_id INTEGER REFERENCES accounts(id),
        planned_amount DECIMAL(18, 4) DEFAULT 0,
        actual_amount DECIMAL(18, 4) DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS budget_lines (
        id SERIAL PRIMARY KEY,
        budget_id INTEGER REFERENCES budgets(id) ON DELETE CASCADE,
        account_id INTEGER REFERENCES accounts(id),
        budget_amount DECIMAL(18, 4) DEFAULT 0,
        used_amount DECIMAL(18, 4) DEFAULT 0,
        remaining_amount DECIMAL(18, 4) DEFAULT 0,
        percentage DECIMAL(5, 2) DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS cost_centers_budgets (
        id SERIAL PRIMARY KEY,
        cost_center_id INTEGER REFERENCES cost_centers(id),
        budget_id INTEGER REFERENCES budgets(id),
        allocated_amount DECIMAL(18, 4) DEFAULT 0,
        used_amount DECIMAL(18, 4) DEFAULT 0,
        fiscal_year INTEGER,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS financial_reports (
        id SERIAL PRIMARY KEY,
        report_name VARCHAR(255) NOT NULL,
        report_type VARCHAR(50) NOT NULL,
        report_period VARCHAR(50),
        generated_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        parameters JSONB DEFAULT '{}',
        data JSONB DEFAULT '{}',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS report_templates (
        id SERIAL PRIMARY KEY,
        template_name VARCHAR(255) NOT NULL,
        template_type VARCHAR(50) NOT NULL,
        description TEXT,
        parameters JSONB DEFAULT '{}',
        template_content TEXT,
        is_default BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    -- ===== FIXED ASSETS (5) =====
    CREATE TABLE IF NOT EXISTS asset_categories (
        id SERIAL PRIMARY KEY,
        category_code VARCHAR(50) UNIQUE,
        category_name VARCHAR(255) NOT NULL,
        category_name_en VARCHAR(255),
        description TEXT,
        depreciation_rate DECIMAL(5, 2) DEFAULT 0,
        useful_life INTEGER DEFAULT 0,
        parent_id INTEGER REFERENCES asset_categories(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS assets (
        id SERIAL PRIMARY KEY,
        company_id VARCHAR(100),
        branch_id INTEGER REFERENCES branches(id),
        name VARCHAR(255) NOT NULL,
        code VARCHAR(50) UNIQUE,
        type VARCHAR(50), -- 'tangible', 'intangible'
        purchase_date DATE,
        cost DECIMAL(18, 4) DEFAULT 0,
        residual_value DECIMAL(18, 4) DEFAULT 0,
        life_years INTEGER DEFAULT 0,
        currency VARCHAR(3) DEFAULT NULL,
        depreciation_method VARCHAR(50) DEFAULT 'straight_line',
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS asset_depreciation_schedule (
        id SERIAL PRIMARY KEY,
        asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
        fiscal_year INTEGER,
        date DATE,
        amount DECIMAL(18, 4) DEFAULT 0,
        accumulated_amount DECIMAL(18, 4) DEFAULT 0,
        book_value DECIMAL(18, 4) DEFAULT 0,
        posted BOOLEAN DEFAULT FALSE,
        journal_entry_id INTEGER, -- REFERENCES journal_entries(id)
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS asset_transfers (
        id SERIAL PRIMARY KEY,
        asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
        from_location VARCHAR(255),
        to_location VARCHAR(255),
        transfer_date DATE NOT NULL,
        reason TEXT,
        condition VARCHAR(50),
        approved_by INTEGER,
        status VARCHAR(20) DEFAULT 'pending',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS asset_disposals (
        id SERIAL PRIMARY KEY,
        asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
        disposal_date DATE NOT NULL,
        disposal_method VARCHAR(50),
        disposal_value DECIMAL(18, 4) DEFAULT 0,
        disposal_reason TEXT,
        buyer_name VARCHAR(255),
        buyer_id INTEGER,
        notes TEXT,
        approved_by INTEGER,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== ASSET ADVANCED (Revaluations, Insurance, Maintenance) =====
    CREATE TABLE IF NOT EXISTS asset_revaluations (
        id SERIAL PRIMARY KEY,
        asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
        revaluation_date DATE NOT NULL,
        old_value NUMERIC(15, 2) NOT NULL,
        new_value NUMERIC(15, 2) NOT NULL,
        difference NUMERIC(15, 2) NOT NULL,
        reason TEXT,
        journal_entry_id INTEGER,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS asset_insurance (
        id SERIAL PRIMARY KEY,
        asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
        policy_number VARCHAR(100),
        insurer VARCHAR(255),
        coverage_type VARCHAR(100),
        premium_amount NUMERIC(15, 2) DEFAULT 0,
        coverage_amount NUMERIC(15, 2) DEFAULT 0,
        start_date DATE,
        end_date DATE,
        status VARCHAR(30) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS asset_maintenance (
        id SERIAL PRIMARY KEY,
        asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
        maintenance_type VARCHAR(50) DEFAULT 'preventive',
        description TEXT,
        scheduled_date DATE,
        completed_date DATE,
        cost NUMERIC(15, 2) DEFAULT 0,
        vendor VARCHAR(255),
        status VARCHAR(30) DEFAULT 'scheduled',
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_asset_revaluations_asset ON asset_revaluations(asset_id);
    CREATE INDEX IF NOT EXISTS idx_asset_insurance_asset ON asset_insurance(asset_id);
    CREATE INDEX IF NOT EXISTS idx_asset_maintenance_asset ON asset_maintenance(asset_id);

    -- ===== TAX TABLES (4) =====
    CREATE TABLE IF NOT EXISTS tax_rates (
        id SERIAL PRIMARY KEY,
        tax_code VARCHAR(50) UNIQUE,
        tax_name VARCHAR(255) NOT NULL,
        tax_name_en VARCHAR(255),
        rate_type VARCHAR(20) DEFAULT 'percentage',
        rate_value DECIMAL(10, 4) DEFAULT 0,
        country_code VARCHAR(5) DEFAULT NULL,
        description TEXT,
        effective_from DATE,
        effective_to DATE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS tax_groups (
        id SERIAL PRIMARY KEY,
        group_code VARCHAR(50) UNIQUE,
        group_name VARCHAR(255) NOT NULL,
        group_name_en VARCHAR(255),
        description TEXT,
        tax_ids JSONB DEFAULT '[]',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS tax_returns (
        id SERIAL PRIMARY KEY,
        return_number VARCHAR(50) UNIQUE,
        tax_period VARCHAR(50),
        tax_type VARCHAR(50) NOT NULL,
        taxable_amount DECIMAL(18, 4) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        penalty_amount DECIMAL(18, 4) DEFAULT 0,
        interest_amount DECIMAL(18, 4) DEFAULT 0,
        total_amount DECIMAL(18, 4) DEFAULT 0,
        due_date DATE,
        filed_date DATE,
        status VARCHAR(20) DEFAULT 'draft',
        branch_id INTEGER REFERENCES branches(id),
        jurisdiction_code VARCHAR(2),
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS tax_payments (
        id SERIAL PRIMARY KEY,
        payment_number VARCHAR(50) UNIQUE,
        tax_return_id INTEGER REFERENCES tax_returns(id),
        payment_date DATE NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        payment_method VARCHAR(50),
        reference VARCHAR(100),
        status VARCHAR(20) DEFAULT 'pending',
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    -- ===== TAX COMPLIANCE TABLES (3) =====
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

    CREATE INDEX IF NOT EXISTS idx_tax_regimes_country ON tax_regimes(country_code);
    CREATE INDEX IF NOT EXISTS idx_branch_tax_settings_branch ON branch_tax_settings(branch_id);

    -- ===== PROJECTS (5) =====
    CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        project_code VARCHAR(50) UNIQUE,
        project_name VARCHAR(255) NOT NULL,
        project_name_en VARCHAR(255),
        description TEXT,
        customer_id INTEGER REFERENCES customers(id),
        project_type VARCHAR(50),
        status VARCHAR(20) DEFAULT 'planning',
        start_date DATE,
        end_date DATE,
        planned_budget DECIMAL(18, 4) DEFAULT 0,
        actual_cost DECIMAL(18, 4) DEFAULT 0,
        progress_percentage DECIMAL(5, 2) DEFAULT 0,
        manager_id INTEGER REFERENCES employees(id),
        branch_id INTEGER,
        contract_type VARCHAR(30) DEFAULT 'fixed_price',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS project_tasks (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        task_name VARCHAR(255) NOT NULL,
        task_name_en VARCHAR(255),
        description TEXT,
        parent_task_id INTEGER REFERENCES project_tasks(id),
        start_date DATE,
        end_date DATE,
        planned_hours DECIMAL(10, 2) DEFAULT 0,
        actual_hours DECIMAL(10, 2) DEFAULT 0,
        progress DECIMAL(5, 2) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        assigned_to INTEGER REFERENCES employees(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS project_budgets (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        budget_type VARCHAR(50) NOT NULL,
        planned_amount DECIMAL(18, 4) DEFAULT 0,
        actual_amount DECIMAL(18, 4) DEFAULT 0,
        variance DECIMAL(18, 4) DEFAULT 0,
        approved_by INTEGER REFERENCES company_users(id),
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS project_expenses (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        expense_type VARCHAR(50) NOT NULL,
        expense_date DATE NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        description TEXT,
        receipt_id INTEGER,
        approved_by INTEGER REFERENCES company_users(id),
        status VARCHAR(20) DEFAULT 'pending',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS project_revenues (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        revenue_type VARCHAR(50) NOT NULL,
        revenue_date DATE NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        description TEXT,
        invoice_id INTEGER,
        approved_by INTEGER REFERENCES company_users(id),
        status VARCHAR(20) DEFAULT 'pending',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS project_documents (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        file_name VARCHAR(255) NOT NULL,
        file_url TEXT NOT NULL,
        file_type VARCHAR(50),
        uploaded_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS project_change_orders (
        id SERIAL PRIMARY KEY,
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        change_order_number VARCHAR(50),
        title VARCHAR(255) NOT NULL,
        description TEXT,
        change_type VARCHAR(50) DEFAULT 'scope',
        cost_impact DECIMAL(18, 4) DEFAULT 0,
        time_impact_days INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        requested_by INTEGER REFERENCES company_users(id),
        approved_by INTEGER REFERENCES company_users(id),
        approved_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    -- ===== ATTACHMENTS (3) =====
    CREATE TABLE IF NOT EXISTS document_types (
        id SERIAL PRIMARY KEY,
        type_code VARCHAR(50) UNIQUE,
        type_name VARCHAR(255) NOT NULL,
        type_name_en VARCHAR(255),
        description TEXT,
        allowed_extensions VARCHAR(255) DEFAULT 'pdf,jpg,png,doc,docx,xls,xlsx',
        max_size INTEGER DEFAULT 10485760,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS attachments (
        id SERIAL PRIMARY KEY,
        entity_type VARCHAR(50) NOT NULL,
        entity_id INTEGER NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        file_type VARCHAR(50),
        mime_type VARCHAR(100),
        description TEXT,
        uploaded_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS document_templates (
        id SERIAL PRIMARY KEY,
        template_name VARCHAR(255) NOT NULL,
        template_type VARCHAR(50) NOT NULL,
        description TEXT,
        template_content TEXT,
        variables JSONB DEFAULT '{}',
        is_default BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    -- (Duplicate notifications table removed)
    
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        sender_id INTEGER REFERENCES company_users(id),
        receiver_id INTEGER REFERENCES company_users(id),
        subject VARCHAR(255),
        body TEXT,
        message_type VARCHAR(50) DEFAULT 'internal',
        is_read BOOLEAN DEFAULT FALSE,
        read_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS email_templates (
        id SERIAL PRIMARY KEY,
        template_name VARCHAR(255) NOT NULL,
        subject VARCHAR(255),
        body TEXT,
        variables JSONB DEFAULT '{}',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== DASHBOARD LAYOUTS =====
    CREATE TABLE IF NOT EXISTS dashboard_layouts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES company_users(id),
        layout_name VARCHAR(255) DEFAULT 'default',
        widgets JSONB DEFAULT '[]'::jsonb,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== SALES TARGETS =====
    CREATE TABLE IF NOT EXISTS sales_targets (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        month_number INTEGER NOT NULL,
        target_amount DECIMAL(18, 4) DEFAULT 0,
        branch_id INTEGER REFERENCES branches(id),
        salesperson_id INTEGER,
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_sales_targets_unique ON sales_targets(year, month_number, COALESCE(branch_id, 0), COALESCE(salesperson_id, 0));

    CREATE INDEX IF NOT EXISTS idx_dashboard_layouts_user ON dashboard_layouts(user_id);
    CREATE INDEX IF NOT EXISTS idx_sales_targets_year ON sales_targets(year);
    """


def get_treasury_tables_sql() -> str:
    """Returns SQL for Treasury tables"""
    return """
    -- ===== TREASURY TABLES (2) =====


    CREATE TABLE IF NOT EXISTS treasury_transactions (
        id SERIAL PRIMARY KEY,
        transaction_number VARCHAR(50) UNIQUE,
        transaction_date DATE NOT NULL,
        transaction_type VARCHAR(50) NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        treasury_id INTEGER REFERENCES treasury_accounts(id),
        target_account_id INTEGER REFERENCES accounts(id),
        target_treasury_id INTEGER REFERENCES treasury_accounts(id),
        branch_id INTEGER REFERENCES branches(id),
        description TEXT,
        reference_number VARCHAR(100),
        status VARCHAR(20) DEFAULT 'posted',
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS bank_reconciliations (
        id SERIAL PRIMARY KEY,
        treasury_account_id INTEGER REFERENCES treasury_accounts(id),
        statement_date DATE NOT NULL,
        start_balance DECIMAL(18, 4) DEFAULT 0,
        end_balance DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        branch_id INTEGER REFERENCES branches(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS bank_statement_lines (
        id SERIAL PRIMARY KEY,
        reconciliation_id INTEGER REFERENCES bank_reconciliations(id) ON DELETE CASCADE,
        transaction_date DATE NOT NULL,
        description TEXT,
        reference VARCHAR(100),
        debit DECIMAL(18, 4) DEFAULT 0,
        credit DECIMAL(18, 4) DEFAULT 0,
        balance DECIMAL(18, 4) DEFAULT 0,
        is_reconciled BOOLEAN DEFAULT FALSE,
        matched_journal_line_id INTEGER REFERENCES journal_lines(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== CHECKS MANAGEMENT =====
    CREATE TABLE IF NOT EXISTS checks_receivable (
        id SERIAL PRIMARY KEY,
        check_number VARCHAR(50) NOT NULL,
        drawer_name VARCHAR(200),
        bank_name VARCHAR(200),
        branch_name VARCHAR(100),
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(10) DEFAULT 'SAR',
        issue_date DATE,
        due_date DATE NOT NULL,
        collection_date DATE,
        bounce_date DATE,
        party_id INTEGER REFERENCES parties(id),
        treasury_account_id INTEGER REFERENCES treasury_accounts(id),
        receipt_id INTEGER,
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        collection_journal_id INTEGER REFERENCES journal_entries(id),
        bounce_journal_id INTEGER REFERENCES journal_entries(id),
        status VARCHAR(30) DEFAULT 'pending',
        bounce_reason TEXT,
        notes TEXT,
        branch_id INTEGER REFERENCES branches(id),
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS checks_payable (
        id SERIAL PRIMARY KEY,
        check_number VARCHAR(50) NOT NULL,
        beneficiary_name VARCHAR(200),
        bank_name VARCHAR(200),
        branch_name VARCHAR(100),
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(10) DEFAULT 'SAR',
        issue_date DATE NOT NULL,
        due_date DATE NOT NULL,
        clearance_date DATE,
        bounce_date DATE,
        party_id INTEGER REFERENCES parties(id),
        treasury_account_id INTEGER REFERENCES treasury_accounts(id),
        payment_voucher_id INTEGER,
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        clearance_journal_id INTEGER REFERENCES journal_entries(id),
        bounce_journal_id INTEGER REFERENCES journal_entries(id),
        status VARCHAR(30) DEFAULT 'issued',
        bounce_reason TEXT,
        notes TEXT,
        branch_id INTEGER REFERENCES branches(id),
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== NOTES RECEIVABLE / PAYABLE =====
    CREATE TABLE IF NOT EXISTS notes_receivable (
        id SERIAL PRIMARY KEY,
        note_number VARCHAR(50) NOT NULL,
        drawer_name VARCHAR(200),
        bank_name VARCHAR(200),
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(10) DEFAULT 'SAR',
        issue_date DATE,
        due_date DATE NOT NULL,
        maturity_date DATE,
        collection_date DATE,
        protest_date DATE,
        party_id INTEGER REFERENCES parties(id),
        treasury_account_id INTEGER REFERENCES treasury_accounts(id),
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        collection_journal_id INTEGER REFERENCES journal_entries(id),
        protest_journal_id INTEGER REFERENCES journal_entries(id),
        status VARCHAR(20) DEFAULT 'pending',
        protest_reason TEXT,
        notes TEXT,
        branch_id INTEGER REFERENCES branches(id),
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS notes_payable (
        id SERIAL PRIMARY KEY,
        note_number VARCHAR(50) NOT NULL,
        beneficiary_name VARCHAR(200),
        bank_name VARCHAR(200),
        amount DECIMAL(18, 4) NOT NULL,
        currency VARCHAR(10) DEFAULT 'SAR',
        issue_date DATE,
        due_date DATE NOT NULL,
        maturity_date DATE,
        payment_date DATE,
        protest_date DATE,
        party_id INTEGER REFERENCES parties(id),
        treasury_account_id INTEGER REFERENCES treasury_accounts(id),
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        payment_journal_id INTEGER REFERENCES journal_entries(id),
        protest_journal_id INTEGER REFERENCES journal_entries(id),
        status VARCHAR(20) DEFAULT 'issued',
        protest_reason TEXT,
        notes TEXT,
        branch_id INTEGER REFERENCES branches(id),
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== EXPENSES TABLE (1) =====
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        expense_number VARCHAR(50) UNIQUE NOT NULL,
        expense_date DATE NOT NULL,
        expense_type VARCHAR(50) NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        description TEXT,
        category VARCHAR(50) DEFAULT 'general',
        payment_method VARCHAR(50) DEFAULT 'cash',
        treasury_id INTEGER REFERENCES treasury_accounts(id),
        expense_account_id INTEGER REFERENCES accounts(id),
        cost_center_id INTEGER REFERENCES cost_centers(id),
        project_id INTEGER REFERENCES projects(id),
        journal_entry_id INTEGER REFERENCES journal_entries(id),
        branch_id INTEGER REFERENCES branches(id),
        approval_status VARCHAR(20) DEFAULT 'pending',
        approved_by INTEGER REFERENCES company_users(id),
        approved_at TIMESTAMPTZ,
        approval_notes TEXT,
        receipt_number VARCHAR(100),
        vendor_name VARCHAR(255),
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """


def get_currency_tables_sql() -> str:
    """Returns SQL for Multi-Currency System tables"""
    return """
    -- ===== MULTI-CURRENCY TABLES (3) =====
    CREATE TABLE IF NOT EXISTS currencies (
        id SERIAL PRIMARY KEY,
        code VARCHAR(3) UNIQUE NOT NULL, -- USD, EUR, SAR
        name VARCHAR(100) NOT NULL,
        name_en VARCHAR(100),
        symbol VARCHAR(10),
        is_base BOOLEAN DEFAULT FALSE,
        current_rate DECIMAL(18, 6) DEFAULT 1, -- Relative to base currency
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS exchange_rates (
        id SERIAL PRIMARY KEY,
        currency_id INTEGER REFERENCES currencies(id) ON DELETE CASCADE,
        rate_date DATE NOT NULL,
        rate DECIMAL(18, 6) NOT NULL,
        source VARCHAR(50) DEFAULT 'manual', -- manual, api
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(currency_id, rate_date)
    );

    CREATE TABLE IF NOT EXISTS currency_transactions (
        id SERIAL PRIMARY KEY,
        transaction_type VARCHAR(50) NOT NULL, -- invoice, payment, journal
        transaction_id INTEGER NOT NULL, -- ID of the related record
        account_id INTEGER REFERENCES accounts(id), -- Critical for revaluation
        currency_code VARCHAR(3) NOT NULL,
        exchange_rate DECIMAL(18, 6) NOT NULL,
        amount_fc DECIMAL(18, 4) NOT NULL, -- Amount in Foreign Currency
        amount_bc DECIMAL(18, 4) NOT NULL, -- Amount in Base Currency
        description TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """
    
def get_contract_tables_sql() -> str:
    """Returns SQL for Contracts & Subscriptions tables"""
    return """
    -- ===== CONTRACTS & SUBSCRIPTIONS (2) =====
    CREATE TABLE IF NOT EXISTS contracts (
        id SERIAL PRIMARY KEY,
        contract_number VARCHAR(50) UNIQUE NOT NULL,
        party_id INTEGER REFERENCES parties(id),
        contract_type VARCHAR(50) DEFAULT 'subscription', -- fixed, subscription, recurring
        status VARCHAR(20) DEFAULT 'draft', -- draft, active, expired, cancelled
        start_date DATE NOT NULL,
        end_date DATE,
        billing_interval VARCHAR(20) DEFAULT 'monthly', -- monthly, quarterly, yearly
        next_billing_date DATE,
        total_amount DECIMAL(18, 4) DEFAULT 0,
        currency VARCHAR(3) DEFAULT 'SAR',
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS contract_items (
        id SERIAL PRIMARY KEY,
        contract_id INTEGER REFERENCES contracts(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        description TEXT,
        quantity DECIMAL(18, 4) DEFAULT 1,
        unit_price DECIMAL(18, 4) DEFAULT 0,
        tax_rate DECIMAL(5, 2) DEFAULT 15,
        total DECIMAL(18, 4) DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """


def get_costing_policy_tables_sql() -> str:
    """Returns SQL for Costing Policy tables"""
    return """
    -- ===== COSTING POLICY TABLES (3) =====
    CREATE TABLE IF NOT EXISTS costing_policies (
        id SERIAL PRIMARY KEY,
        policy_name VARCHAR(100) NOT NULL,
        policy_type VARCHAR(50) NOT NULL, -- global_wac, per_warehouse_wac, hybrid, smart
        description TEXT,
        is_active BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_by INTEGER
    );

    CREATE TABLE IF NOT EXISTS costing_policy_details (
        id SERIAL PRIMARY KEY,
        policy_id INTEGER NOT NULL REFERENCES costing_policies(id) ON DELETE CASCADE,
        setting_key VARCHAR(100) NOT NULL,
        setting_value VARCHAR(500)
    );

    CREATE TABLE IF NOT EXISTS costing_policy_history (
        id SERIAL PRIMARY KEY,
        old_policy_type VARCHAR(50),
        new_policy_type VARCHAR(50),
        change_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        changed_by INTEGER,
        reason TEXT,
        affected_products_count INTEGER,
        total_cost_impact DECIMAL(18, 4),
        status VARCHAR(20) DEFAULT 'completed'
    );

    CREATE TABLE IF NOT EXISTS inventory_cost_snapshots (
        id SERIAL PRIMARY KEY,
        warehouse_id INTEGER,
        product_id INTEGER,
        average_cost DECIMAL(18, 4),
        quantity DECIMAL(18, 4),
        policy_type VARCHAR(50),
        snapshot_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """


def get_advanced_inventory_tables_sql() -> str:
    """Returns SQL for advanced inventory tables (Batch, Serial, Expiry, QC, Cycle Counts)"""
    return """
    ALTER TABLE products ADD COLUMN IF NOT EXISTS has_batch_tracking BOOLEAN DEFAULT FALSE;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS has_serial_tracking BOOLEAN DEFAULT FALSE;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS has_expiry_tracking BOOLEAN DEFAULT FALSE;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS shelf_life_days INTEGER DEFAULT 0;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS expiry_alert_days INTEGER DEFAULT 30;

    -- ===== BATCH NUMBERS (INV-101) =====
    CREATE TABLE IF NOT EXISTS product_batches (
        id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL REFERENCES products(id),
        warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
        batch_number VARCHAR(100) NOT NULL,
        manufacturing_date DATE,
        expiry_date DATE,
        quantity DECIMAL(18, 4) DEFAULT 0,
        available_quantity DECIMAL(18, 4) DEFAULT 0,
        unit_cost DECIMAL(18, 4) DEFAULT 0,
        supplier_id INTEGER,
        reference_type VARCHAR(50),
        reference_id INTEGER,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(product_id, warehouse_id, batch_number)
    );

    -- ===== SERIAL NUMBERS (INV-102) =====
    CREATE TABLE IF NOT EXISTS product_serials (
        id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL REFERENCES products(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        serial_number VARCHAR(200) NOT NULL,
        batch_id INTEGER REFERENCES product_batches(id),
        status VARCHAR(20) DEFAULT 'available',
        purchase_date DATE,
        purchase_reference VARCHAR(100),
        purchase_price DECIMAL(18, 4) DEFAULT 0,
        sale_date DATE,
        sale_reference VARCHAR(100),
        sale_price DECIMAL(18, 4) DEFAULT 0,
        customer_id INTEGER,
        warranty_start DATE,
        warranty_end DATE,
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(product_id, serial_number)
    );

    -- ===== BATCH/SERIAL MOVEMENT LOG =====
    CREATE TABLE IF NOT EXISTS batch_serial_movements (
        id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL REFERENCES products(id),
        batch_id INTEGER REFERENCES product_batches(id),
        serial_id INTEGER REFERENCES product_serials(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        movement_type VARCHAR(50) NOT NULL,
        reference_type VARCHAR(50),
        reference_id INTEGER,
        quantity DECIMAL(18, 4) DEFAULT 1,
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== QUALITY CONTROL (INV-104) =====
    CREATE TABLE IF NOT EXISTS quality_inspections (
        id SERIAL PRIMARY KEY,
        inspection_number VARCHAR(50) UNIQUE,
        inspection_type VARCHAR(50) NOT NULL,
        product_id INTEGER NOT NULL REFERENCES products(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        batch_id INTEGER REFERENCES product_batches(id),
        reference_type VARCHAR(50),
        reference_id INTEGER,
        inspected_quantity DECIMAL(18, 4) DEFAULT 0,
        accepted_quantity DECIMAL(18, 4) DEFAULT 0,
        rejected_quantity DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        result_notes TEXT,
        rejection_reason TEXT,
        inspector_id INTEGER REFERENCES company_users(id),
        inspection_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        completed_date TIMESTAMPTZ,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS quality_inspection_criteria (
        id SERIAL PRIMARY KEY,
        inspection_id INTEGER NOT NULL REFERENCES quality_inspections(id) ON DELETE CASCADE,
        criteria_name VARCHAR(255) NOT NULL,
        expected_value VARCHAR(255),
        actual_value VARCHAR(255),
        is_passed BOOLEAN DEFAULT FALSE,
        notes TEXT
    );

    -- ===== CYCLE COUNTS (INV-105) =====
    CREATE TABLE IF NOT EXISTS cycle_counts (
        id SERIAL PRIMARY KEY,
        count_number VARCHAR(50) UNIQUE,
        warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
        count_type VARCHAR(50) DEFAULT 'full',
        status VARCHAR(20) DEFAULT 'draft',
        scheduled_date DATE,
        start_date TIMESTAMPTZ,
        end_date TIMESTAMPTZ,
        total_items INTEGER DEFAULT 0,
        counted_items INTEGER DEFAULT 0,
        variance_items INTEGER DEFAULT 0,
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cycle_count_items (
        id SERIAL PRIMARY KEY,
        cycle_count_id INTEGER NOT NULL REFERENCES cycle_counts(id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(id),
        batch_id INTEGER REFERENCES product_batches(id),
        system_quantity DECIMAL(18, 4) DEFAULT 0,
        counted_quantity DECIMAL(18, 4),
        variance DECIMAL(18, 4) DEFAULT 0,
        variance_value DECIMAL(18, 4) DEFAULT 0,
        unit_cost DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        counted_by INTEGER REFERENCES company_users(id),
        counted_at TIMESTAMPTZ,
        notes TEXT
    );
    """


def get_advanced_inventory_phase2_tables_sql() -> str:
    """Returns SQL for Phase 2 advanced inventory: Variants, Bins, Kits"""
    return """
    -- ===== PRODUCT ATTRIBUTES & VARIANTS (INV-106) =====
    CREATE TABLE IF NOT EXISTS product_attributes (
        id SERIAL PRIMARY KEY,
        attribute_name VARCHAR(100) NOT NULL,
        attribute_name_en VARCHAR(100),
        attribute_type VARCHAR(50) DEFAULT 'select',
        sort_order INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS product_attribute_values (
        id SERIAL PRIMARY KEY,
        attribute_id INTEGER NOT NULL REFERENCES product_attributes(id) ON DELETE CASCADE,
        value_name VARCHAR(100) NOT NULL,
        value_name_en VARCHAR(100),
        color_code VARCHAR(20),
        sort_order INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS product_variants (
        id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        variant_code VARCHAR(100),
        variant_name VARCHAR(255),
        sku VARCHAR(100),
        barcode VARCHAR(100),
        cost_price DECIMAL(15,2) DEFAULT 0,
        selling_price DECIMAL(15,2) DEFAULT 0,
        weight DECIMAL(10,3),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS product_variant_attributes (
        id SERIAL PRIMARY KEY,
        variant_id INTEGER NOT NULL REFERENCES product_variants(id) ON DELETE CASCADE,
        attribute_id INTEGER NOT NULL REFERENCES product_attributes(id),
        attribute_value_id INTEGER NOT NULL REFERENCES product_attribute_values(id),
        UNIQUE(variant_id, attribute_id)
    );

    -- ===== BIN LOCATIONS (INV-107) =====
    CREATE TABLE IF NOT EXISTS bin_locations (
        id SERIAL PRIMARY KEY,
        warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
        bin_code VARCHAR(50) NOT NULL,
        bin_name VARCHAR(100),
        zone VARCHAR(50),
        aisle VARCHAR(20),
        rack VARCHAR(20),
        shelf VARCHAR(20),
        position VARCHAR(20),
        bin_type VARCHAR(30) DEFAULT 'storage',
        max_weight DECIMAL(10,2),
        max_volume DECIMAL(10,2),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(warehouse_id, bin_code)
    );

    CREATE TABLE IF NOT EXISTS bin_inventory (
        id SERIAL PRIMARY KEY,
        bin_id INTEGER NOT NULL REFERENCES bin_locations(id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(id),
        batch_id INTEGER REFERENCES product_batches(id),
        quantity DECIMAL(15,4) DEFAULT 0,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(bin_id, product_id, batch_id)
    );

    -- ===== PRODUCT KITS (INV-108) =====
    CREATE TABLE IF NOT EXISTS product_kits (
        id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        kit_name VARCHAR(200),
        kit_type VARCHAR(30) DEFAULT 'fixed',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS product_kit_items (
        id SERIAL PRIMARY KEY,
        kit_id INTEGER NOT NULL REFERENCES product_kits(id) ON DELETE CASCADE,
        component_product_id INTEGER NOT NULL REFERENCES products(id),
        quantity DECIMAL(15,4) NOT NULL DEFAULT 1,
        unit_cost DECIMAL(15,2),
        sort_order INTEGER DEFAULT 0,
        notes TEXT
    );

    ALTER TABLE products ADD COLUMN IF NOT EXISTS has_variants BOOLEAN DEFAULT FALSE;
    ALTER TABLE products ADD COLUMN IF NOT EXISTS is_kit BOOLEAN DEFAULT FALSE;
    """


def get_manufacturing_tables_sql() -> str:
    """SQL for Advanced Manufacturing (Phase 5)"""
    return """
    -- ===== WORK CENTERS (MFG-001) =====
    CREATE TABLE IF NOT EXISTS work_centers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        code VARCHAR(50) UNIQUE,
        capacity_per_day DECIMAL(5, 2) DEFAULT 8.0, -- hours
        cost_per_hour DECIMAL(18, 4) DEFAULT 0,
        location VARCHAR(100),
        cost_center_id INTEGER REFERENCES cost_centers(id), -- For linking to Cost Accounting
        default_expense_account_id INTEGER REFERENCES accounts(id), -- For Overhead Absorption
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== ROUTING (MFG-002) =====
    CREATE TABLE IF NOT EXISTS manufacturing_routes (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        product_id INTEGER REFERENCES products(id), -- Default route for product
        is_active BOOLEAN DEFAULT TRUE,
        description TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS manufacturing_operations (
        id SERIAL PRIMARY KEY,
        route_id INTEGER REFERENCES manufacturing_routes(id) ON DELETE CASCADE,
        sequence INTEGER NOT NULL,
        work_center_id INTEGER REFERENCES work_centers(id),
        description VARCHAR(255),
        setup_time DECIMAL(8, 2) DEFAULT 0, -- minutes
        cycle_time DECIMAL(8, 2) DEFAULT 0, -- minutes per unit
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== BILL OF MATERIALS (MFG-003) =====
    CREATE TABLE IF NOT EXISTS bill_of_materials (
        id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(id), -- Output Product
        code VARCHAR(50),
        name VARCHAR(255),
        yield_quantity DECIMAL(15, 4) DEFAULT 1.0,
        route_id INTEGER REFERENCES manufacturing_routes(id),
        is_active BOOLEAN DEFAULT TRUE,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS bom_components (
        id SERIAL PRIMARY KEY,
        bom_id INTEGER REFERENCES bill_of_materials(id) ON DELETE CASCADE,
        component_product_id INTEGER REFERENCES products(id), -- Input Material
        quantity DECIMAL(15, 4) NOT NULL,
        waste_percentage DECIMAL(5, 2) DEFAULT 0,
        cost_share_percentage DECIMAL(5, 2) DEFAULT 0,
        is_percentage BOOLEAN DEFAULT FALSE, -- Variable BOM: quantity = % of order qty
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== BY-PRODUCTS (MFG-010) =====
    CREATE TABLE IF NOT EXISTS bom_outputs (
        id SERIAL PRIMARY KEY,
        bom_id INTEGER REFERENCES bill_of_materials(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id), -- Output Product (By-product)
        quantity DECIMAL(15, 4) NOT NULL,
        cost_allocation_percentage DECIMAL(5, 2) DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== PRODUCTION ORDERS (MFG-004) =====
    CREATE TABLE IF NOT EXISTS production_orders (
        id SERIAL PRIMARY KEY,
        order_number VARCHAR(50) UNIQUE,
        product_id INTEGER REFERENCES products(id),
        bom_id INTEGER REFERENCES bill_of_materials(id),
        route_id INTEGER REFERENCES manufacturing_routes(id),
        quantity DECIMAL(15, 4) NOT NULL,
        produced_quantity DECIMAL(15, 4) DEFAULT 0,
        scrapped_quantity DECIMAL(15, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'in_progress', 'completed', 'cancelled')),
        start_date DATE,
        due_date DATE,
        warehouse_id INTEGER REFERENCES warehouses(id), -- Logic: Raw materials source / FG destination? Usually separate.
        destination_warehouse_id INTEGER REFERENCES warehouses(id),
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS production_order_operations (
        id SERIAL PRIMARY KEY,
        production_order_id INTEGER REFERENCES production_orders(id) ON DELETE CASCADE,
        operation_id INTEGER REFERENCES manufacturing_operations(id),
        work_center_id INTEGER REFERENCES work_centers(id),
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped', 'paused')),
        worker_id INTEGER REFERENCES company_users(id),
        actual_setup_time DECIMAL(8, 2) DEFAULT 0,
        actual_run_time DECIMAL(8, 2) DEFAULT 0,
        completed_quantity DECIMAL(15, 4) DEFAULT 0,
        scrapped_quantity DECIMAL(15, 4) DEFAULT 0,
        planned_start_time TIMESTAMPTZ,
        planned_end_time TIMESTAMPTZ,
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== MRP - Material Requirements Planning (MFG-005) =====
    CREATE TABLE IF NOT EXISTS mrp_plans (
        id SERIAL PRIMARY KEY,
        plan_name VARCHAR(255) NOT NULL,
        production_order_id INTEGER REFERENCES production_orders(id) ON DELETE CASCADE,
        status VARCHAR(50) DEFAULT 'draft', -- draft, confirmed, converted
        calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        created_by INTEGER REFERENCES company_users(id)
    );

    CREATE TABLE IF NOT EXISTS mrp_items (
        id SERIAL PRIMARY KEY,
        mrp_plan_id INTEGER REFERENCES mrp_plans(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        required_quantity DECIMAL(18, 4) NOT NULL,
        available_quantity DECIMAL(18, 4) DEFAULT 0,
        on_hand_quantity DECIMAL(18, 4) DEFAULT 0,
        on_order_quantity DECIMAL(18, 4) DEFAULT 0,
        shortage_quantity DECIMAL(18, 4) DEFAULT 0,
        lead_time_days INTEGER DEFAULT 0,
        suggested_action VARCHAR(50), -- purchase_order, transfer, production_order
        status VARCHAR(50) DEFAULT 'pending'
    );

    -- ===== IN-PROCESS QC CHECKS (MFG-108) =====
    CREATE TABLE IF NOT EXISTS mfg_qc_checks (
        id SERIAL PRIMARY KEY,
        production_order_id INTEGER REFERENCES production_orders(id) ON DELETE CASCADE,
        operation_id INTEGER REFERENCES manufacturing_operations(id),
        check_name VARCHAR(200) NOT NULL,
        check_type VARCHAR(30) DEFAULT 'visual' CHECK (check_type IN ('visual','measurement','test','weight','count')),
        specification TEXT,
        actual_value VARCHAR(200),
        result VARCHAR(20) DEFAULT 'pending' CHECK (result IN ('pending','pass','fail','warning')),
        failure_action VARCHAR(20) DEFAULT 'warn' CHECK (failure_action IN ('stop','warn','continue')),
        checked_by INTEGER REFERENCES company_users(id),
        notes TEXT,
        checked_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- ===== EQUIPMENT & MAINTENANCE (MFG-011) =====
    CREATE TABLE IF NOT EXISTS manufacturing_equipment (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        code VARCHAR(50) UNIQUE,
        work_center_id INTEGER REFERENCES work_centers(id),
        status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'broken', 'retired')),
        purchase_date DATE,
        last_maintenance_date DATE,
        next_maintenance_date DATE,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS maintenance_logs (
        id SERIAL PRIMARY KEY,
        equipment_id INTEGER REFERENCES manufacturing_equipment(id) ON DELETE CASCADE,
        maintenance_type VARCHAR(50) NOT NULL, -- preventive, corrective, breakdown
        description TEXT,
        cost DECIMAL(18, 4) DEFAULT 0,
        performed_by INTEGER REFERENCES company_users(id),
        external_service_provider VARCHAR(255),
        maintenance_date DATE NOT NULL,
        next_due_date DATE,
        status VARCHAR(20) DEFAULT 'completed',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS project_timesheets (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES company_users(id),
        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
        task_id INTEGER REFERENCES project_tasks(id),
        date DATE NOT NULL,
        hours DECIMAL(5, 2) NOT NULL,
        description TEXT,
        status VARCHAR(20) DEFAULT 'draft',
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """


def sync_essential_columns(conn):
    """Ensure essential columns exist even in older companies"""
    columns_to_add = [
        # Phase 7 / Legacy
        ("journal_entries", "source", "VARCHAR(100)"),
        ("journal_entries", "source_id", "INTEGER"),
        ("products", "sku", "VARCHAR(100) UNIQUE"),
        # Budgets improvements (Phase 8.13)
        ("budgets", "name", "VARCHAR(255)"),
        ("budgets", "description", "TEXT"),
        ("budgets", "cost_center_id", "INTEGER"),
        ("budgets", "budget_type", "VARCHAR(30) DEFAULT 'annual'"),
        # POS treasury link
        ("pos_sessions", "treasury_account_id", "INTEGER REFERENCES treasury_accounts(id)"),
    ]

    for table, column, col_type in columns_to_add:
        try:
            query = text(f"""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column}'
            """)
            if not conn.execute(query).fetchone():
                logger.info(f"Adding missing column {column} to {table}")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        except Exception as e:
            logger.warning(f"Could not add column {column} to {table}: {e}")

    # Backfill budgets.name from budget_name for existing rows
    try:
        conn.execute(text(
            "UPDATE budgets SET name = budget_name WHERE name IS NULL AND budget_name IS NOT NULL"
        ))
    except Exception:
        pass

    # Ensure Phase 8.13 tables exist in older company DBs
    missing_tables_sql = [
        # budget_items
        """CREATE TABLE IF NOT EXISTS budget_items (
            id SERIAL PRIMARY KEY,
            budget_id INTEGER REFERENCES budgets(id) ON DELETE CASCADE,
            account_id INTEGER REFERENCES accounts(id),
            planned_amount DECIMAL(18, 4) DEFAULT 0,
            actual_amount DECIMAL(18, 4) DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )""",
        # commission_rules
        """CREATE TABLE IF NOT EXISTS commission_rules (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            salesperson_id INTEGER,
            product_id INTEGER,
            category_id INTEGER,
            rate_type VARCHAR(20) DEFAULT 'percentage',
            rate DECIMAL(10, 4) DEFAULT 0,
            min_amount DECIMAL(18, 4) DEFAULT 0,
            max_amount DECIMAL(18, 4),
            is_active BOOLEAN DEFAULT TRUE,
            branch_id INTEGER REFERENCES branches(id),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )""",
        # sales_commissions
        """CREATE TABLE IF NOT EXISTS sales_commissions (
            id SERIAL PRIMARY KEY,
            salesperson_id INTEGER,
            salesperson_name VARCHAR(255),
            invoice_id INTEGER,
            invoice_number VARCHAR(50),
            invoice_date DATE,
            invoice_total DECIMAL(18, 4) DEFAULT 0,
            commission_rate DECIMAL(10, 4) DEFAULT 0,
            commission_amount DECIMAL(18, 4) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            paid_date DATE,
            branch_id INTEGER REFERENCES branches(id),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(invoice_id, salesperson_id)
        )""",
        # stock_transfer_log
        """CREATE TABLE IF NOT EXISTS stock_transfer_log (
            id SERIAL PRIMARY KEY,
            shipment_id INTEGER,
            product_id INTEGER REFERENCES products(id),
            from_warehouse_id INTEGER REFERENCES warehouses(id),
            to_warehouse_id INTEGER REFERENCES warehouses(id),
            quantity DECIMAL(18, 4) DEFAULT 0,
            transfer_cost DECIMAL(18, 4) DEFAULT 0,
            from_avg_cost_before DECIMAL(18, 4) DEFAULT 0,
            to_avg_cost_before DECIMAL(18, 4) DEFAULT 0,
            to_avg_cost_after DECIMAL(18, 4) DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )""",
        # customer_price_list_items
        """CREATE TABLE IF NOT EXISTS customer_price_list_items (
            id SERIAL PRIMARY KEY,
            price_list_id INTEGER NOT NULL,
            product_id INTEGER REFERENCES products(id),
            price DECIMAL(18, 4) NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        )""",
    ]

    for sql in missing_tables_sql:
        try:
            conn.execute(text(sql))
        except Exception as e:
            logger.warning(f"Could not ensure table: {e}")



def create_company_tables(company_id: str, currency: str = "SAR") -> Tuple[bool, str]:
    """Create all 91 tables for a company database"""
    db_name = f"aman_{company_id}"
    connection_url = settings.get_company_database_url(company_id)
    
    try:
        company_engine = create_engine(connection_url, isolation_level="AUTOCOMMIT")
        
        with company_engine.connect() as conn:
            # Sync essential columns (Phase 7/8 updates for existing DBs)
            sync_essential_columns(conn)
            
            # Execute all table creation SQL
            sql_blocks = [
                get_all_table_sql(),                # 0: Core tables (Users, Branches, Parties, Accounts, Treasury Accounts, Invoices)
                get_additional_tables_sql(),         # 1: Additional/Legacy tables (Customers, Suppliers, Products, Inventories)
                get_organization_tables_sql(),       # 2: Org tables (Departments, Employees, Roles, Cost Centers)
                get_financial_tables_sql(),          # 3: Financial tables (Fiscal Years, Payroll, Budgets, Assets, Tax, Projects)
                get_treasury_tables_sql(),           # 4: Treasury tables (Transactions, Recon, Checks, Notes, Expenses)
                get_currency_tables_sql(),           # 5: Multi-currency
                get_pos_tables_sql(),                # 6: POS
                get_contract_tables_sql(),           # 7: Contracts
                get_costing_policy_tables_sql(),      # 8: Costing
                get_advanced_inventory_tables_sql(),  # 9: Adv Inv
                get_advanced_inventory_phase2_tables_sql(), # 10: Adv Inv Phase 2
                get_manufacturing_tables_sql(),       # 11: Manufacturing (Phase 5)
                get_approval_tables_sql(),            # 12: Approval Workflows (Phase 7)
                get_security_tables_sql(),            # 13: Security - 2FA, Passwords, Sessions (Phase 7)
                get_performance_indexes_sql()         # 14: Performance Indexes (Phase 7.5)
            ]
            
            for index, sql_block in enumerate(sql_blocks):
                # Replace default currency
                processed_sql = sql_block.replace("'SAR'", f"'{currency}'")
                
                # Split and execute individual statements
                statements = [s.strip() for s in processed_sql.split(';') if s.strip()]
                
                logger.info(f"Executing SQL block {index} ({len(statements)} statements)")
                for i, stmt in enumerate(statements):
                    try:
                        conn.execute(text(stmt + ";"))
                    except Exception as e:
                        logger.error(f"Failed at statement {i} in block {index}")
                        logger.error(f"Statement: {stmt[:100]}...")
                        logger.error(f"Error: {str(e)}")
                        raise e
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type)",
                "CREATE INDEX IF NOT EXISTS idx_accounts_parent ON accounts(parent_id)",
                "CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date)",
                "CREATE INDEX IF NOT EXISTS idx_journal_entries_status ON journal_entries(status)",
                "CREATE INDEX IF NOT EXISTS idx_journal_lines_account ON journal_lines(account_id)",
                "CREATE INDEX IF NOT EXISTS idx_journal_lines_entry ON journal_lines(journal_entry_id)",
                "CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)",
                "CREATE INDEX IF NOT EXISTS idx_invoices_party ON invoices(party_id)",
                "CREATE INDEX IF NOT EXISTS idx_invoices_type_status ON invoices(invoice_type, status)",
                "CREATE INDEX IF NOT EXISTS idx_invoices_branch ON invoices(branch_id)",
                "CREATE INDEX IF NOT EXISTS idx_company_users_username ON company_users(username)",
                "CREATE INDEX IF NOT EXISTS idx_company_users_email ON company_users(email)",
                "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
                "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
                "CREATE INDEX IF NOT EXISTS idx_products_code ON products(product_code)",
                "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory(warehouse_id)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_product_warehouse ON inventory(product_id, warehouse_id)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_txn_product ON inventory_transactions(product_id)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_txn_date ON inventory_transactions(transaction_date)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_txn_type ON inventory_transactions(transaction_type)",
                "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
                "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
                "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
                "CREATE INDEX IF NOT EXISTS idx_pos_orders_session ON pos_orders(session_id)",
                "CREATE INDEX IF NOT EXISTS idx_pos_orders_date ON pos_orders(order_date)",
                "CREATE INDEX IF NOT EXISTS idx_pos_sessions_status ON pos_sessions(status)",
                "CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department_id)",
                "CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON attendance(employee_id, date)",
                "CREATE INDEX IF NOT EXISTS idx_payroll_entries_period ON payroll_entries(period_id)",
                "CREATE INDEX IF NOT EXISTS idx_treasury_txn_date ON treasury_transactions(transaction_date)",
                "CREATE INDEX IF NOT EXISTS idx_treasury_txn_treasury ON treasury_transactions(treasury_id)",
                "CREATE INDEX IF NOT EXISTS idx_party_txn_party ON party_transactions(party_id)",
                "CREATE INDEX IF NOT EXISTS idx_party_txn_date ON party_transactions(transaction_date)",
            ]
            for idx in indexes:
                try:
                    conn.execute(text(idx))
                except Exception:
                    pass  # Ignore if table doesn't exist yet

            # Create updated_at trigger function
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """))

            # Apply updated_at trigger to tables that have the column
            trigger_tables = [
                'company_users', 'accounts', 'customers', 'suppliers', 'products',
                'invoices', 'journal_entries', 'budgets', 'assets', 'employees',
                'employee_loans', 'leave_requests', 'projects', 'project_tasks',
                'contracts', 'sales_orders', 'purchase_orders', 'warehouses',
                'treasury_accounts', 'tax_rates', 'currencies', 'parties',
                'sales_quotations', 'expenses', 'pos_sessions'
            ]
            for table in trigger_tables:
                try:
                    conn.execute(text(f"""
                        DROP TRIGGER IF EXISTS trigger_update_{table}_updated_at ON {table};
                        CREATE TRIGGER trigger_update_{table}_updated_at
                            BEFORE UPDATE ON {table}
                            FOR EACH ROW
                            EXECUTE FUNCTION update_updated_at_column();
                    """))
                except Exception:
                    pass  # Ignore if table doesn't have updated_at
            
            # Note: with isolation_level="AUTOCOMMIT", we don't need conn.commit()
            # but it doesn't hurt.
        
        logger.info(f"✅ Created all tables for {db_name}")
        return True, "تم إنشاء جميع الجداول بنجاح"

        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        return False, str(e)
    finally:
        company_engine.dispose()


# Country → official currency mapping
COUNTRY_CURRENCY_MAP = {
    "SA": "SAR",
    "SY": "SYP",
    "AE": "AED",
    "EG": "EGP",
    "KW": "KWD",
    "TR": "TRY",
    "JO": "JOD",
    "IQ": "IQD",
    "LB": "LBP",
    "OM": "OMR",
    "BH": "BHD",
    "QA": "QAR",
}

def initialize_company_default_data(company_id: str, admin_username: str, 
                                    admin_email: str, admin_password: str, 
                                    admin_full_name: str, timezone: str = "Asia/Damascus",
                                    currency: str = "SYP", country: str = "SY") -> Tuple[bool, str]:
    """Initialize default data for company"""
    db_name = f"aman_{company_id}"
    connection_url = settings.get_company_database_url(company_id)
    
    try:
        company_engine = create_engine(connection_url)
        hashed_password = hash_password(admin_password)
        
        with company_engine.connect() as conn:
            # Create admin user
            conn.execute(text("""
                INSERT INTO company_users (username, password, email, full_name, role, permissions)
                VALUES (:username, :password, :email, :full_name, 'superuser', :permissions)
            """), {
                "username": admin_username,
                "password": hashed_password,
                "email": admin_email,
                "full_name": admin_full_name,
                "permissions": '{"all": true}'
            })
            
            # Default Roles - comprehensive roles with permissions
            conn.execute(text("""
                INSERT INTO roles (role_name, role_name_ar, description, permissions, is_system_role) VALUES 
                ('superuser', 'مدير النظام', 'صلاحيات كاملة للنظام', '["*"]', true),
                ('admin', 'مدير', 'صلاحيات إدارية كاملة', '["*"]', true),
                ('manager', 'مدير فرع', 'إدارة المبيعات والمشتريات والمخزون', '["sales.*", "buying.*", "inventory.*", "stock.*", "treasury.view", "treasury.create", "reports.view", "hr.view", "products.*", "contracts.*", "pos.*", "manufacturing.view", "assets.view", "expenses.view", "expenses.create", "expenses.approve", "dashboard.view", "projects.view", "projects.create"]', false),
                ('accountant', 'محاسب', 'إدارة المحاسبة والتقارير المالية', '["accounting.*", "reports.financial", "reports.view", "treasury.*", "reconciliation.*", "sales.view", "buying.view", "contracts.view", "currencies.view", "currencies.manage", "taxes.view", "taxes.manage", "expenses.view", "expenses.approve", "dashboard.view"]', false),
                ('sales', 'مبيعات', 'إدارة المبيعات ونقاط البيع', '["sales.*", "products.view", "stock.view", "pos.*", "contracts.view", "dashboard.view"]', false),
                ('inventory', 'أمين مستودع', 'إدارة المخزون والمنتجات', '["inventory.*", "stock.*", "products.*", "manufacturing.view", "buying.view", "dashboard.view"]', false),
                ('cashier', 'كاشير', 'نقطة البيع والمبيعات', '["pos.*", "sales.view", "products.view", "stock.view", "treasury.view", "dashboard.view"]', false),
                ('user', 'مستخدم', 'صلاحيات محدودة', '["dashboard.view"]', false)
                ON CONFLICT (role_name) DO NOTHING
            """))
            
            # Default accounts hierarchical structure
            # (account_number, account_code, name, name_en, account_type, parent_index_in_this_list)
            # Level 1
            root_accounts = [
                ("1", "ASSET", "الأصول", "Assets", "asset", None),
                ("2", "LIAB", "الخصوم", "Liabilities", "liability", None),
                ("3", "EQTY", "حقوق الملكية", "Equity", "equity", None),
                ("4", "REV", "الإيرادات", "Revenue", "revenue", None),
                ("5", "EXP", "المصروفات", "Expenses", "expense", None),
            ]
            
            inserted_ids = {}
            for acc in root_accounts:
                result = conn.execute(text("""
                    INSERT INTO accounts (account_number, account_code, name, name_en, account_type, currency)
                    VALUES (:number, :code, :name, :name_en, :type, :currency) RETURNING id
                """), {"number": acc[0], "code": acc[1], "name": acc[2], "name_en": acc[3], "type": acc[4], "currency": currency})
                inserted_ids[acc[0]] = result.fetchone()[0]

            # Level 2 & 3 - Comprehensive "Global" Chart of Accounts
            sub_accounts = [
                # 1. Assets
                ("11", "C-ASSET", "أصول متداولة", "Current Assets", "asset", "1"),
                ("1101", "CASH", "النقد وما في حكمه", "Cash & Equivalents", "asset", "11"),
                ("110101", "BOX", "الصندوق الرئيسي", "Main Box", "asset", "1101"),
                ("110102", "BNK", "البنك", "Bank", "asset", "1101"),
                ("1102", "AR", "العملاء والذمم المدينة", "Accounts Receivable", "asset", "11"),
                ("1103", "INV", "المخزون", "Inventory", "asset", "11"),
                ("110301", "RM-INV", "مخزون المواد الأولية", "Raw Materials Inventory", "asset", "1103"),
                ("110302", "FG-INV", "مخزون الإنتاج التام", "Finished Goods Inventory", "asset", "1103"),
                ("1110", "WIP", "أعمال تحت التشغيل", "Work In Progress", "asset", "11"),
                ("1111", "INT-CO", "حسابات بين الفروع", "Intercompany Accounts", "asset", "11"),
                ("1104", "ADV", "سلف وقروض الموظفين", "Employee Loans", "asset", "11"),
                ("1105", "PRE", "مصروفات مدفوعة مقدماً", "Prepaid Expenses", "asset", "11"),
                
                ("12", "F-ASSET", "أصول ثابتة", "Fixed Assets", "asset", "1"),
                ("1201", "MAC", "الآلات والمعدات", "Machinery & Equipment", "asset", "12"),
                ("1202", "VEH", "السيارات ووسائل النقل", "Vehicles", "asset", "12"),
                ("1203", "FUR", "الأثاث والمفروشات", "Furniture", "asset", "12"),
                ("1204", "BLD", "المباني والإنشاءات", "Buildings", "asset", "12"),
                ("1205", "LND", "الأراضي", "Lands", "asset", "12"),
                ("1206", "CMP", "أجهزة حاسوب وأنظمة", "Computers & Systems", "asset", "12"),
                ("1207", "ACC-DEP", "الإهلاك المتراكم", "Accumulated Depreciation", "asset", "12"),

                # Prepayments & Special Current Assets
                ("1106", "PRE-SUP", "مدفوعات مقدمة للموردين", "Prepayments to Suppliers", "asset", "11"),
                ("1107", "VAT-IN-AST", "ضريبة المدخلات", "Input VAT (Receivable)", "asset", "11"),
                ("1108", "CHK-RCV", "شيكات تحت التحصيل", "Checks Under Collection", "asset", "11"),
                ("1109", "NR", "أوراق قبض", "Notes Receivable", "asset", "11"),

                # 2. Liabilities
                ("21", "C-LIAB", "خصوم متداولة", "Current Liabilities", "liability", "2"),
                ("2101", "AP", "الموردين والذمم الدائنة", "Accounts Payable", "liability", "21"),
                ("2102", "ACC", "مصاريف مستحقة", "Accrued Expenses", "liability", "21"),
                ("2104", "UNB-PUR", "مشتريات مستلمة غير مفوترة", "Unbilled Received Purchases", "liability", "2102"),
                ("2103", "VAT", "ضريبة القيمة المضافة", "VAT Payable", "liability", "21"),
                ("210301", "VAT-OUT", "ضريبة المخرجات", "Output VAT", "liability", "2103"),
                ("2105", "CHK-PAY", "شيكات تحت الدفع", "Checks Payable", "liability", "21"),
                ("2106", "GOSI-PAY", "التأمينات الاجتماعية المستحقة", "GOSI Payable", "liability", "21"),
                ("2107", "CUST-DEP", "عربون / دفعات مقدمة من العملاء", "Customer Deposits", "liability", "21"),
                ("2110", "NP", "أوراق دفع", "Notes Payable", "liability", "21"),
                
                ("22", "L-LIAB", "خصوم غير متداولة", "Non-Current Liabilities", "liability", "2"),
                ("2201", "L-LOAN", "قروض طويلة الأجل", "Long Term Loans", "liability", "22"),
                ("2202", "EOS", "مخصص نهاية الخدمة", "End of Service Provision", "liability", "22"),

                # 3. Equity
                ("31", "CAP", "رأس المال", "Capital", "equity", "3"),
                ("32", "RET", "الأرباح المبقاة", "Retained Earnings", "equity", "3"),
                ("33", "CUR", "أرباح العام الحالي", "Current Year Earnings", "equity", "3"),
                ("34", "DRW", "الجارى والمسحوبات", "Owner Withdrawals", "equity", "3"),

                # 4. Revenue
                ("41", "SALE", "إيرادات التشغيل", "Operating Revenue", "revenue", "4"),
                ("4101", "SALE-G", "مبيعات البضائع", "Sales of Goods", "revenue", "41"),
                ("4102", "SALE-S", "إيرادات الخدمات", "Service Revenue", "revenue", "41"),
                ("4103", "SALE-R", "مردودات المبيعات", "Sales Returns", "revenue", "41"),
                ("4104", "SALE-DISC", "خصم مبيعات", "Sales Discount", "revenue", "41"),
                ("42", "O-REV", "إيرادات أخرى", "Other Revenue", "revenue", "4"),
                ("4201", "FX-GAIN", "أرباح فروقات عملة (محققة)", "Realized FX Gain", "revenue", "42"),
                ("4202", "UFX-GAIN", "أرباح فروقات عملة (غير محققة)", "Unrealized FX Gain", "revenue", "42"),

                # 5. Expenses
                ("51", "CGS", "تكلفة البضاعة المباعة", "Cost of Goods Sold", "expense", "5"),
                ("5101", "CGS-G", "تكلفة مبيعات البضائع", "COGS - Goods", "expense", "51"),
                ("5102", "CGS-MFG", "تكلفة التصنيع", "Manufacturing Cost", "expense", "51"),
                ("5103", "LABOR", "تكلفة العمالة المباشرة", "Direct Labor Cost", "expense", "51"),
                ("5104", "MFG-OH", "المصاريف الصناعية العامة", "Manufacturing Overhead", "expense", "51"),
                ("52", "OP-EXP", "المصروفات التشغيلية والإدارية", "Operating Expenses", "expense", "5"),
                ("5201", "SAL", "الرواتب والأجور", "Salaries", "expense", "52"),
                ("5202", "RNT", "مصروف الإيجار", "Rent Expense", "expense", "52"),
                ("5203", "UTL", "الكهرباء والمياه", "Utilities", "expense", "52"),
                ("5204", "COM", "الاتصالات والإنترنت", "Communication", "expense", "52"),
                ("5205", "MNT", "الصيانة", "Maintenance", "expense", "52"),
                ("5206", "GOV", "الرسوم الحكومية", "Government Fees", "expense", "52"),
                ("5207", "MKT", "التسويق والإعلان", "Marketing", "expense", "52"),
                ("5208", "TRV", "مصاريف السفر والتنقل", "Travel Expenses", "expense", "52"),
                ("5209", "GEN-EXP", "مصروفات عمومية", "General Expenses", "expense", "52"),
                ("5210", "GOSI-EXP", "مصروف التأمينات الاجتماعية", "GOSI Expense", "expense", "52"),
                ("5211", "INS", "مصروف التأمين", "Insurance Expense", "expense", "52"),
                ("5212", "CLEAN", "مصروف النظافة", "Cleaning Expense", "expense", "52"),
                ("5213", "STATIONERY", "مصروف القرطاسية", "Stationery Expense", "expense", "52"),
                ("5214", "HOSP", "مصروف الضيافة", "Hospitality Expense", "expense", "52"),
                ("53", "DEP", "الإهلاك", "Depreciation", "expense", "5"),
                ("54", "FIN", "المصروفات المالية والبنكية", "Financial Charges", "expense", "5"),
                ("5401", "BANK-F", "الرسوم البنكية", "Bank Fees", "expense", "54"),
                ("5402", "FX-LOSS", "خسائر فروقات عملة (محققة)", "Realized FX Loss", "expense", "54"),
                ("5403", "UFX-LOSS", "خسائر فروقات عملة (غير محققة)", "Unrealized FX Loss", "expense", "54"),
                ("55", "O-EXP", "مصروفات أخرى", "Other Expenses", "expense", "5"),
                ("5501", "AST-LOSS", "خسائر استبعاد الأصول", "Asset Disposal Loss", "expense", "55"),
                ("5502", "CASH-OS", "فروقات صندوق (زيادة/نقصان)", "Cash Over/Short", "expense", "55"),
                ("5503", "INV-ADJ", "فروقات تسوية المخزون", "Inventory Adjustment", "expense", "55"),

                # ── COA-001: Intangible Assets ──
                ("13", "INTANG", "أصول غير ملموسة", "Intangible Assets", "asset", "1"),
                ("1301", "GOODWILL", "شهرة", "Goodwill", "asset", "13"),
                ("1302", "PATENT", "براءات اختراع وعلامات تجارية", "Patents & Trademarks", "asset", "13"),
                ("1303", "COPYR", "حقوق التأليف والنشر", "Copyrights", "asset", "13"),
                ("1304", "ACC-AMORT", "الإطفاء المتراكم", "Accumulated Amortization", "asset", "13"),
                ("1305", "ROU", "أصل حق الاستخدام", "Right of Use Asset", "asset", "13"),

                # ── COA-002: Tax accounts ──
                ("2108", "WHT-PAY", "ضريبة الاستقطاع", "Withholding Tax Payable", "liability", "21"),
                ("2109", "INC-TAX", "ضريبة الدخل المستحقة", "Income Tax Payable", "liability", "21"),
                ("2111", "ZAKAT", "الزكاة المستحقة", "Zakat Payable", "liability", "21"),
                ("2112", "VAT-SETT", "تسوية ضريبة القيمة المضافة", "VAT Settlement", "liability", "21"),

                # ── COA-003/004: Additional Expenses ──
                ("5215", "LEGAL", "مصروفات قانونية", "Legal Expenses", "expense", "52"),
                ("5216", "AUDIT", "مصروف التدقيق والمراجعة", "Audit Fees", "expense", "52"),
                ("5217", "COMM", "عمولات المبيعات", "Sales Commissions", "expense", "52"),
                ("5218", "PR", "علاقات عامة", "Public Relations", "expense", "52"),

                # ── COA-005: Other Revenue ──
                ("4203", "INT-INC", "فوائد محصلة", "Interest Income", "revenue", "42"),
                ("4204", "DIV-INC", "توزيعات أرباح", "Dividend Income", "revenue", "42"),
                ("4205", "AST-GAIN", "ربح بيع أصول", "Gain on Asset Disposal", "revenue", "42"),
                ("4206", "PUR-DISC", "خصومات مكتسبة", "Purchase Discounts", "revenue", "42"),

                # ── COA-006: HR, Provisions, Prepaid sub-accounts ──
                ("5219", "ALLOW", "بدلات الموظفين", "Employee Allowances", "expense", "52"),
                ("5220", "OVT", "العمل الإضافي", "Overtime Expense", "expense", "52"),
                ("5221", "TERM-EXP", "مكافآت نهاية الخدمة (مصروف)", "Termination Benefits Expense", "expense", "52"),
                ("5222", "LV-EXP", "مصروف الإجازات", "Leave Expense", "expense", "52"),
                ("5223", "BD-EXP", "مصروف ديون معدومة", "Bad Debt Expense", "expense", "52"),
                ("2203", "LV-PROV", "مخصص الإجازات", "Leave Provision", "liability", "22"),
                ("2204", "BD-PROV", "مخصص الديون المعدومة", "Allowance for Doubtful Debts", "liability", "22"),
                ("110501", "PRE-RENT", "إيجار مدفوع مقدماً", "Prepaid Rent", "asset", "1105"),
                ("110502", "PRE-INS", "تأمين مدفوع مقدماً", "Prepaid Insurance", "asset", "1105"),

                # ── Equity: Revaluation Reserve (for GL-007) ──
                ("35", "REVAL", "احتياطي إعادة التقييم", "Revaluation Reserve", "equity", "3"),
            ]

            for acc in sub_accounts:
                parent_id = inserted_ids.get(acc[5])
                result = conn.execute(text("""
                    INSERT INTO accounts (account_number, account_code, name, name_en, account_type, parent_id, currency)
                    VALUES (:number, :code, :name, :name_en, :type, :parent_id, :currency) RETURNING id
                """), {"number": acc[0], "code": acc[1], "name": acc[2], "name_en": acc[3], "type": acc[4], "parent_id": parent_id, "currency": currency})
                inserted_ids[acc[0]] = result.fetchone()[0]
            
            # Default settings
            default_currency = currency

            # Default Mappings (GL Account Mapping)
            # We map system roles (keys) to account IDs from the inserted_ids
            # inserted_ids maps account_number (e.g. '1103') to its database ID
            mapping_seeds = [
                # Assets
                ("acc_map_inventory", inserted_ids.get("1103")),  # INV
                ("acc_map_vat_in", inserted_ids.get("1107")),      # VAT-IN (Asset)
                ("acc_map_ar", inserted_ids.get("1102")),         # AR
                ("acc_map_cash_main", inserted_ids.get("110101")), # BOX
                ("acc_map_bank", inserted_ids.get("110102")),      # BNK
                ("acc_map_loans_adv", inserted_ids.get("1104")),   # ADV (Loans)
                ("acc_map_prepaid_exp", inserted_ids.get("1105")), # PRE (Prepaid)
                ("acc_map_prepayment_supplier", inserted_ids.get("1106")), # PRE-SUP
                ("acc_map_checks_receivable", inserted_ids.get("1108")),   # CHK-RCV
                ("acc_map_notes_receivable", inserted_ids.get("1109")),    # NR
                ("acc_map_wip", inserted_ids.get("1110")),           # WIP
                ("acc_map_raw_materials", inserted_ids.get("110301")), # RM-INV
                ("acc_map_finished_goods", inserted_ids.get("110302")),# FG-INV
                ("acc_map_fixed_assets", inserted_ids.get("12")),  # F-ASSET
                ("acc_map_acc_depr", inserted_ids.get("1207")),    # Accumulated Depreciation

                # Liabilities
                ("acc_map_ap", inserted_ids.get("2101")),         # AP
                ("acc_map_vat_out", inserted_ids.get("210301")),   # VAT-OUT
                ("acc_map_accrued_salaries", inserted_ids.get("2102")), # ACC (Accrued)
                ("acc_map_unbilled_purchases", inserted_ids.get("2104")), # UNB-PUR
                ("acc_map_checks_payable", inserted_ids.get("2105")),     # CHK-PAY
                ("acc_map_gosi_payable", inserted_ids.get("2106")),       # GOSI Payable
                ("acc_map_customer_deposits", inserted_ids.get("2107")),  # Customer Deposits
                ("acc_map_notes_payable", inserted_ids.get("2110")),      # NP
                ("acc_map_eos_provision", inserted_ids.get("2202")),      # EOS

                # Revenue
                ("acc_map_sales_rev", inserted_ids.get("4101")),   # SALE-G
                ("acc_map_service_rev", inserted_ids.get("4102")), # SALE-S
                ("acc_map_asset_gain", inserted_ids.get("42")),    # O-REV

                # Cost of Sales / Manufacturing
                ("acc_map_cogs", inserted_ids.get("5101")),          # CGS-G
                ("acc_map_mfg_cogs", inserted_ids.get("5102")),      # CGS-MFG
                ("acc_map_labor_cost", inserted_ids.get("5103")),    # Direct Labor
                ("acc_map_mfg_overhead", inserted_ids.get("5104")),  # Manufacturing Overhead

                # Operating Expenses
                ("acc_map_salaries_exp", inserted_ids.get("5201")),# SAL
                ("acc_map_salaries", inserted_ids.get("5201")),    # Alias for expenses module
                ("acc_map_rent_expense", inserted_ids.get("5202")),     # RNT
                ("acc_map_utilities_expense", inserted_ids.get("5203")), # UTL
                ("acc_map_travel_expense", inserted_ids.get("5208")),    # TRV
                ("acc_map_general_expense", inserted_ids.get("5209")),   # GEN-EXP
                ("acc_map_gosi_expense", inserted_ids.get("5210")),      # GOSI Expense
                ("acc_map_insurance_expense", inserted_ids.get("5211")), # INS

                # Depreciation & Financial
                ("acc_map_depr_exp", inserted_ids.get("53")),      # DEP
                ("acc_map_asset_loss", inserted_ids.get("5501")),  # Asset Disposal Loss
                ("acc_map_cash_over_short", inserted_ids.get("5502")), # POS Cash Over/Short
                ("acc_map_expense_other", inserted_ids.get("55")), # Other Expenses (fallback)

                # Inventory & Intercompany
                ("acc_map_inventory_adjustment", inserted_ids.get("5503")), # Inventory Adjustment
                ("acc_map_intercompany", inserted_ids.get("1111")),         # Intercompany Accounts
                ("acc_map_fx_difference", inserted_ids.get("5402")),        # FX Difference (Realized Loss)

                # ── COA-001: Intangible Assets ──
                ("acc_map_intangible_assets", inserted_ids.get("13")),
                ("acc_map_acc_amortization", inserted_ids.get("1304")),

                # ── COA-002: Tax accounts ──
                ("acc_map_withholding_tax", inserted_ids.get("2108")),
                ("acc_map_income_tax", inserted_ids.get("2109")),
                ("acc_map_zakat", inserted_ids.get("2111")),
                ("acc_map_vat_settlements", inserted_ids.get("2112")),

                # ── COA-005: Other Revenue ──
                ("acc_map_sales_returns", inserted_ids.get("4103")),
                ("acc_map_sales_discount", inserted_ids.get("4104")),
                ("acc_map_interest_income", inserted_ids.get("4203")),
                ("acc_map_asset_disposal_gain", inserted_ids.get("4205")),
                ("acc_map_purchase_discount", inserted_ids.get("4206")),

                # ── COA-003/004: Additional Expenses ──
                ("acc_map_legal_expense", inserted_ids.get("5215")),
                ("acc_map_audit_expense", inserted_ids.get("5216")),
                ("acc_map_sales_commission", inserted_ids.get("5217")),

                # ── COA-006: HR Provisions & Prepaid ──
                ("acc_map_allowances", inserted_ids.get("5219")),
                ("acc_map_overtime", inserted_ids.get("5220")),
                ("acc_map_termination_benefits", inserted_ids.get("5221")),
                ("acc_map_leave_expense", inserted_ids.get("5222")),
                ("acc_map_bad_debt_expense", inserted_ids.get("5223")),
                ("acc_map_provision_holiday", inserted_ids.get("2203")),
                ("acc_map_provision_doubtful", inserted_ids.get("2204")),
                ("acc_map_prepaid_rent", inserted_ids.get("110501")),
                ("acc_map_prepaid_insurance", inserted_ids.get("110502")),
                ("acc_map_accrued_expenses", inserted_ids.get("2102")),

                # ── GL-007: Revaluation Reserve ──
                ("acc_map_revaluation_reserve", inserted_ids.get("35")),
            ]

            curr_names = {
                "SAR": ("ريال سعودي", "Saudi Riyal", "ر.س"),
                "SYP": ("ليرة سورية", "Syrian Pound", "ل.س"),
                "USD": ("دولار أمريكي", "US Dollar", "$"),
                "EUR": ("يورو", "Euro", "€"),
                "GBP": ("جنيه إسترليني", "British Pound", "£"),
                "AED": ("درهم إماراتي", "UAE Dirham", "د.إ"),
                "KWD": ("دينار كويتي", "Kuwaiti Dinar", "د.ك"),
                "EGP": ("جنيه مصري", "Egyptian Pound", "ج.م"),
                "TRY": ("ليرة تركية", "Turkish Lira", "₺"),
            }
            c_name, c_name_en, c_symbol = curr_names.get(currency, (currency, currency, currency))
            
            conn.execute(text("""
                INSERT INTO currencies (code, name, name_en, symbol, is_base, current_rate)
                VALUES (:code, :name, :name_en, :symbol, TRUE, 1.0)
                ON CONFLICT (code) DO UPDATE SET is_base = TRUE
            """), {"code": currency, "name": c_name, "name_en": c_name_en, "symbol": c_symbol})



            settings_data = [
                ("default_currency", default_currency),
                ("company_country", country),
                ("fiscal_year_start", "01-01"),
                ("invoice_prefix", "INV-"),
                ("journal_prefix", "JE-"),
                ("decimal_places", "2"),
                ("date_format", "YYYY-MM-DD"),
                ("timezone", timezone),
            ]
            
            for key, value in settings_data:
                conn.execute(text("""
                    INSERT INTO company_settings (setting_key, setting_value) VALUES (:key, :value)
                """), {"key": key, "value": value})
            
            # Insert Mappings
            for key, val_id in mapping_seeds:
                if val_id:
                    conn.execute(text("""
                        INSERT INTO company_settings (setting_key, setting_value) VALUES (:key, :value)
                        ON CONFLICT (setting_key) DO UPDATE SET setting_value = :value
                    """), {"key": key, "value": str(val_id)})

            # Default branch
            # Map country code to country name and timezone
            country_names = {
                "SA": ("المملكة العربية السعودية", "Saudi Arabia"),
                "SY": ("سوريا", "Syria"),
                "AE": ("الإمارات", "United Arab Emirates"),
                "EG": ("مصر", "Egypt"),
                "KW": ("الكويت", "Kuwait"),
                "TR": ("تركيا", "Turkey"),
            }
            country_ar, country_en = country_names.get(country, (country, country))
            branch_result = conn.execute(text("""
                INSERT INTO branches (branch_code, branch_name, branch_name_en, country, country_code, default_currency, is_default, is_active)
                VALUES ('BR001', 'الفرع الرئيسي', 'Main Branch', :country_name, :country_code, :currency, TRUE, TRUE)
                RETURNING id
            """), {"country_name": country_ar, "country_code": country, "currency": currency}).fetchone()
            branch_id = branch_result[0]

            # Link admin user to branch
            user_id_result = conn.execute(text("SELECT id FROM company_users WHERE username = :u"), {"u": admin_username}).fetchone()
            if user_id_result:
                conn.execute(text("""
                    INSERT INTO user_branches (user_id, branch_id) VALUES (:uid, :bid)
                """), {"uid": user_id_result[0], "bid": branch_id})

            # Default warehouse
            conn.execute(text("""
                INSERT INTO warehouses (warehouse_code, warehouse_name, warehouse_name_en, branch_id, is_default, is_active)
                VALUES ('WH001', 'المستودع الرئيسي', 'Main Warehouse', :bid, TRUE, TRUE)
            """), {"bid": branch_id})

            
            # Default product units
            units = [
                ("PC", "قطعة", "Piece", "pcs"),
                ("KG", "كيلوغرام", "Kilogram", "kg"),
                ("LT", "لتر", "Liter", "lt"),
                ("M", "متر", "Meter", "m"),
                ("BOX", "صندوق", "Box", "box"),
            ]
            for unit in units:
                conn.execute(text("""
                    INSERT INTO product_units (unit_code, unit_name, unit_name_en, abbreviation)
                    VALUES (:code, :name, :name_en, :abbr)
                """), {"code": unit[0], "name": unit[1], "name_en": unit[2], "abbr": unit[3]})
            
            # Default tax rate (VAT 15%)
            conn.execute(text("""
                INSERT INTO tax_rates (tax_code, tax_name, tax_name_en, rate_type, rate_value, is_active)
                VALUES ('VAT15', 'ضريبة القيمة المضافة', 'VAT', 'percentage', 15, TRUE)
            """))

            # ── Tax Compliance: Seed tax_regimes for the company's country ───
            _tax_regimes = {
                "SA": [
                    ("vat", "ضريبة القيمة المضافة", "Value Added Tax (VAT)", 15.00, True, "all", "quarterly"),
                    ("zakat", "الزكاة", "Zakat", 2.50, True, "saudi_owned", "annual"),
                    ("income_tax", "ضريبة الدخل", "Corporate Income Tax", 20.00, True, "foreign_owned", "annual"),
                    ("withholding", "ضريبة الاستقطاع", "Withholding Tax", 5.00, False, "cross_border", "monthly"),
                ],
                "SY": [
                    ("income_tax", "ضريبة الدخل", "Income Tax", 22.00, True, "all", "annual"),
                    ("salary_tax", "ضريبة الرواتب والأجور", "Salary Tax", 0.00, True, "all", "monthly"),
                    ("stamp_duty", "رسوم الطوابع", "Stamp Duty", 0.60, False, "contracts", "per_transaction"),
                ],
                "AE": [
                    ("vat", "ضريبة القيمة المضافة", "Value Added Tax (VAT)", 5.00, True, "all", "quarterly"),
                    ("corporate_tax", "ضريبة الشركات", "Corporate Tax", 9.00, True, "all", "annual"),
                ],
                "EG": [
                    ("vat", "ضريبة القيمة المضافة", "Value Added Tax (VAT)", 14.00, True, "all", "monthly"),
                    ("income_tax", "ضريبة الدخل", "Corporate Income Tax", 22.50, True, "all", "annual"),
                ],
                "JO": [
                    ("sales_tax", "ضريبة المبيعات", "General Sales Tax", 16.00, True, "all", "monthly"),
                    ("income_tax", "ضريبة الدخل", "Corporate Income Tax", 20.00, True, "all", "annual"),
                ],
                "KW": [
                    ("income_tax", "ضريبة الدخل", "Corporate Income Tax", 15.00, True, "foreign_owned", "annual"),
                    ("zakat", "الزكاة", "Zakat (NLST)", 1.00, True, "all", "annual"),
                ],
            }
            country_regimes = _tax_regimes.get(country, _tax_regimes.get("SA", []))
            for reg in country_regimes:
                conn.execute(text("""
                    INSERT INTO tax_regimes (country_code, tax_type, name_ar, name_en, default_rate, is_required, applies_to, filing_frequency)
                    VALUES (:cc, :type, :ar, :en, :rate, :req, :applies, :freq)
                    ON CONFLICT (country_code, tax_type) DO NOTHING
                """), {"cc": country, "type": reg[0], "ar": reg[1], "en": reg[2], "rate": reg[3], "req": reg[4], "applies": reg[5], "freq": reg[6]})

            # Company tax settings for the main country
            conn.execute(text("""
                INSERT INTO company_tax_settings (country_code) VALUES (:cc)
                ON CONFLICT (country_code) DO NOTHING
            """), {"cc": country})

            # Default Costing Policy
            conn.execute(text("""
                INSERT INTO costing_policies (policy_name, policy_type, description, is_active, created_by)
                VALUES ('Default Global WAC', 'global_wac', 'Standard unified cost across all branches', TRUE, 1)
            """))
            
            conn.commit()

        # DB-015: Populate central user index for fast login lookup
        try:
            system_url = settings.DATABASE_URL
            system_engine = create_engine(system_url)
            with system_engine.connect() as sys_conn:
                sys_conn.execute(text("""
                    INSERT INTO system_user_index (username, company_id, is_active)
                    VALUES (:username, :company_id, true)
                    ON CONFLICT (username, company_id) DO UPDATE SET is_active = true, updated_at = CURRENT_TIMESTAMP
                """), {"username": admin_username, "company_id": company_id})
                sys_conn.commit()
            system_engine.dispose()
        except Exception as idx_err:
            logger.warning(f"⚠️ Could not populate user index: {idx_err}")

        logger.info(f"✅ Initialized default data for {db_name}")
        return True, "تم تهيئة البيانات الافتراضية"
        
    except Exception as e:
        logger.error(f"❌ Error initializing data: {str(e)}")
        return False, str(e)
    finally:
        company_engine.dispose()

def get_pos_tables_sql() -> str:
    """Returns SQL for POS module tables"""
    return """
    -- ===== POS TABLES =====
    CREATE TABLE IF NOT EXISTS pos_sessions (
        id SERIAL PRIMARY KEY,
        session_code VARCHAR(50) UNIQUE,
        pos_profile_id INTEGER, 
        user_id INTEGER REFERENCES company_users(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        opening_balance DECIMAL(18, 4) DEFAULT 0,
        closing_balance DECIMAL(18, 4) DEFAULT 0,
        total_sales DECIMAL(18, 4) DEFAULT 0,
        total_returns DECIMAL(18, 4) DEFAULT 0,
        cash_register_balance DECIMAL(18, 4) DEFAULT 0,
        difference DECIMAL(18, 4) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'opened', 
        opened_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        closed_at TIMESTAMPTZ,
        notes TEXT,
        branch_id INTEGER REFERENCES branches(id),
        treasury_account_id INTEGER REFERENCES treasury_accounts(id)
    );

    CREATE TABLE IF NOT EXISTS pos_orders (
        id SERIAL PRIMARY KEY,
        order_number VARCHAR(50) UNIQUE NOT NULL,
        session_id INTEGER REFERENCES pos_sessions(id),
        customer_id INTEGER REFERENCES customers(id),
        walk_in_customer_name VARCHAR(255),
        branch_id INTEGER REFERENCES branches(id),
        warehouse_id INTEGER REFERENCES warehouses(id),
        order_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) DEFAULT 'draft', 
        
        -- Money Fields
        subtotal DECIMAL(18, 4) DEFAULT 0,
        discount_type VARCHAR(20) DEFAULT 'amount',
        discount_amount DECIMAL(18, 4) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        total_amount DECIMAL(18, 4) DEFAULT 0,
        paid_amount DECIMAL(18, 4) DEFAULT 0,
        change_amount DECIMAL(18, 4) DEFAULT 0,
        
        note TEXT,
        created_by INTEGER REFERENCES company_users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pos_order_lines (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES pos_orders(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id),
        description VARCHAR(255),
        quantity DECIMAL(18, 4) NOT NULL DEFAULT 1,
        original_price DECIMAL(18, 4) NOT NULL,
        unit_price DECIMAL(18, 4) NOT NULL, 
        tax_rate DECIMAL(5, 2) DEFAULT 0,
        tax_amount DECIMAL(18, 4) DEFAULT 0,
        discount_percentage DECIMAL(5, 2) DEFAULT 0,
        discount_amount DECIMAL(18, 4) DEFAULT 0,
        subtotal DECIMAL(18, 4) NOT NULL, 
        total DECIMAL(18, 4) NOT NULL,    
        
        warehouse_id INTEGER REFERENCES warehouses(id),
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS pos_payments (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES pos_orders(id) ON DELETE CASCADE,
        session_id INTEGER REFERENCES pos_sessions(id),
        payment_method VARCHAR(50) NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        reference_number VARCHAR(100),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- POS Order Payments (per-order payment method breakdown)
    CREATE TABLE IF NOT EXISTS pos_order_payments (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES pos_orders(id) ON DELETE CASCADE,
        method VARCHAR(50) NOT NULL,
        amount DECIMAL(18, 4) NOT NULL,
        reference VARCHAR(100),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- POS Returns
    CREATE TABLE IF NOT EXISTS pos_returns (
        id SERIAL PRIMARY KEY,
        original_order_id INTEGER REFERENCES pos_orders(id),
        user_id INTEGER REFERENCES company_users(id),
        session_id INTEGER REFERENCES pos_sessions(id),
        refund_amount DECIMAL(18, 4) NOT NULL DEFAULT 0,
        refund_method VARCHAR(50) DEFAULT 'cash',
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS pos_return_items (
        id SERIAL PRIMARY KEY,
        return_id INTEGER REFERENCES pos_returns(id) ON DELETE CASCADE,
        original_item_id INTEGER,
        quantity DECIMAL(18, 4) NOT NULL DEFAULT 1,
        reason TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- POS Promotions
    CREATE TABLE IF NOT EXISTS pos_promotions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        promotion_type VARCHAR(50) NOT NULL DEFAULT 'percentage',
        value NUMERIC(15, 2) NOT NULL DEFAULT 0,
        buy_qty INTEGER,
        get_qty INTEGER,
        coupon_code VARCHAR(100),
        applicable_products TEXT,
        applicable_categories TEXT,
        min_order_amount NUMERIC(15, 2) DEFAULT 0,
        start_date TIMESTAMPTZ,
        end_date TIMESTAMPTZ,
        is_active BOOLEAN DEFAULT TRUE,
        branch_id INTEGER,
        created_by INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- POS Loyalty Programs
    CREATE TABLE IF NOT EXISTS pos_loyalty_programs (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        points_per_unit NUMERIC(10, 4) DEFAULT 1,
        currency_per_point NUMERIC(10, 4) DEFAULT 0.01,
        min_points_redeem INTEGER DEFAULT 100,
        tier_rules JSONB DEFAULT '[]'::jsonb,
        is_active BOOLEAN DEFAULT TRUE,
        branch_id INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS pos_loyalty_points (
        id SERIAL PRIMARY KEY,
        program_id INTEGER REFERENCES pos_loyalty_programs(id),
        party_id INTEGER,
        points_earned NUMERIC(12, 2) DEFAULT 0,
        points_redeemed NUMERIC(12, 2) DEFAULT 0,
        balance NUMERIC(12, 2) DEFAULT 0,
        tier VARCHAR(50) DEFAULT 'standard',
        last_activity_at TIMESTAMPTZ DEFAULT NOW(),
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS pos_loyalty_transactions (
        id SERIAL PRIMARY KEY,
        loyalty_id INTEGER REFERENCES pos_loyalty_points(id),
        order_id INTEGER,
        txn_type VARCHAR(20) NOT NULL,
        points NUMERIC(12, 2) NOT NULL,
        description TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- POS Tables (Restaurant/Dine-in)
    CREATE TABLE IF NOT EXISTS pos_tables (
        id SERIAL PRIMARY KEY,
        table_number VARCHAR(50) NOT NULL,
        table_name VARCHAR(100),
        floor VARCHAR(50) DEFAULT 'main',
        capacity INTEGER DEFAULT 4,
        status VARCHAR(20) DEFAULT 'available',
        shape VARCHAR(20) DEFAULT 'square',
        pos_x NUMERIC(8, 2) DEFAULT 0,
        pos_y NUMERIC(8, 2) DEFAULT 0,
        branch_id INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS pos_table_orders (
        id SERIAL PRIMARY KEY,
        table_id INTEGER REFERENCES pos_tables(id),
        order_id INTEGER,
        seated_at TIMESTAMPTZ DEFAULT NOW(),
        cleared_at TIMESTAMPTZ,
        guests INTEGER DEFAULT 1,
        waiter_id INTEGER,
        status VARCHAR(20) DEFAULT 'seated'
    );

    -- POS Kitchen Display
    CREATE TABLE IF NOT EXISTS pos_kitchen_orders (
        id SERIAL PRIMARY KEY,
        order_id INTEGER,
        order_line_id INTEGER,
        product_id INTEGER,
        product_name VARCHAR(255),
        quantity NUMERIC(12, 3),
        notes TEXT,
        station VARCHAR(100) DEFAULT 'main',
        status VARCHAR(30) DEFAULT 'pending',
        priority INTEGER DEFAULT 0,
        sent_at TIMESTAMPTZ DEFAULT NOW(),
        accepted_at TIMESTAMPTZ,
        ready_at TIMESTAMPTZ,
        served_at TIMESTAMPTZ,
        branch_id INTEGER
    );

    CREATE INDEX IF NOT EXISTS idx_pos_returns_session ON pos_returns(session_id);
    CREATE INDEX IF NOT EXISTS idx_pos_returns_order ON pos_returns(original_order_id);
    CREATE INDEX IF NOT EXISTS idx_pos_order_payments_order ON pos_order_payments(order_id);
    CREATE INDEX IF NOT EXISTS idx_pos_promotions_active ON pos_promotions(is_active);
    CREATE INDEX IF NOT EXISTS idx_pos_kitchen_status ON pos_kitchen_orders(status);
    """


def get_approval_tables_sql() -> str:
    """Returns SQL for Approval Workflow tables (Phase 7)"""
    return """
    -- ===== APPROVAL WORKFLOWS (Phase 7) =====

    CREATE TABLE IF NOT EXISTS approval_workflows (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        document_type VARCHAR(50) NOT NULL,
        description TEXT,
        conditions JSONB DEFAULT '{}',
        steps JSONB DEFAULT '[]',
        is_active BOOLEAN DEFAULT TRUE,
        created_by INTEGER,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS approval_requests (
        id SERIAL PRIMARY KEY,
        workflow_id INTEGER REFERENCES approval_workflows(id),
        document_type VARCHAR(50) NOT NULL,
        document_id INTEGER NOT NULL,
        amount DECIMAL(18, 4) DEFAULT 0,
        description TEXT,
        current_step INTEGER DEFAULT 1,
        total_steps INTEGER DEFAULT 1,
        status VARCHAR(20) DEFAULT 'pending',
        requested_by INTEGER,
        completed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS approval_actions (
        id SERIAL PRIMARY KEY,
        request_id INTEGER REFERENCES approval_requests(id) ON DELETE CASCADE,
        step INTEGER NOT NULL,
        action VARCHAR(20) NOT NULL,
        actioned_by INTEGER,
        notes TEXT,
        actioned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status);
    CREATE INDEX IF NOT EXISTS idx_approval_requests_doc ON approval_requests(document_type, document_id);
    CREATE INDEX IF NOT EXISTS idx_approval_actions_request ON approval_actions(request_id);
    """


def get_security_tables_sql() -> str:
    """Returns SQL for Security tables (2FA, Password Policy, Sessions) - Phase 7"""
    return """
    -- ===== SECURITY TABLES (Phase 7) =====

    CREATE TABLE IF NOT EXISTS user_2fa_settings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER UNIQUE NOT NULL,
        secret_key VARCHAR(100),
        is_enabled BOOLEAN DEFAULT FALSE,
        backup_codes TEXT,
        verified_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS password_history (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS user_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        token_hash VARCHAR(255),
        ip_address VARCHAR(50),
        user_agent TEXT,
        login_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        last_activity TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );

    CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id, is_active);
    CREATE INDEX IF NOT EXISTS idx_password_history_user ON password_history(user_id);

    -- ===== PHASE 9: External API + CRM + ZATCA + WHT =====

    ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_hash TEXT;
    ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_signature TEXT;
    ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_qr TEXT;
    ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_status VARCHAR(20) DEFAULT 'pending';
    ALTER TABLE invoices ADD COLUMN IF NOT EXISTS zatca_submission_id TEXT;

    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        key_hash VARCHAR(255) NOT NULL UNIQUE,
        key_prefix VARCHAR(10) NOT NULL,
        permissions JSONB DEFAULT '[]',
        rate_limit_per_minute INT DEFAULT 60,
        is_active BOOLEAN DEFAULT TRUE,
        created_by INT,
        expires_at TIMESTAMPTZ,
        last_used_at TIMESTAMPTZ,
        usage_count INT DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        notes TEXT
    );

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
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS webhook_logs (
        id SERIAL PRIMARY KEY,
        webhook_id INT REFERENCES webhooks(id) ON DELETE CASCADE,
        event VARCHAR(100),
        payload JSONB,
        response_status INT,
        response_body TEXT,
        success BOOLEAN DEFAULT FALSE,
        attempt INT DEFAULT 1,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS wht_rates (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        name_ar VARCHAR(100),
        rate DECIMAL(5,2) NOT NULL,
        category VARCHAR(50) DEFAULT 'general',
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    INSERT INTO wht_rates (name, name_ar, rate, category) 
    SELECT * FROM (VALUES
        ('Services - Resident', 'خدمات - مقيم', 5.00, 'services'),
        ('Services - Non-Resident', 'خدمات - غير مقيم', 15.00, 'services'),
        ('Rent', 'إيجار', 5.00, 'rent'),
        ('Consulting', 'استشارات', 5.00, 'consulting'),
        ('Royalties', 'حقوق الملكية', 15.00, 'royalties'),
        ('Insurance', 'تأمين', 5.00, 'insurance'),
        ('International Transport', 'نقل دولي', 5.00, 'transport'),
        ('Dividend', 'أرباح الأسهم', 5.00, 'dividend')
    ) AS v(name, name_ar, rate, category)
    WHERE NOT EXISTS (SELECT 1 FROM wht_rates LIMIT 1);

    CREATE TABLE IF NOT EXISTS wht_transactions (
        id SERIAL PRIMARY KEY,
        invoice_id INT,
        payment_id INT,
        supplier_id INT,
        wht_rate_id INT REFERENCES wht_rates(id),
        gross_amount DECIMAL(18,2) NOT NULL,
        wht_rate DECIMAL(5,2) NOT NULL,
        wht_amount DECIMAL(18,2) NOT NULL,
        net_amount DECIMAL(18,2) NOT NULL,
        certificate_number VARCHAR(50),
        status VARCHAR(20) DEFAULT 'pending',
        created_by INT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS sales_opportunities (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        customer_id INT REFERENCES parties(id),
        contact_name VARCHAR(100),
        contact_email VARCHAR(100),
        contact_phone VARCHAR(30),
        stage VARCHAR(30) DEFAULT 'lead',
        probability INT DEFAULT 10,
        expected_value DECIMAL(18,2) DEFAULT 0,
        expected_close_date DATE,
        currency VARCHAR(10) DEFAULT 'SAR',
        source VARCHAR(50),
        assigned_to INT,
        branch_id INT,
        notes TEXT,
        lost_reason TEXT,
        won_quotation_id INT,
        created_by INT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS opportunity_activities (
        id SERIAL PRIMARY KEY,
        opportunity_id INT REFERENCES sales_opportunities(id) ON DELETE CASCADE,
        activity_type VARCHAR(30),
        title VARCHAR(200),
        description TEXT,
        due_date DATE,
        completed BOOLEAN DEFAULT FALSE,
        created_by INT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS support_tickets (
        id SERIAL PRIMARY KEY,
        ticket_number VARCHAR(30) UNIQUE,
        subject VARCHAR(200) NOT NULL,
        description TEXT,
        customer_id INT REFERENCES parties(id),
        contact_name VARCHAR(100),
        contact_email VARCHAR(100),
        contact_phone VARCHAR(30),
        status VARCHAR(20) DEFAULT 'open',
        priority VARCHAR(20) DEFAULT 'medium',
        category VARCHAR(50),
        assigned_to INT,
        branch_id INT,
        sla_hours INT DEFAULT 24,
        resolution TEXT,
        resolved_at TIMESTAMPTZ,
        closed_at TIMESTAMPTZ,
        created_by INT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS ticket_comments (
        id SERIAL PRIMARY KEY,
        ticket_id INT REFERENCES support_tickets(id) ON DELETE CASCADE,
        comment TEXT NOT NULL,
        is_internal BOOLEAN DEFAULT FALSE,
        attachment_url TEXT,
        created_by INT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS tax_calendar (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        tax_type VARCHAR(50),
        due_date DATE NOT NULL,
        reminder_days JSONB DEFAULT '[7, 3, 1]',
        is_recurring BOOLEAN DEFAULT FALSE,
        recurrence_months INT DEFAULT 3,
        is_completed BOOLEAN DEFAULT FALSE,
        notes TEXT,
        created_by INT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_sales_opp_stage ON sales_opportunities(stage);
    CREATE INDEX IF NOT EXISTS idx_sales_opp_customer ON sales_opportunities(customer_id);
    CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status, priority);
    CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON support_tickets(assigned_to);
    """


def get_performance_indexes_sql() -> str:
    """Returns SQL for performance optimization indexes (Phase 7.5)"""
    return """
    -- ===== PERFORMANCE INDEXES (Phase 7.5) =====

    -- Journal Entries - heavily queried for reports
    CREATE INDEX IF NOT EXISTS idx_je_date_status ON journal_entries(entry_date, status);
    CREATE INDEX IF NOT EXISTS idx_je_source ON journal_entries(source);
    CREATE INDEX IF NOT EXISTS idx_je_created_by ON journal_entries(created_by);

    -- Journal Lines - joins and aggregations
    CREATE INDEX IF NOT EXISTS idx_jl_account ON journal_lines(account_id);
    CREATE INDEX IF NOT EXISTS idx_jl_je_account ON journal_lines(journal_entry_id, account_id);

    -- Invoices - filtering by date / status / party
    CREATE INDEX IF NOT EXISTS idx_inv_date_status ON invoices(invoice_date, status);
    CREATE INDEX IF NOT EXISTS idx_inv_party ON invoices(party_id);
    CREATE INDEX IF NOT EXISTS idx_inv_type_status ON invoices(invoice_type, status);

    -- Products - SKU and barcode lookups
    CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
    CREATE INDEX IF NOT EXISTS idx_products_code ON products(product_code);
    CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);


    -- Audit Log - most recent activity
    CREATE INDEX IF NOT EXISTS idx_audit_user_date ON audit_logs(user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);

    -- Parties - name search
    CREATE INDEX IF NOT EXISTS idx_parties_name ON parties(name);
    CREATE INDEX IF NOT EXISTS idx_parties_type ON parties(party_type);

    -- Employees
    CREATE INDEX IF NOT EXISTS idx_emp_code ON employees(employee_code);
    CREATE INDEX IF NOT EXISTS idx_emp_dept ON employees(department_id);

    -- Checks
    CREATE INDEX IF NOT EXISTS idx_checks_recv_status ON checks_receivable(status);
    CREATE INDEX IF NOT EXISTS idx_checks_recv_due ON checks_receivable(due_date);
    CREATE INDEX IF NOT EXISTS idx_checks_pay_status ON checks_payable(status);
    CREATE INDEX IF NOT EXISTS idx_checks_pay_due ON checks_payable(due_date);

    -- Notifications
    CREATE INDEX IF NOT EXISTS idx_notif_user_read ON notifications(user_id, is_read);
    """
