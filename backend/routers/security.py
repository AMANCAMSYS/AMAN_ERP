"""
Security Router - SEC-001, SEC-002, SEC-003, SEC-201, SEC-202
المصادقة الثنائية (2FA) + سياسات كلمات المرور + إدارة الجلسات
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from database import get_db_connection, hash_password, verify_password
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import logging
import re

logger = logging.getLogger("aman.security")

router = APIRouter(prefix="/security", tags=["الأمان"])


# ===================== 2FA Schemas =====================

class TwoFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_data: str

class TwoFAVerifyRequest(BaseModel):
    code: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordPolicySchema(BaseModel):
    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    max_age_days: int = 90
    prevent_reuse: int = 5


# ===================== 2FA Setup & Verification =====================

@router.post("/2fa/setup")
def setup_2fa(current_user=Depends(get_current_user)):
    """
    إعداد المصادقة الثنائية - يولّد مفتاح سري ورمز QR
    """
    db = get_db_connection(current_user.company_id)
    try:
        import pyotp
        import base64

        # Check if already enabled
        existing = db.execute(text("""
            SELECT is_enabled FROM user_2fa_settings WHERE user_id = :uid
        """), {"uid": current_user.id}).fetchone()

        if existing and existing.is_enabled:
            raise HTTPException(400, "المصادقة الثنائية مفعّلة بالفعل")

        # Generate TOTP secret
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=current_user.username,
            issuer_name="AMAN ERP"
        )

        # Store secret (not yet enabled)
        db.execute(text("""
            INSERT INTO user_2fa_settings (user_id, secret_key, is_enabled)
            VALUES (:uid, :secret, FALSE)
            ON CONFLICT (user_id) DO UPDATE SET secret_key = :secret, is_enabled = FALSE
        """), {"uid": current_user.id, "secret": secret})
        db.commit()

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_data": provisioning_uri,  # Frontend can use a QR library
            "message": "امسح رمز QR باستخدام تطبيق المصادقة، ثم أدخل الرمز للتأكيد"
        }
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(500, "مكتبة pyotp غير مثبتة. قم بتشغيل: pip install pyotp")
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/2fa/verify")
def verify_2fa(data: TwoFAVerifyRequest, current_user=Depends(get_current_user)):
    """
    التحقق من رمز 2FA وتفعيله
    """
    db = get_db_connection(current_user.company_id)
    try:
        import pyotp

        settings_row = db.execute(text("""
            SELECT secret_key, is_enabled FROM user_2fa_settings WHERE user_id = :uid
        """), {"uid": current_user.id}).fetchone()

        if not settings_row or not settings_row.secret_key:
            raise HTTPException(400, "يجب إعداد 2FA أولاً")

        totp = pyotp.TOTP(settings_row.secret_key)
        if not totp.verify(data.code, valid_window=1):
            raise HTTPException(400, "الرمز غير صحيح أو منتهي الصلاحية")

        # Enable 2FA
        db.execute(text("""
            UPDATE user_2fa_settings SET is_enabled = TRUE, verified_at = CURRENT_TIMESTAMP
            WHERE user_id = :uid
        """), {"uid": current_user.id})
        db.commit()

        # Generate backup codes
        backup_codes = [pyotp.random_base32()[:8] for _ in range(8)]
        db.execute(text("""
            UPDATE user_2fa_settings SET backup_codes = :codes WHERE user_id = :uid
        """), {"uid": current_user.id, "codes": ",".join(backup_codes)})
        db.commit()

        try:
            log_activity(db, current_user.id, current_user.username, "enable_2fa",
                         "security", str(current_user.id), {})
        except Exception:
            pass

        return {
            "message": "تم تفعيل المصادقة الثنائية بنجاح",
            "backup_codes": backup_codes,
            "warning": "احتفظ بأكواد الاسترداد في مكان آمن. لن تظهر مرة أخرى!"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/2fa/disable")
def disable_2fa(data: TwoFAVerifyRequest, current_user=Depends(get_current_user)):
    """تعطيل المصادقة الثنائية (يتطلب رمز تأكيد)"""
    db = get_db_connection(current_user.company_id)
    try:
        import pyotp

        settings_row = db.execute(text("""
            SELECT secret_key, is_enabled FROM user_2fa_settings WHERE user_id = :uid
        """), {"uid": current_user.id}).fetchone()

        if not settings_row or not settings_row.is_enabled:
            raise HTTPException(400, "المصادقة الثنائية غير مفعّلة")

        totp = pyotp.TOTP(settings_row.secret_key)
        if not totp.verify(data.code, valid_window=1):
            raise HTTPException(400, "الرمز غير صحيح")

        db.execute(text("""
            UPDATE user_2fa_settings SET is_enabled = FALSE, secret_key = NULL, backup_codes = NULL
            WHERE user_id = :uid
        """), {"uid": current_user.id})
        db.commit()

        try:
            log_activity(db, current_user.id, current_user.username, "disable_2fa",
                         "security", str(current_user.id), {})
        except Exception:
            pass

        return {"message": "تم تعطيل المصادقة الثنائية"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/2fa/status")
def get_2fa_status(current_user=Depends(get_current_user)):
    """حالة المصادقة الثنائية للمستخدم الحالي"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"is_enabled": False}

    db = get_db_connection(company_id)
    try:
        row = db.execute(text("""
            SELECT is_enabled, verified_at FROM user_2fa_settings WHERE user_id = :uid
        """), {"uid": current_user.id}).fetchone()

        return {
            "is_enabled": row.is_enabled if row else False,
            "verified_at": str(row.verified_at) if row and row.verified_at else None
        }
    except Exception:
        return {"is_enabled": False}
    finally:
        db.close()


# ===================== Password Policies =====================

def validate_password(password: str, policy: dict) -> dict:
    """Validate a password against the company's password policy."""
    errors = []
    min_length = policy.get("min_length", 8)

    if len(password) < min_length:
        errors.append(f"يجب ألا تقل كلمة المرور عن {min_length} أحرف")
    if policy.get("require_uppercase", True) and not re.search(r'[A-Z]', password):
        errors.append("يجب أن تحتوي على حرف كبير واحد على الأقل")
    if policy.get("require_lowercase", True) and not re.search(r'[a-z]', password):
        errors.append("يجب أن تحتوي على حرف صغير واحد على الأقل")
    if policy.get("require_numbers", True) and not re.search(r'\d', password):
        errors.append("يجب أن تحتوي على رقم واحد على الأقل")
    if policy.get("require_special", True) and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("يجب أن تحتوي على رمز خاص واحد على الأقل")

    return {"valid": len(errors) == 0, "errors": errors}


def get_password_policy(db) -> dict:
    """Get password policy from company_settings."""
    try:
        import json
        row = db.execute(text("""
            SELECT setting_value FROM company_settings WHERE setting_key = 'password_policy'
        """)).scalar()
        if row:
            return json.loads(row)
    except Exception:
        pass
    # Default policy
    return {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True,
        "max_age_days": 90,
        "prevent_reuse": 5
    }


@router.post("/change-password")
def change_password(data: PasswordChangeRequest, current_user=Depends(get_current_user)):
    """تغيير كلمة المرور مع التحقق من السياسة"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(400, "غير متاح لمسؤولي النظام")

    db = get_db_connection(company_id)
    try:
        # Verify current password
        user = db.execute(text("SELECT password FROM company_users WHERE id = :id"),
                          {"id": current_user.id}).fetchone()
        if not user or not verify_password(data.current_password, user.password):
            raise HTTPException(400, "كلمة المرور الحالية غير صحيحة")

        # Validate new password against policy
        policy = get_password_policy(db)
        validation = validate_password(data.new_password, policy)
        if not validation["valid"]:
            raise HTTPException(400, "كلمة المرور لا تستوفي الشروط:\n" + "\n".join(validation["errors"]))

        # Check reuse prevention
        prevent_reuse = policy.get("prevent_reuse", 5)
        if prevent_reuse > 0:
            old_passwords = db.execute(text("""
                SELECT password_hash FROM password_history
                WHERE user_id = :uid ORDER BY created_at DESC LIMIT :limit
            """), {"uid": current_user.id, "limit": prevent_reuse}).fetchall()

            for old_pw in old_passwords:
                if verify_password(data.new_password, old_pw.password_hash):
                    raise HTTPException(400, f"لا يمكن استخدام كلمة مرور مستخدمة في آخر {prevent_reuse} مرات")

        # Update password
        new_hash = hash_password(data.new_password)
        db.execute(text("""
            UPDATE company_users SET password = :pw, updated_at = CURRENT_TIMESTAMP WHERE id = :id
        """), {"pw": new_hash, "id": current_user.id})

        # Save to password history
        db.execute(text("""
            INSERT INTO password_history (user_id, password_hash)
            VALUES (:uid, :pw)
        """), {"uid": current_user.id, "pw": new_hash})

        db.commit()

        try:
            log_activity(db, current_user.id, current_user.username, "change_password",
                         "security", str(current_user.id), {})
        except Exception:
            pass

        return {"message": "تم تغيير كلمة المرور بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/password-policy", dependencies=[Depends(require_permission(["settings.view", "security.view"]))])
def get_password_policy_endpoint(current_user=Depends(get_current_user)):
    """جلب سياسة كلمات المرور الحالية"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return get_password_policy(None)

    db = get_db_connection(company_id)
    try:
        return get_password_policy(db)
    finally:
        db.close()


@router.put("/password-policy", dependencies=[Depends(require_permission(["settings.edit", "security.manage"]))])
def update_password_policy(data: PasswordPolicySchema, current_user=Depends(get_current_user)):
    """تحديث سياسة كلمات المرور"""
    db = get_db_connection(current_user.company_id)
    try:
        import json
        policy_json = json.dumps(data.dict())

        db.execute(text("""
            INSERT INTO company_settings (setting_key, setting_value)
            VALUES ('password_policy', :val)
            ON CONFLICT (setting_key) DO UPDATE SET setting_value = :val
        """), {"val": policy_json})
        db.commit()

        return {"message": "تم تحديث سياسة كلمات المرور"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ===================== Active Sessions =====================

@router.get("/sessions")
def list_active_sessions(current_user=Depends(get_current_user)):
    """جلب الجلسات النشطة للمستخدم"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"sessions": []}

    db = get_db_connection(company_id)
    try:
        rows = db.execute(text("""
            SELECT id, ip_address, user_agent, login_time, last_activity, is_active
            FROM user_sessions
            WHERE user_id = :uid AND is_active = TRUE
            ORDER BY last_activity DESC
        """), {"uid": current_user.id}).fetchall()

        sessions = []
        for r in rows:
            s = dict(r._mapping)
            for k in ["login_time", "last_activity"]:
                if s.get(k):
                    s[k] = str(s[k])
            sessions.append(s)

        return {"sessions": sessions}
    except Exception:
        return {"sessions": []}
    finally:
        db.close()


@router.delete("/sessions/{session_id}")
def terminate_session(session_id: int, current_user=Depends(get_current_user)):
    """إنهاء جلسة محددة"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(400, "غير متاح")

    db = get_db_connection(company_id)
    try:
        db.execute(text("""
            UPDATE user_sessions SET is_active = FALSE
            WHERE id = :sid AND user_id = :uid
        """), {"sid": session_id, "uid": current_user.id})
        db.commit()
        return {"message": "تم إنهاء الجلسة"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.delete("/sessions")
def terminate_all_sessions(current_user=Depends(get_current_user)):
    """إنهاء جميع الجلسات الأخرى"""
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        raise HTTPException(400, "غير متاح")

    db = get_db_connection(company_id)
    try:
        db.execute(text("""
            UPDATE user_sessions SET is_active = FALSE
            WHERE user_id = :uid
        """), {"uid": current_user.id})
        db.commit()
        return {"message": "تم إنهاء جميع الجلسات"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ===================== SEC-202: Password Expiry & Notifications =====================

@router.get("/password-expiry")
def check_password_expiry(current_user=Depends(get_current_user)):
    """
    فحص حالة انتهاء صلاحية كلمة المرور
    يعيد: عدد الأيام المتبقية، هل منتهية، هل قريبة من الانتهاء
    """
    company_id = getattr(current_user, "company_id", None)
    if not company_id:
        return {"expired": False, "days_remaining": 999, "warning": False}

    db = get_db_connection(company_id)
    try:
        policy = get_password_policy(db)
        max_age_days = policy.get("max_age_days", 90)

        if max_age_days <= 0:
            return {"expired": False, "days_remaining": 999, "warning": False,
                    "message": "سياسة انتهاء كلمات المرور معطّلة"}

        # Get last password change date
        last_change = db.execute(text("""
            SELECT created_at FROM password_history
            WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1
        """), {"uid": current_user.id}).scalar()

        if not last_change:
            # No password history - check user created_at
            last_change = db.execute(text("""
                SELECT COALESCE(updated_at, created_at) FROM company_users WHERE id = :uid
            """), {"uid": current_user.id}).scalar()

        if not last_change:
            return {"expired": False, "days_remaining": max_age_days, "warning": False}

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if hasattr(last_change, 'replace'):
            # Ensure timezone-naive comparison
            last_change = last_change.replace(tzinfo=None) if hasattr(last_change, 'tzinfo') and last_change.tzinfo else last_change

        days_since_change = (now - last_change).days
        days_remaining = max(0, max_age_days - days_since_change)
        is_expired = days_remaining == 0
        is_warning = 0 < days_remaining <= 7  # Warning 7 days before

        result = {
            "expired": is_expired,
            "days_remaining": days_remaining,
            "warning": is_warning,
            "max_age_days": max_age_days,
            "last_changed": str(last_change)
        }

        if is_expired:
            result["message"] = "كلمة المرور منتهية الصلاحية. يرجى تغييرها فوراً"
        elif is_warning:
            result["message"] = f"تنبيه: ستنتهي صلاحية كلمة المرور خلال {days_remaining} يوم"

        return result
    except Exception as e:
        logger.warning(f"Password expiry check failed: {e}")
        return {"expired": False, "days_remaining": 999, "warning": False}
    finally:
        db.close()


def check_password_expiry_on_login(company_conn, user_id: int, policy: dict = None) -> dict:
    """
    فحص انتهاء كلمة المرور عند تسجيل الدخول (يُستدعى من auth.py login)
    Returns dict with status info to include in login response
    """
    try:
        if not policy:
            policy = get_password_policy(company_conn)

        max_age_days = policy.get("max_age_days", 90)
        if max_age_days <= 0:
            return {}

        last_change = company_conn.execute(text("""
            SELECT created_at FROM password_history
            WHERE user_id = :uid ORDER BY created_at DESC LIMIT 1
        """), {"uid": user_id}).scalar()

        if not last_change:
            last_change = company_conn.execute(text("""
                SELECT COALESCE(updated_at, created_at) FROM company_users WHERE id = :uid
            """), {"uid": user_id}).scalar()

        if not last_change:
            return {}

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if hasattr(last_change, 'replace') and hasattr(last_change, 'tzinfo') and last_change.tzinfo:
            last_change = last_change.replace(tzinfo=None)

        days_since = (now - last_change).days
        days_remaining = max(0, max_age_days - days_since)

        if days_remaining == 0:
            return {"password_expired": True, "password_message": "كلمة المرور منتهية. يرجى تغييرها فوراً"}
        elif days_remaining <= 7:
            return {"password_warning": True,
                    "password_days_remaining": days_remaining,
                    "password_message": f"تنبيه: ستنتهي صلاحية كلمة المرور خلال {days_remaining} يوم"}
        return {}
    except Exception:
        return {}
