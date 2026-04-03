import sys
sys.path.append("/home/omar/Desktop/aman/backend")
from database import _get_engine
from sqlalchemy import text

company_id = "eaed4032"
engine = _get_engine(company_id)
with engine.connect() as db:
    try:
        rows = db.execute(text("""
            SELECT id, user_id, event_type, email_enabled, in_app_enabled, push_enabled
            FROM notification_preferences WHERE user_id = 1
        """)).fetchall()
        print("notification_preferences query OK")
    except Exception as e:
        print("notification_preferences query error:", str(e).split('\n')[0])
