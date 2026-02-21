"""
Phase 8.8 — Permission Tables Migration
PERM-001: Field-Level Permissions tables
PERM-002: Warehouse-Level Permissions tables
PERM-003: Cost-Center-Level Permissions tables
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, create_engine
from config import settings


def get_company_ids():
    root_url = settings.get_company_database_url("postgres").replace("/aman_postgres", "/postgres")
    engine = create_engine(root_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT datname FROM pg_database WHERE datname LIKE 'aman_%' AND datistemplate = false"
        ))
        ids = [row[0].replace("aman_", "") for row in result]
    engine.dispose()
    return ids


def col_exists(conn, table, column):
    r = conn.execute(text("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = :t AND column_name = :c
    """), {"t": table, "c": column}).fetchone()
    return r is not None


def table_exists(conn, table):
    r = conn.execute(text("""
        SELECT 1 FROM information_schema.tables WHERE table_name = :t
    """), {"t": table}).fetchone()
    return r is not None


def migrate_company(company_id):
    db_url = settings.get_company_database_url(company_id)
    engine = create_engine(db_url)
    conn = engine.connect()
    trans = conn.begin()
    changes = []

    try:
        # PERM-001: Field-Level Permissions
        if not table_exists(conn, "user_field_permissions"):
            conn.execute(text("""
                CREATE TABLE user_field_permissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES company_users(id) ON DELETE CASCADE,
                    field_restrictions JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            """))
            changes.append("Created user_field_permissions")

        if not table_exists(conn, "role_field_permissions"):
            conn.execute(text("""
                CREATE TABLE role_field_permissions (
                    id SERIAL PRIMARY KEY,
                    role_name VARCHAR(100) NOT NULL UNIQUE,
                    field_restrictions JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            changes.append("Created role_field_permissions")

        # PERM-002: Warehouse-Level Permissions
        if not table_exists(conn, "user_warehouses"):
            conn.execute(text("""
                CREATE TABLE user_warehouses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES company_users(id) ON DELETE CASCADE,
                    warehouse_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, warehouse_id)
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_warehouses_user ON user_warehouses(user_id)
            """))
            changes.append("Created user_warehouses")

        # PERM-003: Cost-Center-Level Permissions
        if not table_exists(conn, "user_cost_centers"):
            conn.execute(text("""
                CREATE TABLE user_cost_centers (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES company_users(id) ON DELETE CASCADE,
                    cost_center_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, cost_center_id)
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_cost_centers_user ON user_cost_centers(user_id)
            """))
            changes.append("Created user_cost_centers")

        # DASH-001: Dashboard Layouts table
        if not table_exists(conn, "dashboard_layouts"):
            conn.execute(text("""
                CREATE TABLE dashboard_layouts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES company_users(id) ON DELETE CASCADE,
                    layout_name VARCHAR(100) NOT NULL DEFAULT 'default',
                    is_active BOOLEAN DEFAULT TRUE,
                    widgets JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, layout_name)
                )
            """))
            changes.append("Created dashboard_layouts")

        trans.commit()
        print(f"  [{company_id}] OK — {len(changes)} changes: {'; '.join(changes) if changes else 'already up to date'}")

    except Exception as e:
        trans.rollback()
        print(f"  [{company_id}] ERROR: {e}")
    finally:
        conn.close()
        engine.dispose()


if __name__ == "__main__":
    companies = get_company_ids()
    print(f"=== Phase 8.8 Permissions + Dashboard Migration — {len(companies)} companies ===")
    for cid in companies:
        migrate_company(cid)
    print("=== Done ===")
