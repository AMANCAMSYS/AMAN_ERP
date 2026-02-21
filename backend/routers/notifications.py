
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
import logging

logger = logging.getLogger("aman.notifications")

router = APIRouter(prefix="/notifications", tags=["الإشعارات"])

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: Optional[str]
    link: Optional[str]
    is_read: bool
    type: str
    created_at: datetime

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    type: str = "info"
    send_email: bool = False
    send_sms: bool = False


# ===================== User Notifications =====================

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """جلب إشعارات المستخدم الحالي"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return []

    db = get_db_connection(company_id)
    try:
        result = db.execute(text("""
            SELECT * FROM notifications 
            WHERE user_id = :uid 
            ORDER BY created_at DESC 
            LIMIT :limit
        """), {"uid": current_user.id, "limit": limit}).fetchall()
        return [dict(r._mapping) for r in result]
    finally:
        db.close()

@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """عدد الإشعارات غير المقروءة"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"count": 0}

    db = get_db_connection(company_id)
    try:
        count = db.execute(text("""
            SELECT COUNT(*) FROM notifications 
            WHERE user_id = :uid AND is_read = FALSE
        """), {"uid": current_user.id}).scalar()
        return {"count": count}
    finally:
        db.close()

@router.put("/{notification_id}/read")
async def mark_read(notification_id: int, current_user: dict = Depends(get_current_user)):
    """تحديد إشعار كمقروء"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"success": False}

    db = get_db_connection(company_id)
    try:
        db.execute(text("""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE id = :id AND user_id = :uid
        """), {"id": notification_id, "uid": current_user.id})
        db.commit()
        return {"success": True}
    finally:
        db.close()

@router.post("/mark-all-read")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """تحديد الكل كمقروء"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"success": False}

    db = get_db_connection(company_id)
    try:
        db.execute(text("""
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE user_id = :uid AND is_read = FALSE
        """), {"uid": current_user.id})
        db.commit()
        return {"success": True}
    finally:
        db.close()


# ===================== Create Notification with Email/SMS =====================

@router.post("/send")
async def create_and_send_notification(
    data: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    إنشاء إشعار مع إرسال اختياري عبر البريد الإلكتروني و SMS
    """
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(400, "لا يمكن إرسال إشعارات بدون شركة")

    db = get_db_connection(company_id)
    try:
        # 1. Create in-app notification
        db.execute(text("""
            INSERT INTO notifications (user_id, title, message, link, is_read, type, created_at)
            VALUES (:uid, :title, :msg, :link, FALSE, :type, CURRENT_TIMESTAMP)
        """), {
            "uid": data.user_id,
            "title": data.title,
            "msg": data.message,
            "link": data.link,
            "type": data.type
        })

        results = {"in_app": True, "email": None, "sms": None}

        # 2. Send email if requested
        if data.send_email:
            try:
                from services.email_service import send_notification_email, get_base_template
                html = get_base_template(f"""
                    <h2>{data.title}</h2>
                    <p>{data.message or ''}</p>
                    {"<a href='" + data.link + "' class='btn'>عرض التفاصيل</a>" if data.link else ""}
                """)
                results["email"] = send_notification_email(db, data.user_id, data.title, html)
            except Exception as e:
                logger.error(f"Email notification failed: {str(e)}")
                results["email"] = False

        # 3. Send SMS if requested
        if data.send_sms:
            try:
                from services.email_service import send_notification_sms
                sms_text = f"{data.title}: {data.message or ''}"[:160]
                results["sms"] = send_notification_sms(db, data.user_id, sms_text)
            except Exception as e:
                logger.error(f"SMS notification failed: {str(e)}")
                results["sms"] = False

        db.commit()
        return {"message": "تم إرسال الإشعار", "results": results}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ===================== Notification Settings (SMTP / SMS) =====================

@router.get("/settings", dependencies=[Depends(require_permission("settings.view"))])
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    """إعدادات البريد الإلكتروني و SMS"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {}

    db = get_db_connection(company_id)
    try:
        keys = [
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_from_email',
            'smtp_from_name', 'smtp_tls',
            'sms_api_url', 'sms_sender_name',
            'notification_email_enabled', 'notification_sms_enabled'
        ]
        # Don't return passwords
        rows = db.execute(text("""
            SELECT setting_key, setting_value FROM company_settings
            WHERE setting_key = ANY(:keys)
        """), {"keys": keys}).fetchall()

        settings = {r.setting_key: r.setting_value for r in rows}
        # Mask sensitive fields
        settings["smtp_password"] = "********" if settings.get("smtp_host") else ""
        settings["sms_api_key"] = "********" if settings.get("sms_api_url") else ""
        return settings
    finally:
        db.close()


@router.put("/settings", dependencies=[Depends(require_permission("settings.edit"))])
async def update_notification_settings(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """تحديث إعدادات البريد الإلكتروني و SMS"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(400, "لا يمكن تعديل الإعدادات بدون شركة")

    db = get_db_connection(company_id)
    try:
        allowed_keys = [
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'smtp_from_email', 'smtp_from_name', 'smtp_tls',
            'sms_api_url', 'sms_api_key', 'sms_sender_name',
            'notification_email_enabled', 'notification_sms_enabled'
        ]

        for key, value in data.items():
            if key not in allowed_keys:
                continue
            if value == "********":  # Don't update masked values
                continue

            db.execute(text("""
                INSERT INTO company_settings (setting_key, setting_value)
                VALUES (:key, :val)
                ON CONFLICT (setting_key) DO UPDATE SET setting_value = :val
            """), {"key": key, "val": str(value)})

        db.commit()
        return {"message": "تم تحديث إعدادات الإشعارات بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/test-email", dependencies=[Depends(require_permission("settings.edit"))])
async def test_email_connection(current_user: dict = Depends(get_current_user)):
    """اختبار اتصال SMTP"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(400, "لا يمكن الاختبار بدون شركة")

    db = get_db_connection(company_id)
    try:
        from services.email_service import get_email_service_from_settings, get_base_template

        service = get_email_service_from_settings(db)
        if not service:
            raise HTTPException(400, "إعدادات SMTP غير مكتملة")

        user = db.execute(text("SELECT email FROM company_users WHERE id = :id"), {"id": current_user.id}).fetchone()
        if not user or not user.email:
            raise HTTPException(400, "لا يوجد بريد إلكتروني مسجّل لحسابك")

        html = get_base_template("""
            <h2>✅ اختبار ناجح!</h2>
            <p>تم الاتصال بخادم SMTP بنجاح. هذه رسالة اختبار من نظام AMAN ERP.</p>
        """)
        success = service.send(user.email, "اختبار اتصال AMAN ERP", html)

        if success:
            return {"message": "تم إرسال رسالة الاختبار بنجاح", "sent_to": user.email}
        else:
            raise HTTPException(500, "فشل في إرسال رسالة الاختبار")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()
