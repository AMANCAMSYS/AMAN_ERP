import sys
sys.path.append("/home/omar/Desktop/aman/backend")
from database import get_system_db, _get_engine
from sqlalchemy import text

db = next(get_system_db())
companies = db.execute(text("SELECT id FROM system_companies WHERE status = 'active'")).fetchall()
for (c_id,) in companies:
    company_engine = _get_engine(c_id)
    with company_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES company_users(id) ON DELETE CASCADE,
                event_type VARCHAR(50) NOT NULL,
                email_enabled BOOLEAN DEFAULT TRUE,
                in_app_enabled BOOLEAN DEFAULT TRUE,
                push_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, event_type)
            );
        """))
        conn.commit()
    print(f"Fixed {c_id}")
