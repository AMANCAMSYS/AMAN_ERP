from datetime import datetime, timezone
from sqlalchemy import text
from fastapi import Request, HTTPException
from database import engine
import json
import logging

logger = logging.getLogger(__name__)

def log_activity(
    db_conn,
    user_id: int,
    username: str,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    request: Request = None,
    branch_id: int = None,
    critical: bool = False,
):
    """
    سجل نشاط المستخدم في قاعدة البيانات.
    يسجل: من، ماذا، أين، متى، وتفاصيل إضافية.

    Args:
        critical: TASK-021 — When True, a failure to persist the audit row
            raises HTTPException(503) so the caller's transaction is rolled
            back. Use this for operations where losing the audit trail is
            unacceptable (e.g., financial posts, role grants, user admin).
            When False (default), failures are only logged.
    """
    try:
        ip_address = None
        if request:
            ip_address = request.client.host
        
        # Branch Fallback Logic
        if branch_id is None:
            try:
                # 1. Try to get user's first assigned branch
                branch_id = db_conn.execute(
                    text("SELECT branch_id FROM user_branches WHERE user_id = :uid LIMIT 1"), 
                    {"uid": user_id}
                ).scalar()
                
                # 2. If user has no branches, fallback to company default branch
                if branch_id is None:
                    branch_id = db_conn.execute(
                        text("SELECT id FROM branches WHERE is_default = TRUE LIMIT 1")
                    ).scalar()
            except Exception as e:
                logger.warning(f"Could not determine branch for audit log: {e}")

        # Ensure details is JSON serializable
        details_json = json.dumps(details, default=str) if details else '{}'

        db_conn.execute(
            text("""
                INSERT INTO audit_logs 
                (user_id, username, action, resource_type, resource_id, details, ip_address, branch_id, created_at)
                VALUES 
                (:uid, :uname, :act, :res_type, :res_id, :det, :ip, :bid, :now)
            """),
            {
                "uid": user_id,
                "uname": username,
                "act": action,
                "res_type": resource_type,
                "res_id": str(resource_id) if resource_id else None,
                "det": details_json,
                "ip": ip_address,
                "bid": branch_id,
                "now": datetime.now(timezone.utc)
            }
        )
        db_conn.commit()
        logger.info(f"📝 AUDIT: {username} -> {action} ({resource_id})")

    except Exception as e:
        # ACC-F6: never swallow silently — emit full stack for observability
        logger.error(
            f"❌ FAILED TO LOG AUDIT: user={username} action={action} resource={resource_type}:{resource_id} err={e}",
            exc_info=True,
        )
        if critical:
            # TASK-021: fail-closed — reject the operation so the caller
            # rolls back. The audit trail is a non-negotiable prerequisite
            # for critical actions.
            try:
                db_conn.rollback()
            except Exception:
                pass
            raise HTTPException(
                status_code=503,
                detail="تعذّر تسجيل الحدث في سجل التدقيق؛ تم إلغاء العملية للحفاظ على النزاهة.",
            )


def log_system_activity(
    action: str,
    company_id: str = None,
    performed_by: str = None,
    description: str = None,
    request: Request = None
):
    """سجل نشاط على مستوى النظام (في قاعدة البيانات الرئيسية)"""
    try:
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host
            user_agent = request.headers.get("user-agent")
            
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO system_activity_log 
                    (company_id, action_type, action_description, performed_by, ip_address, user_agent, created_at)
                    VALUES 
                    (:cid, :act, :desc, :by, :ip, :ua, CURRENT_TIMESTAMP)
                """),
                {
                    "cid": company_id,
                    "act": action,
                    "desc": description,
                    "by": performed_by,
                    "ip": ip_address,
                    "ua": user_agent
                }
            )
            conn.commit()
    except Exception as e:
        logger.error(f"❌ FAILED TO LOG SYSTEM ACTIVITY: {e}")
