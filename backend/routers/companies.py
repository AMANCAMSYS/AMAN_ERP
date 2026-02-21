"""
AMAN ERP - Companies Router
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import os
import shutil
from datetime import datetime
from typing import List, Optional

from database import (
    get_system_db, 
    generate_company_id,
    create_company_database,
    create_company_tables,
    initialize_company_default_data
)
from schemas import CompanyCreateRequest, CompanyCreateResponse, CompanyListResponse, CompanyListItem, CompanyUpdateRequest
from utils.permissions import require_permission

router = APIRouter(prefix="/companies", tags=["إدارة الشركات"])
logger = logging.getLogger(__name__)

# Rate limiting for company registration
_register_attempts = {}  # {ip: {"count": int, "first_attempt": datetime}}
MAX_REGISTER_PER_HOUR = 3


def check_register_rate_limit(request):
    """Limit company registrations to prevent abuse"""
    from datetime import timedelta
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.utcnow()
    
    if client_ip in _register_attempts:
        info = _register_attempts[client_ip]
        if now - info["first_attempt"] > timedelta(hours=1):
            _register_attempts[client_ip] = {"count": 1, "first_attempt": now}
            return
        if info["count"] >= MAX_REGISTER_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail="تم تجاوز الحد الأقصى لتسجيل الشركات. يرجى الانتظار ساعة."
            )
        info["count"] += 1
    else:
        _register_attempts[client_ip] = {"count": 1, "first_attempt": now}


from fastapi import Request

@router.post("/register", response_model=CompanyCreateResponse, status_code=status.HTTP_201_CREATED)
async def register_new_company(request_body: CompanyCreateRequest, request: Request):
    """
    تسجيل شركة جديدة - company_id يُنشأ تلقائياً
    
    يتم تنفيذ:
    1. توليد company_id فريد (8 أحرف)
    2. إنشاء قاعدة بيانات PostgreSQL مستقلة
    3. إنشاء 91 جدول
    4. تهيئة البيانات الافتراضية
    5. إنشاء حساب المدير
    """
    db = get_system_db()
    
    try:
        # Rate limit check
        check_register_rate_limit(request)
        
        # Check if email exists
        existing = db.execute(
            text("SELECT 1 FROM system_companies WHERE email = :email"),
            {"email": request_body.email}
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="البريد مستخدم")
        
        # Generate unique company_id
        company_id = generate_company_id()
        max_attempts = 10
        attempts = 0
        
        while db.execute(
            text("SELECT 1 FROM system_companies WHERE id = :id"),
            {"id": company_id}
        ).fetchone() and attempts < max_attempts:
            company_id = generate_company_id()
            attempts += 1
        
        if attempts >= max_attempts:
            raise HTTPException(status_code=500, detail="فشل توليد معرف فريد")
        
        logger.info(f"🆔 Generated company_id: {company_id}")
        
        # Create database
        success, message, db_name, db_user = create_company_database(company_id, request_body.admin_password)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"فشل إنشاء قاعدة البيانات: {message}")
        
        try:
            # Create all 91 tables
            success, message = create_company_tables(company_id, request_body.currency)
            if not success:
                db.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
                db.execute(text(f'DROP USER IF EXISTS {db_user}'))
                db.commit()
                raise HTTPException(status_code=500, detail=f"فشل إنشاء الجداول: {message}")
            
            # Initialize default data
            success, message = initialize_company_default_data(
                company_id,
                request_body.admin_username,
                request_body.admin_email,
                request_body.admin_password,
                request_body.admin_full_name,
                request_body.timezone,
                request_body.currency
            )
            
            if not success:
                logger.warning(f"⚠️ Warning: {message}")
            
            # Register in system database
            db.execute(text("""
                INSERT INTO system_companies 
                (id, company_name, company_name_en, commercial_registry, tax_number, 
                 phone, email, address, database_name, database_user, currency, 
                 status, plan_type, created_at, activated_at)
                VALUES 
                (:id, :name, :name_en, :registry, :tax, :phone, :email, :address, 
                 :db_name, :db_user, :currency, 'active', :plan, :now, :now)
            """), {
                "id": company_id,
                "name": request_body.company_name,
                "name_en": request_body.company_name_en,
                "registry": request_body.commercial_registry,
                "tax": request_body.tax_number,
                "phone": request_body.phone,
                "email": request_body.email,
                "address": request_body.address,
                "db_name": db_name,
                "db_user": db_user,
                "currency": request_body.currency,
                "plan": request_body.plan_type,
                "now": datetime.utcnow()
            })
            
            db.commit()
            logger.info(f"✅ Created company: {request_body.company_name} (ID: {company_id})")
            
            return CompanyCreateResponse(
                success=True,
                company_id=company_id,
                company_name=request_body.company_name,
                database_name=db_name,
                message=f"تم إنشاء الشركة بنجاح. معرف الشركة: {company_id}",
                admin_username=request_body.admin_username,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ Error in register_new_company: {str(e)}\nTraceback:\n{error_details}")
            
            # Write to file for debugging
            try:
                with open("last_error.txt", "w") as f:
                    f.write(f"Error: {str(e)}\n")
                    f.write(error_details)
            except Exception as write_err:
                logger.warning(f"Failed to write error log file: {write_err}")
                
            db.rollback()
            try:
                db.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
                db.execute(text(f'DROP USER IF EXISTS {db_user}'))
                db.commit()
            except Exception as cleanup_err:
                logger.error(f"Failed to cleanup after company creation failure: {cleanup_err}")
            raise HTTPException(status_code=500, detail=f"فشل إنشاء الشركة: {str(e)} | Type: {type(e).__name__}")

    
    finally:
        db.close()


@router.get("/list", response_model=CompanyListResponse, dependencies=[Depends(require_permission("admin.companies"))])
def list_companies(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    search: Optional[str] = None
):
    """عرض قائمة الشركات مع دعم البحث والترقيم"""
    db = get_system_db()
    
    try:
        # Build filters
        base_query = "FROM system_companies WHERE 1=1"
        params = {"limit": limit, "skip": skip}
        
        if status_filter:
            base_query += " AND status = :status"
            params["status"] = status_filter
            
        if search:
            base_query += " AND (company_name ILIKE :search OR email ILIKE :search OR database_name ILIKE :search)"
            params["search"] = f"%{search}%"

        # 1. Total count query
        count_query = f"SELECT count(*) {base_query}"
        total = db.execute(text(count_query), params).scalar() or 0

        # 2. Data query
        query = f"SELECT id, company_name, database_name, email, status, plan_type, created_at {base_query}"
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :skip"
        
        result = db.execute(text(query), params).fetchall()
        
        companies = [
            CompanyListItem(
                id=row[0],
                company_name=row[1],
                database_name=row[2],
                email=row[3],
                status=row[4],
                plan_type=row[5],
                created_at=row[6]
            )
            for row in result
        ]
        
        return {
            "companies": companies,
            "total": total
        }
    finally:
        db.close()


from routers.auth import decode_token, oauth2_scheme

@router.get("/{company_id}")
def get_company(
    company_id: str,
    token: str = Depends(oauth2_scheme)
):
    """عرض تفاصيل شركة - متاح للمدير أو للمستخدمين التابعين لنفس الشركة"""
    # Check permissions manually
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # If user is NOT system admin AND requesting a different company -> Forbidden
    if user.get("company_id") != company_id:
        # Check if they have admin permission (for system admins viewing other companies)
        # Note: We need to re-implement permission check logic here or use simple role check
        # For now, simplest is: Only System Admin OR User belonging to Company can view.
        
        # If user is system admin (role='system_admin'), they can view anything.
        # But our token structure varies. Let's assume 'system_admin' role exists in token? 
        # Actually safer: Use existing permission logic if easier, OR just simple:
        
        if user.get("role") != "system_admin":
             raise HTTPException(status_code=403, detail="Access Denied")

    """عرض تفاصيل شركة"""
    db = get_system_db()
    
    try:
        result = db.execute(
            text("""
                SELECT id, company_name, company_name_en, email, phone, address, 
                       status, plan_type, currency, created_at, activated_at
                FROM system_companies WHERE id = :id
            """),
            {"id": company_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الشركة غير موجودة")
        
        return {
            "id": result[0],
            "company_name": result[1],
            "company_name_en": result[2],
            "email": result[3],
            "phone": result[4],
            "address": result[5],
            "status": result[6],
            "plan_type": result[7],
            "currency": result[8],
            "created_at": result[9],
            "activated_at": result[10]
        }
    except Exception as e:
        logger.error(f"Error in get_company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
@router.put("/update/{company_id}")
def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    token: str = Depends(oauth2_scheme)
):
    """Update company details"""
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Only System Admin OR Company Admin can update
    is_sys_admin = user.get("role") == "system_admin"
    is_own_company = user.get("company_id") == company_id
    
    # Check if user is an admin within their own company
    user_role = user.get("role")
    is_company_admin = user_role in ["company_admin", "admin", "superuser"]
    
    # Allow if System Admin OR (Own Company AND Company Admin)
    allowed = is_sys_admin or (is_own_company and is_company_admin)
    
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")

    db = get_system_db()
    try:
        # Check if company exists
        existing = db.execute(
            text("SELECT id FROM system_companies WHERE id = :id"),
            {"id": company_id}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Company not found")

        # Prepare update query
        update_data = request.dict(exclude_unset=True)
        if not update_data:
            return {"success": True, "message": "No changes provided"}

        set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
        update_data["id"] = company_id
        
        db.execute(
            text(f"UPDATE system_companies SET {set_clause} WHERE id = :id"),
            update_data
        )
        db.commit()
        
        return {"success": True, "message": "Company updated successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating company {company_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

@router.post("/upload-logo/{company_id}")
async def upload_company_logo(
    company_id: str,
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    """رفع شعار الشركة"""
    from routers.auth import decode_token, oauth2_scheme
    from database import SessionLocal
    user = decode_token(token)
    if not user or (user.get("company_id") != company_id and user.get("role") != "system_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="يجب رفع صورة")

    # Save path
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم")
        
    filename = f"logo_{company_id}{file_ext}"
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "logos")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Save to company_settings
        from database import get_db_connection
        db = get_db_connection(company_id)
        try:
            logo_url = f"/uploads/logos/{filename}"
            # Check if key exists
            exists = db.execute(text("SELECT 1 FROM company_settings WHERE setting_key = 'company_logo'")).fetchone()
            if exists:
                db.execute(text("UPDATE company_settings SET setting_value = :val WHERE setting_key = 'company_logo'"), {"val": logo_url})
            else:
                db.execute(text("INSERT INTO company_settings (setting_key, setting_value) VALUES ('company_logo', :val)"), {"val": logo_url})
            
            # Also update system_companies if possible (for global view)
            try:
                sys_db = SessionLocal()
                sys_db.execute(text("UPDATE system_companies SET logo_url = :url WHERE id = :id"), {"url": logo_url, "id": company_id})
                sys_db.commit()
                sys_db.close()
            except Exception:
                pass  # logo_url might not exist yet in system_companies

            # Commit to company db
            db.commit()
            return {"success": True, "logo_url": logo_url}
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error uploading logo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload: {str(e)}")
