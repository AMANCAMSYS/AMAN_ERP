import sys
sys.path.append("/home/omar/Desktop/aman/backend")
from database import _get_engine
from sqlalchemy import text

company_id = "eaed4032"
engine = _get_engine(company_id)
with engine.connect() as db:
    try:
        rows = db.execute(text("""
            SELECT id, user_id, title, message, body, link, is_read,
                   type, channel, event_type, feature_source,
                   reference_type, reference_id, status, sent_at,
                   read_at, created_at
            FROM notifications
            LIMIT 1
        """)).fetchall()
        print("notifications query OK")
    except Exception as e:
        print("notifications query error:", str(e).split('\n')[0])
