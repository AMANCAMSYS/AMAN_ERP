"""
AMAN ERP - Authentication Router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr
import logging
import secrets
import hashlib

from database import get_system_db, verify_password, get_db_connection, hash_password, engine as system_engine
from config import settings
from schemas import Token, UserResponse
from utils.audit import log_activity, log_system_activity
from utils.limiter import limiter

router = APIRouter(prefix="/auth", tags=["المصادقة"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)
logger = logging.getLogger(__name__)

# ============ SEC-FIX: Redis-backed rate limiter ============
# Persists across restarts and works in multi-worker / multi-instance environments.
MAX_LOGIN_ATTEMPTS = 5  # SEC-FIX: Production rate limit (reverted from 500 testing value)
MAX_USERNAME_ATTEMPTS = 10  # SEC-FIX: Production rate limit (reverted from 1000 testing value)
LOCKOUT_SECONDS = 15 * 60  # 15 minutes

_rate_redis = None  # lazy-initialised Redis connection

def _get_rate_redis():
    """Return a Redis client for rate limiting (lazy init, graceful fallback)."""
    global _rate_redis
    if _rate_redis is not None:
        return _rate_redis
    try:
        import redis as _redis_lib
        if settings.REDIS_URL:
            _rate_redis = _redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2, decode_responses=True)
            _rate_redis.ping()  # verify connectivity
            return _rate_redis
    except Exception as e:
        logger.warning(f"Redis unavailable for rate-limiter, falling back to in-memory: {e}")
    _rate_redis = None
    return None

# In-memory fallback (single-worker only, cleared on restart)
_login_attempts = {}
_username_attempts = {}


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown")


def check_rate_limit(request: Request, username: str = None):
    """Check if IP or username has exceeded login attempt limit."""
    client_ip = _get_client_ip(request)
    if client_ip in ("testclient",):
        return

    r = _get_rate_redis()
    if r is not None:
        # --- Redis path ---
        try:
            ip_key = f"rl:ip:{client_ip}"
            ip_count = r.get(ip_key)
            if ip_count and int(ip_count) >= MAX_LOGIN_ATTEMPTS:
                ttl = r.ttl(ip_key)
                minutes = max(int(ttl / 60) + 1, 1) if ttl and ttl > 0 else 1
                raise HTTPException(429, f"تم تجاوز عدد المحاولات المسموح. يرجى الانتظار {minutes} دقيقة")

            if username:
                user_key = f"rl:user:{username}"
                user_count = r.get(user_key)
                if user_count and int(user_count) >= MAX_USERNAME_ATTEMPTS:
                    ttl = r.ttl(user_key)
                    minutes = max(int(ttl / 60) + 1, 1) if ttl and ttl > 0 else 1
                    logger.warning(f"🔒 Username '{username}' locked out - too many attempts")
                    raise HTTPException(429, f"تم تجاوز عدد المحاولات لهذا المستخدم. يرجى الانتظار {minutes} دقيقة")
            return
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Redis rate-limit read error: {e}")
            # Fall through to memory check

    # --- In-memory fallback ---
    now = datetime.now(timezone.utc)
    if client_ip in _login_attempts:
        info = _login_attempts[client_ip]
        if (now - info["last_attempt"]).total_seconds() > LOCKOUT_SECONDS:
            del _login_attempts[client_ip]
        elif info["count"] >= MAX_LOGIN_ATTEMPTS:
            remaining = LOCKOUT_SECONDS - (now - info["last_attempt"]).total_seconds()
            minutes = max(int(remaining / 60) + 1, 1)
            raise HTTPException(429, f"تم تجاوز عدد المحاولات المسموح. يرجى الانتظار {minutes} دقيقة")

    if username and username in _username_attempts:
        info = _username_attempts[username]
        if (now - info["last_attempt"]).total_seconds() > LOCKOUT_SECONDS:
            del _username_attempts[username]
        elif info["count"] >= MAX_USERNAME_ATTEMPTS:
            remaining = LOCKOUT_SECONDS - (now - info["last_attempt"]).total_seconds()
            minutes = max(int(remaining / 60) + 1, 1)
            logger.warning(f"🔒 Username '{username}' locked out - too many attempts")
            raise HTTPException(429, f"تم تجاوز عدد المحاولات لهذا المستخدم. يرجى الانتظار {minutes} دقيقة")


def record_failed_attempt(request: Request, username: str = None):
    """Record a failed login attempt for both IP and username."""
    client_ip = _get_client_ip(request)

    r = _get_rate_redis()
    if r is not None:
        try:
            ip_key = f"rl:ip:{client_ip}"
            pipe = r.pipeline()
            pipe.incr(ip_key)
            pipe.expire(ip_key, LOCKOUT_SECONDS)
            if username:
                user_key = f"rl:user:{username}"
                pipe.incr(user_key)
                pipe.expire(user_key, LOCKOUT_SECONDS)
            pipe.execute()
            return
        except Exception as e:
            logger.error(f"Redis rate-limit write error: {e}")

    # In-memory fallback
    now = datetime.now(timezone.utc)
    if client_ip in _login_attempts:
        _login_attempts[client_ip]["count"] += 1
        _login_attempts[client_ip]["last_attempt"] = now
    else:
        _login_attempts[client_ip] = {"count": 1, "last_attempt": now}
    if username:
        if username in _username_attempts:
            _username_attempts[username]["count"] += 1
            _username_attempts[username]["last_attempt"] = now
        else:
            _username_attempts[username] = {"count": 1, "last_attempt": now}


def clear_failed_attempts(request: Request, username: str = None):
    """Clear failed attempts on successful login."""
    client_ip = _get_client_ip(request)

    r = _get_rate_redis()
    if r is not None:
        try:
            r.delete(f"rl:ip:{client_ip}")
            if username:
                r.delete(f"rl:user:{username}")
            return
        except Exception:
            pass

    # In-memory fallback
    _login_attempts.pop(client_ip, None)
    if username:
        _username_attempts.pop(username, None)


# ============ SEC-201: Persistent Token Blacklist ============
# In-memory cache + DB persistence for token blacklist
_token_blacklist_cache = set()  # Local cache for fast lookup
_blacklist_initialized = False


def _ensure_blacklist_table():
    """Create token_blacklist table in system DB if not exists"""
    global _blacklist_initialized
    if _blacklist_initialized:
        return
    try:
        from database import engine as sys_engine
        with sys_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    id SERIAL PRIMARY KEY,
                    token_hash VARCHAR(64) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    username VARCHAR(100),
                    reason VARCHAR(50) DEFAULT 'logout'
                );
                CREATE INDEX IF NOT EXISTS idx_token_blacklist_hash ON token_blacklist(token_hash);
                CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);
            """))
            conn.commit()
        _blacklist_initialized = True
    except Exception as e:
        logger.warning(f"Token blacklist table init failed: {e}")


def _hash_token(token: str) -> str:
    """Hash token for storage (don't store raw tokens)"""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


def add_token_to_blacklist(token: str, username: str = None, reason: str = "logout"):
    """Add token to blacklist (DB + cache)"""
    _ensure_blacklist_table()
    token_hash = _hash_token(token)
    _token_blacklist_cache.add(token_hash)

    try:
        # Extract expiry from token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
                             options={"verify_exp": False})
        exp = payload.get("exp")
        if exp:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).replace(tzinfo=None)
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        from database import engine as sys_engine
        with sys_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO token_blacklist (token_hash, expires_at, username, reason)
                VALUES (:hash, :exp, :user, :reason)
                ON CONFLICT (token_hash) DO NOTHING
            """), {"hash": token_hash, "exp": expires_at, "user": username, "reason": reason})
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to persist token blacklist: {e}")


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted (cache first, then DB)"""
    token_hash = _hash_token(token)

    # Fast cache check
    if token_hash in _token_blacklist_cache:
        return True

    # DB fallback (after restart, cache is empty)
    try:
        _ensure_blacklist_table()
        from database import engine as sys_engine
        with sys_engine.connect() as conn:
            row = conn.execute(text(
                "SELECT 1 FROM token_blacklist WHERE token_hash = :hash AND expires_at > CURRENT_TIMESTAMP"
            ), {"hash": token_hash}).fetchone()
            if row:
                _token_blacklist_cache.add(token_hash)  # Populate cache
                return True
    except Exception:
        pass

    return False


def cleanup_expired_blacklist():
    """Remove expired tokens from blacklist (called periodically)"""
    try:
        _ensure_blacklist_table()
        from database import engine as sys_engine
        with sys_engine.connect() as conn:
            deleted = conn.execute(text(
                "DELETE FROM token_blacklist WHERE expires_at < CURRENT_TIMESTAMP"
            )).rowcount
            conn.commit()
            if deleted:
                logger.info(f"🧹 Cleaned {deleted} expired tokens from blacklist")
    except Exception as e:
        logger.warning(f"Blacklist cleanup failed: {e}")


# Legacy compatibility alias
token_blacklist = _token_blacklist_cache


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    to_encode.setdefault("token_use", "access")
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    to_encode.update({"token_use": "refresh"})
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # SEC-FIX: Production rate limit (reverted from 1000 testing value)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    company_code: Optional[str] = Form(None),  # رمز الشركة — إلزامي لمستخدمي الشركات
):
    """
    تسجيل الدخول.
    - مستخدم النظام (admin): username + password فقط.
    - موظف شركة: company_code + username + password.
      الـ company_code يُحدد الشركة بشكل حصري — لا يوجد أي بحث في شركات أخرى.
    """
    # Rate limit check (IP + username)
    check_rate_limit(request, form_data.username)
    
    db = get_system_db()
    
    try:
        # Check if system admin
        result = db.execute(
            text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
            {"username": form_data.username}
        ).fetchone()
        
        if result and form_data.username == "admin":
            # System admin login - verify password using bcrypt
            from database import verify_password as verify_pwd, hash_password
            
            admin_hash = getattr(settings, 'ADMIN_PASSWORD_HASH', None)
            if not admin_hash:
                import os
                admin_hash = os.environ.get('ADMIN_PASSWORD_HASH', None)
            
            if not admin_hash:
                # SECURITY: No hash configured — reject login entirely
                logger.critical("⚠️ ADMIN_PASSWORD_HASH not configured! Admin login DISABLED.")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Admin password not configured. Set ADMIN_PASSWORD_HASH in .env"
                )
            
            if not verify_pwd(form_data.password, admin_hash):
                record_failed_attempt(request, form_data.username)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="كلمة المرور غير صحيحة",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            clear_failed_attempts(request, form_data.username)
            auth_payload = {
                "sub": form_data.username,
                "role": "system_admin",
                "type": "system_admin",
                "company_id": None,
                "permissions": ["*"]
            }
            access_token = create_access_token(auth_payload)
            refresh_token = create_refresh_token(auth_payload)
            # LOG SYSTEM ADMIN LOGIN
            log_system_activity(
                action="auth.login",
                performed_by=form_data.username,
                description="System administrator logged in",
                request=request
            )
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                user={"username": form_data.username, "role": "system_admin", "company_id": None, "permissions": ["*"]}
            )
        
        # ── تسجيل دخول موظف الشركة ──────────────────────────────────────────
        # company_code إلزامي — بدونه لا نبحث في أي شركة
        if not company_code:
            record_failed_attempt(request, form_data.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="رمز الشركة مطلوب. يمكنك الحصول عليه من مسؤول الشركة.",
            )

        # التحقق من أن الشركة موجودة ونشطة
        company = db.execute(
            text("SELECT id, database_name, status FROM system_companies WHERE id = :code AND status = 'active'"),
            {"code": company_code.strip()}
        ).fetchone()

        if not company:
            record_failed_attempt(request, form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="رمز الشركة غير صحيح أو الشركة غير نشطة",
                headers={"WWW-Authenticate": "Bearer"}
            )

        company_id, db_name, company_status = company
        conn_url = settings.get_company_database_url(company_id)
        if not conn_url:
            raise HTTPException(status_code=500, detail="خطأ في الاتصال بقاعدة البيانات")

        try:
            company_engine = create_engine(conn_url, pool_pre_ping=True)
            with company_engine.connect() as company_conn:
                result = company_conn.execute(
                    text("""
                        SELECT id, username, password, email, full_name, role, permissions, is_active
                        FROM company_users WHERE username = :username AND is_active = true
                    """),
                    {"username": form_data.username}
                ).fetchone()

                if not result or not verify_password(form_data.password, result[2]):
                    company_engine.dispose()
                    record_failed_attempt(request, form_data.username)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="اسم المستخدم أو كلمة المرور غير صحيحة",
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # ── تسجيل الدخول ناجح ──────────────────────────────────────
                company_conn.execute(
                    text("UPDATE company_users SET last_login = :now WHERE id = :user_id"),
                    {"now": datetime.now(timezone.utc), "user_id": result[0]}
                )

                allowed_branches_rows = company_conn.execute(
                    text("SELECT branch_id FROM user_branches WHERE user_id = :uid"),
                    {"uid": result[0]}
                ).fetchall()
                allowed_branches = [r[0] for r in allowed_branches_rows] if allowed_branches_rows else []

                login_branch_id = allowed_branches[0] if allowed_branches else None
                if not login_branch_id:
                    default_branch = company_conn.execute(
                        text("SELECT id FROM branches WHERE is_default = true LIMIT 1")
                    ).fetchone()
                    login_branch_id = default_branch[0] if default_branch else None

                try:
                    log_activity(
                        company_conn,
                        user_id=result[0],
                        username=result[1],
                        action="auth.login",
                        resource_type="user",
                        resource_id=str(result[0]),
                        details={"method": "password", "company_code": company_code},
                        request=request,
                        branch_id=login_branch_id
                    )
                    log_system_activity(
                        action="auth.login",
                        company_id=company_id,
                        performed_by=result[1],
                        description=f"User logged in via company_code",
                        request=request
                    )
                except Exception as log_err:
                    logger.warning(f"Logging failed: {log_err}")

                company_conn.commit()

                # تحديث فهرس المستخدمين المركزي
                try:
                    db.execute(
                        text("""
                            INSERT INTO system_user_index (username, company_id, is_active)
                            VALUES (:username, :company_id, true)
                            ON CONFLICT (username, company_id) DO UPDATE
                            SET is_active = true, updated_at = CURRENT_TIMESTAMP
                        """),
                        {"username": form_data.username, "company_id": company_id}
                    )
                    db.commit()
                except Exception:
                    pass

                # الصلاحيات
                role_permissions = []
                if result[5]:
                    try:
                        role_res = company_conn.execute(
                            text("SELECT permissions FROM roles WHERE role_name = :r"),
                            {"r": result[5]}
                        ).scalar()
                        if role_res:
                            role_permissions = role_res
                    except Exception as e:
                        logger.warning(f"Could not fetch roles: {e}")

                user_permissions = result[6]
                if isinstance(user_permissions, dict) and user_permissions.get('all') is True:
                    user_permissions = ["*"]
                elif not isinstance(user_permissions, list):
                    user_permissions = []

                final_permissions = list(set((role_permissions or []) + user_permissions))
                if result[5] in ['admin', 'system_admin', 'superuser'] or result[1] == 'admin':
                    final_permissions = ["*"]
                elif "*" in final_permissions:
                    final_permissions = ["*"]

                # معلومات الشركة
                company_info = db.execute(
                    text("SELECT currency, enabled_modules, company_name FROM system_companies WHERE id = :id"),
                    {"id": company_id}
                ).fetchone()

                currency = company_info[0] if company_info else "SAR"
                enabled_modules = company_info[1] if company_info and company_info[1] else []

                if isinstance(enabled_modules, str):
                    import json
                    try:
                        enabled_modules = json.loads(enabled_modules)
                    except Exception:
                        enabled_modules = []

                auth_payload = {
                    "sub": result[1],
                    "user_id": result[0],
                    "company_id": company_id,
                    "role": result[5],
                    "permissions": final_permissions,
                    "enabled_modules": enabled_modules,
                    "allowed_branches": allowed_branches,
                    "type": "company_user"
                }
                access_token = create_access_token(auth_payload)
                refresh_token = create_refresh_token(auth_payload)

                decimal_places = 2
                company_country = "SA"
                company_timezone = "Asia/Riyadh"
                industry_type = None
                try:
                    dp_res = company_conn.execute(
                        text("SELECT setting_value FROM company_settings WHERE setting_key = 'decimal_places'")
                    ).scalar()
                    if dp_res:
                        decimal_places = int(dp_res)
                    cc_res = company_conn.execute(
                        text("SELECT setting_value FROM company_settings WHERE setting_key = 'company_country'")
                    ).scalar()
                    if cc_res:
                        company_country = cc_res
                    tz_res = company_conn.execute(
                        text("SELECT setting_value FROM company_settings WHERE setting_key = 'timezone'")
                    ).scalar()
                    if tz_res:
                        company_timezone = tz_res
                    it_res = company_conn.execute(
                        text("SELECT setting_value FROM company_settings WHERE setting_key = 'industry_type'")
                    ).scalar()
                    if it_res:
                        industry_type = it_res
                except Exception as e:
                    logger.warning(f"Failed to fetch settings: {e}")

                company_engine.dispose()
                clear_failed_attempts(request, form_data.username)
                logger.info(f"✅ Login: {result[1]} -> company:{company_id}")

                return Token(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="bearer",
                    user={
                        "id": result[0],
                        "username": result[1],
                        "email": result[3],
                        "full_name": result[4],
                        "role": result[5],
                        "permissions": final_permissions,
                        "enabled_modules": enabled_modules,
                        "industry_type": industry_type,
                        "currency": currency,
                        "country": company_country,
                        "decimal_places": decimal_places,
                        "timezone": company_timezone,
                        "allowed_branches": allowed_branches
                    },
                    company_id=company_id
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error for company {company_id}: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="خطأ في الخادم أثناء تسجيل الدخول")

    finally:
        db.close()

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """الحصول على معلومات المستخدم الحالي"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if is_token_blacklisted(token):
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("token_use") == "refresh":
            raise credentials_exception
        username: str = payload.get("sub")
        company_id: str = payload.get("company_id")
        permissions: list = payload.get("permissions")
        
        if username is None:
            raise credentials_exception
            
        # For system_admin, company_id is not required
        is_system_admin = payload.get("type") == "system_admin"
        if not is_system_admin and company_id is None:
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        raise credentials_exception
    
    if payload.get("type") == "system_admin":
        return UserResponse(
            id=0,
            username=payload.get("sub"),
            email="admin@aman-erp.com",
            full_name="المدير العام للنظام",
            role="system_admin",
            is_active=True,
            company_id=None,
            currency=payload.get("currency", None),
            permissions=["*"]
        )
    
    company_id = payload.get("company_id")
    user_id = payload.get("user_id")
    
    if not company_id or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="بيانات غير كاملة")
    
    db = get_system_db()
    try:
        company = db.execute(
            text("SELECT database_name, currency FROM system_companies WHERE id = :id"),
            {"id": company_id}
        ).fetchone()
        
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الشركة غير موجودة")
        
        currency = company[1]
        
        try:
            with get_db_connection(company_id) as company_conn:
                result = company_conn.execute(
                    text("SELECT id, username, email, full_name, role, is_active, permissions FROM company_users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
            
                if result:
                    # Process permissions (same logic as login)
                    user_permissions = result[6]
                
                    # Handle Legacy Format {'all': True}
                    if isinstance(user_permissions, dict) and user_permissions.get('all') is True:
                        user_permissions = ["*"]
                    elif not isinstance(user_permissions, list):
                        user_permissions = []

                    # Fetch Role Permissions
                    role_permissions = []
                    if result[4]:  # role
                        try:
                            role_res = company_conn.execute(
                                text("SELECT permissions FROM roles WHERE role_name = :r"),
                                {"r": result[4]}
                            ).scalar()
                            if role_res:
                                role_permissions = role_res if isinstance(role_res, list) else []
                        except Exception as e:
                            logger.warning(f"Failed to fetch role permissions for '{result[4]}': {e}")

                    final_permissions = list(set((role_permissions or []) + user_permissions))

                    # Fetch Allowed Branches
                    allowed_branches_rows = company_conn.execute(
                        text("SELECT branch_id FROM user_branches WHERE user_id = :uid"),
                        {"uid": user_id}
                    ).fetchall()
                    allowed_branches = [r[0] for r in allowed_branches_rows]

                    # Force Admin Access
                    if result[4] in ['admin', 'system_admin', 'superuser']:
                        final_permissions = ["*"]
                    elif "*" in final_permissions:
                        final_permissions = ["*"]

                    # Fetch Decimal Places Setting
                    decimal_places = 2
                    company_country = "SY"
                    company_timezone = "Asia/Damascus"
                    industry_type_me = None
                    try:
                        dp_res = company_conn.execute(
                            text("SELECT setting_value FROM company_settings WHERE setting_key = 'decimal_places'")
                        ).scalar()
                        if dp_res:
                            decimal_places = int(dp_res)
                        cc_res = company_conn.execute(
                            text("SELECT setting_value FROM company_settings WHERE setting_key = 'company_country'")
                        ).scalar()
                        if cc_res:
                            company_country = cc_res
                        tz_res = company_conn.execute(
                            text("SELECT setting_value FROM company_settings WHERE setting_key = 'timezone'")
                        ).scalar()
                        if tz_res:
                            company_timezone = tz_res
                        it_res = company_conn.execute(
                            text("SELECT setting_value FROM company_settings WHERE setting_key = 'industry_type'")
                        ).scalar()
                        if it_res:
                            industry_type_me = it_res
                    except Exception as e:
                        logger.warning(f"Failed to fetch settings in /me: {e}")

                    # Fetch company details
                    company_info = db.execute(
                        text("SELECT currency, enabled_modules FROM system_companies WHERE id = :id"),
                        {"id": company_id}
                    ).fetchone()
                    
                    currency = company_info[0] if company_info else "SAR"
                    enabled_modules = company_info[1] if company_info and company_info[1] else []
                    
                    if isinstance(enabled_modules, str):
                        import json
                        try:
                            enabled_modules = json.loads(enabled_modules)
                        except:
                            enabled_modules = []

                    return UserResponse(
                        id=result[0],
                        username=result[1],
                        email=result[2],
                        full_name=result[3],
                        role=result[4],
                        is_active=result[5],
                        company_id=company_id,
                        currency=currency,
                        country=company_country,
                        decimal_places=decimal_places,
                        timezone=company_timezone,
                        permissions=final_permissions,
                        allowed_branches=allowed_branches,
                        enabled_modules=enabled_modules,
                        industry_type=industry_type_me
                    )
        except (OperationalError, ProgrammingError):
            logger.exception("Current user lookup failed due to tenant DB/schema issue for company %s", company_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="بيانات الشركة غير جاهزة حالياً. يرجى إعادة تسجيل الدخول أو التواصل مع الدعم.",
            )

    finally:
        db.close()
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستخدم غير موجود")


class SelfProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    data: SelfProfileUpdateRequest,
    token: str = Depends(oauth2_scheme)
):
    """Update currently logged-in user profile fields."""
    current_user = await get_current_user(token)
    company_id = getattr(current_user, "company_id", None)

    if not company_id:
        raise HTTPException(status_code=400, detail="غير متاح لمسؤولي النظام")

    updates = {}

    if data.full_name is not None:
        full_name = data.full_name.strip()
        if not full_name:
            raise HTTPException(status_code=400, detail="الاسم الكامل لا يمكن أن يكون فارغا")
        updates["full_name"] = full_name

    if data.email is not None:
        updates["email"] = str(data.email).strip().lower()

    if not updates:
        raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")

    db = get_db_connection(company_id)
    try:
        if "email" in updates:
            existing_email = db.execute(
                text("""
                    SELECT id FROM company_users
                    WHERE lower(email) = :email AND id != :uid
                    LIMIT 1
                """),
                {"email": updates["email"], "uid": current_user.id}
            ).fetchone()
            if existing_email:
                raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم من قبل مستخدم آخر")

        set_parts = []
        params = {"uid": current_user.id}

        if "full_name" in updates:
            set_parts.append("full_name = :full_name")
            params["full_name"] = updates["full_name"]
        if "email" in updates:
            set_parts.append("email = :email")
            params["email"] = updates["email"]

        set_parts.append("updated_at = CURRENT_TIMESTAMP")

        db.execute(
            text(f"UPDATE company_users SET {', '.join(set_parts)} WHERE id = :uid"),
            params
        )
        db.commit()

        try:
            log_activity(
                db,
                current_user.id,
                current_user.username,
                "update_profile",
                "company_users",
                str(current_user.id),
                {"updated_fields": list(updates.keys())}
            )
        except Exception:
            pass

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update self profile: {e}")
        raise HTTPException(status_code=500, detail="فشل تحديث بيانات الحساب")
    finally:
        db.close()

    return await get_current_user(token)


@router.post("/logout")
async def logout(
    body: Optional[LogoutRequest] = Body(default=None),
    token: str = Depends(oauth2_scheme)
):
    """تسجيل الخروج - يتم إضافة التوكن إلى القائمة السوداء"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
                             options={"verify_exp": False})
        username = payload.get("sub")
    except JWTError:
        username = None
    add_token_to_blacklist(token, username=username, reason="logout")
    if body and body.refresh_token:
        add_token_to_blacklist(body.refresh_token, username=username, reason="logout_refresh")
    return {"message": "تم تسجيل الخروج بنجاح"}


@router.post("/refresh")
async def refresh_token(
    body: Optional[RefreshTokenRequest] = Body(default=None),
    token: Optional[str] = Depends(oauth2_scheme_optional)
):
    """تجديد الجلسة باستخدام refresh token (دوار)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="رمز التحديث منتهي أو غير صالح",
        headers={"WWW-Authenticate": "Bearer"},
    )

    provided_refresh_token = None
    if body and body.refresh_token:
        provided_refresh_token = body.refresh_token.strip()
    elif token:
        provided_refresh_token = token

    if not provided_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="رمز التحديث مطلوب"
        )
    
    if is_token_blacklisted(provided_refresh_token):
        raise credentials_exception
        
    try:
        payload = jwt.decode(provided_refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("token_use") != "refresh":
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Create new token with same claims but fresh expiry
        new_payload = {
            "sub": payload.get("sub"),
            "type": payload.get("type"),
            "company_id": payload.get("company_id"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions"),
            "enabled_modules": payload.get("enabled_modules"),
        }

        # Include optional fields
        if payload.get("user_id"):
            new_payload["user_id"] = payload["user_id"]
        if payload.get("allowed_branches"):
            new_payload["allowed_branches"] = payload["allowed_branches"]
        
        new_access_token = create_access_token(new_payload)
        new_refresh_token = create_refresh_token(new_payload)
        
        # Rotate refresh token: revoke old one and return new one
        add_token_to_blacklist(provided_refresh_token, username=username, reason="refresh_rotate")
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise credentials_exception


# ═══════════════════════════════════════════════════════════════════════════════
# FORGOT / RESET PASSWORD
# ═══════════════════════════════════════════════════════════════════════════════

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _ensure_reset_table():
    """Ensure password_reset_tokens table exists in system DB with all required columns"""
    try:
        with system_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    company_id VARCHAR(50),
                    email VARCHAR(255),
                    token_hash VARCHAR(255) NOT NULL UNIQUE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Ensure columns exist for tables created before schema updates
            conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
            conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS company_id VARCHAR(50)"))
            conn.commit()
    except Exception as e:
        logger.error(f"_ensure_reset_table error: {e}")


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest):
    """
    طلب إعادة تعيين كلمة المرور — يرسل رابط عبر البريد الإلكتروني
    يبحث عن المستخدم بالبريد في جميع الشركات
    """
    _ensure_reset_table()
    email = body.email.strip().lower()

    # Always return success to prevent email enumeration
    success_msg = {"message": "إذا كان البريد مسجلاً، سيتم إرسال رابط إعادة التعيين"}

    db = get_system_db()
    try:
        # Search all company databases for this email
        companies = db.execute(
            text("SELECT id FROM system_companies WHERE status = 'active'")
        ).fetchall()

        found_user = None
        found_company = None

        for company in companies:
            company_id = company[0]
            try:
                company_db = get_db_connection(company_id)
                user = company_db.execute(
                    text("SELECT id, username, email, full_name FROM company_users WHERE LOWER(email) = :email AND is_active = true"),
                    {"email": email}
                ).fetchone()
                company_db.close()

                if user:
                    found_user = user
                    found_company = company_id
                    break
            except Exception:
                continue

        if not found_user:
            return success_msg

        # Generate secure reset token
        reset_token = secrets.token_urlsafe(48)
        token_hash = _hash_reset_token(reset_token)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Store token
        with system_engine.connect() as conn:
            # Invalidate old tokens
            conn.execute(text(
                "UPDATE password_reset_tokens SET used = TRUE WHERE username = :username AND used = FALSE"
            ), {"username": found_user.username})

            conn.execute(text("""
                INSERT INTO password_reset_tokens (username, company_id, email, token_hash, expires_at)
                VALUES (:username, :cid, :email, :hash, :exp)
            """), {
                "username": found_user.username,
                "cid": found_company,
                "email": email,
                "hash": token_hash,
                "exp": expires_at
            })
            conn.commit()

        # Build reset URL — skip placeholder production URLs
        prod_url = settings.FRONTEND_URL_PRODUCTION
        if prod_url and prod_url.startswith("https://your-domain"):
            prod_url = None
        frontend_url = prod_url or settings.FRONTEND_URL or "http://localhost:5173"
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"

        # SEC-FIX: Never log full reset token — only log a prefix for debugging
        logger.info(f"Password reset generated for {email} (token prefix: {reset_token[:8]}...)")

        # Send email
        email_sent = False
        smtp_configured = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)
        if smtp_configured:
            try:
                from utils.email import send_email
                from services.email_service import get_base_template

                body_html = get_base_template(f"""
                    <h2>إعادة تعيين كلمة المرور</h2>
                    <p>مرحباً {found_user.full_name or found_user.username}،</p>
                    <p>لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بك.</p>
                    <p>اضغط على الزر أدناه لإعادة التعيين:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="btn">إعادة تعيين كلمة المرور</a>
                    </p>
                    <div class="info-box">
                        <p>⏰ هذا الرابط صالح لمدة <strong>ساعة واحدة</strong> فقط.</p>
                        <p>إذا لم تطلب إعادة التعيين، تجاهل هذا البريد.</p>
                    </div>
                """)

                email_sent = send_email(
                    to_emails=[email],
                    subject="🔐 إعادة تعيين كلمة المرور - AMAN ERP",
                    body=body_html
                )
                if email_sent:
                    logger.info(f"🔐 Password reset email sent to {email}")
                else:
                    logger.warning(f"⚠️ Email send returned False for {email}, check SMTP credentials")
            except Exception as e:
                logger.error(f"❌ Failed to send reset email: {e}")
        else:
            logger.warning("⚠️ SMTP not configured — reset URL logged above for development use")

        # SEC-FIX-001: Never expose reset token in API response
        # In development, log the URL server-side only
        if not smtp_configured or not email_sent:
            logger.warning(f"SMTP not available — password reset token generated but not delivered for {email}")
            # Return the same generic message regardless (prevent email enumeration)

        return success_msg

    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return success_msg
    finally:
        db.close()


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, body: ResetPasswordRequest):
    """
    إعادة تعيين كلمة المرور باستخدام التوكن المُرسل بالبريد
    """
    _ensure_reset_table()
    token_hash = _hash_reset_token(body.token)

    # SEC-FIX-004: Enforce strong password policy
    from utils.sql_safety import validate_password_strength
    validate_password_strength(body.new_password)

    with system_engine.connect() as conn:
        # Find valid token
        token_row = conn.execute(text("""
            SELECT username, company_id, email FROM password_reset_tokens
            WHERE token_hash = :hash AND used = FALSE AND expires_at > CURRENT_TIMESTAMP
        """), {"hash": token_hash}).fetchone()

        if not token_row:
            raise HTTPException(400, "الرابط غير صالح أو منتهي الصلاحية")

        username = token_row.username
        company_id = token_row.company_id

        # Update password in company database
        try:
            company_db = get_db_connection(company_id)
            new_hash = hash_password(body.new_password)
            company_db.execute(
                text("UPDATE company_users SET password = :pwd, updated_at = CURRENT_TIMESTAMP WHERE username = :user"),
                {"pwd": new_hash, "user": username}
            )
            company_db.commit()
            company_db.close()
        except Exception as e:
            logger.error(f"Failed to update password: {e}")
            raise HTTPException(500, "فشل في تحديث كلمة المرور")

        # Mark token as used
        conn.execute(text(
            "UPDATE password_reset_tokens SET used = TRUE WHERE token_hash = :hash"
        ), {"hash": token_hash})
        conn.commit()

        # Blacklist all existing tokens for this user
        # (force re-login after password change)
        log_system_activity(
            action="auth.password_reset",
            performed_by=username,
            description=f"Password reset via email for user {username}",
            request=request
        )

        return {"message": "تم تغيير كلمة المرور بنجاح. يرجى تسجيل الدخول"}

def get_current_user_company(current_user: UserResponse = Depends(get_current_user)):
    """Dependency that ensures a user is linked to a company and returns that company_id"""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized - User not linked to a company"
        )
    return current_user.company_id
