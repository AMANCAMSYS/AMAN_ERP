"""
AMAN ERP - Company Settings Router
Handles dynamic key-value settings for each company.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from database import get_company_db, get_db_connection
from routers.auth import get_current_user, UserResponse
from utils.permissions import require_permission
from schemas.settings import SettingsUpdateRequest
from utils.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["إعدادات الشركة"])

# Permission Mapping for Settings Keys
# Keys starting with prefix -> require permission
PERMISSION_MAPPING = {
    # Prefix : Required Permission (or one of them)
    "hr_": "hr.view",
    "payroll_": "hr.view",
    "sales_": "sales.view",
    "crm_": "sales.view", 
    "purchases_": "buying.view",
    "inventory_": "stock.view_cost", # Sensitive inventory settings
    "stock_": "stock.view",
    "financial_": "accounting.view",
    "vat_": "accounting.view",
    "fiscal_": "accounting.view",
    "accounting_": "accounting.view",
    "security_": "admin", # Security settings are sensitive
    "smtp_": "admin",      # SMTP creds are sensitive
    "sms_": "admin",       # API keys
    "zatca_": "admin",     # Compliance sensitive
    "project_": "projects.view", # Assuming projects module
    "expense_": "treasury.view",
    "workflow_": "admin", # Workflow rules often involve financial limits
    "audit_": "audit.view",
    "pos_": "pos.view", # Assuming pos role, otherwise settings.view
}

@router.get("/", response_model=Dict[str, Any], dependencies=[Depends(require_permission("settings.view"))])
def get_company_settings(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all company settings as a dictionary.
    Filtered by user permissions.
    """
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")
        
    db = get_db_connection(company_id)
    
    try:
        # Try cache first
        cache_key = f"company_settings:{company_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            raw_settings = cached_result
        else:
            result = db.execute(text("SELECT setting_key, setting_value FROM company_settings")).fetchall()
            raw_settings = {row.setting_key: row.setting_value for row in result}
            cache.set(cache_key, raw_settings, expire=3600)

        # Check permissions
        is_admin = current_user.role in ["system_admin", "company_admin", "admin", "superuser"]
        perms = current_user.permissions or []
        has_all_perms = "*" in perms
        can_view_all_settings = is_admin or has_all_perms or "settings.view" in perms or "settings.manage" in perms
        
        settings_dict = {}
        for key, value in raw_settings.items():
            # If user has full access, include everything
            if can_view_all_settings:
                settings_dict[key] = value
                continue
                
            # Otherwise, check granular permissions
            allowed = True
            
            # Default: specific keys might need check. 
            # If key matches a known prefix, check for permission
            for prefix, required_perm in PERMISSION_MAPPING.items():
                if key.startswith(prefix):
                    # Check if user has this permission (or wildcard of it)
                    # e.g. required='hr.view', user has 'hr.*' -> OK
                    has_perm = required_perm in perms
                    if not has_perm:
                        # Check wildcard parent
                        parts = required_perm.split('.')
                        if len(parts) > 1 and f"{parts[0]}.*" in perms:
                            has_perm = True
                    
                    if not has_perm:
                        allowed = False
                    break # Matched prefix, stop checking others
            
            # If allowed, add to result
            if allowed:
                # Basic non-sensitive settings (branding, etc) are allowed by default if they don't match restricted prefixes
                settings_dict[key] = value

        return settings_dict
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return {} 
    finally:
        db.close()

@router.post("/bulk", status_code=status.HTTP_200_OK, dependencies=[Depends(require_permission("settings.manage"))])
def update_settings_bulk(
    request: SettingsUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update or create multiple settings at once.
    """
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")
        
    # Authorization Check
    is_admin = current_user.role in ["system_admin", "company_admin", "admin", "superuser"]
    perms = current_user.permissions or []
    has_all_perms = "*" in perms
    # settings.manage allows updating EVERYTHING in this simple implementation? 
    # Or should it be restricted too? Let's say settings.manage is super-power for settings.
    can_manage_all = is_admin or has_all_perms or "settings.manage" in perms
    
    if can_manage_all:
        pass # Allow all
    else:
        # Check each key against user permissions
        for key in request.settings.keys():
            required_perm = None
            
            # Map keys to manage permissions
            if key.startswith("hr_") or key.startswith("payroll_"):
                required_perm = "hr.manage"
            elif key.startswith("sales_") or key.startswith("crm_"):
                required_perm = "sales.manage"
            elif key.startswith("purchases_"):
                required_perm = "buying.manage"
            elif key.startswith("inventory_") or key.startswith("stock_"):
                required_perm = "stock.manage"
            elif key.startswith("financial_") or key.startswith("vat_") or key.startswith("fiscal_") or key.startswith("accounting_"):
                required_perm = "accounting.manage"
            elif key.startswith("project_"):
                required_perm = "projects.manage"
            elif key.startswith("expense_"):
                required_perm = "treasury.manage"
            elif key.startswith("pos_"):
                required_perm = "pos.manage"
            elif key.startswith("audit_"):
                required_perm = "audit.manage"
            elif key.startswith("branches_") or key.startswith("multi_branch_"): 
                required_perm = "branches.manage"
            
            # Sensitive keys - must be admin (already checked above, so if we are here, fail)
            elif any(key.startswith(p) for p in ["security_", "smtp_", "sms_", "zatca_", "workflow_"]):
                 raise HTTPException(status_code=403, detail=f"Not authorized to update sensitive setting: {key}")
            
            # General fallback
            else:
                # If it's a general setting (logo, company name, etc), we might require settings.manage
                # But we are in the 'else' block where user DOES NOT have settings.manage.
                # So they cannot update unclassified/general settings.
                 raise HTTPException(status_code=403, detail=f"Not authorized to update setting: {key}")
            
            # Check if user has the specific required permission
            has_perm = required_perm in perms
            if not has_perm:
                # Check wildcard
                parts = required_perm.split('.')
                if len(parts) > 1 and f"{parts[0]}.*" in perms:
                    has_perm = True
            
            if not has_perm:
                raise HTTPException(status_code=403, detail=f"Missing permission {required_perm} for setting {key}")
    
    db = get_db_connection(company_id)
    try:
        # Upsert logic — atomic ON CONFLICT
        for key, value in request.settings.items():
            value_str = str(value) if value is not None else ""
            db.execute(
                text("INSERT INTO company_settings (setting_key, setting_value) VALUES (:key, :value) ON CONFLICT (setting_key) DO UPDATE SET setting_value = :value, updated_at = CURRENT_TIMESTAMP"),
                {"key": key, "value": value_str}
            )
        
        db.commit()
        
        # ── إذا تم تغيير نوع النشاط → زرع شجرة الحسابات المتخصصة ──
        if "industry_type" in request.settings:
            industry_key = request.settings["industry_type"]
            try:
                from services.industry_coa_templates import seed_industry_coa
                # normalize_industry_key is called inside seed_industry_coa
                coa_result = seed_industry_coa(db, industry_key, replace_existing=False)
                logger.info(f"📊 COA seeded for industry '{industry_key}': {coa_result}")
            except Exception as coa_err:
                logger.warning(f"⚠️ COA seeding skipped: {coa_err}")
        
        # Invalidate cache
        cache.delete(f"company_settings:{company_id}")
        
        return {"success": True, "message": "Settings updated successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
@router.post("/test-email", status_code=status.HTTP_200_OK, dependencies=[Depends(require_permission("settings.manage"))])
def test_email_connection(
    request: SettingsUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Test SMTP connection using provided settings.
    """
    import smtplib
    from email.mime.text import MIMEText
    
    settings = request.settings
    host = settings.get("smtp_host")
    port = int(settings.get("smtp_port", 587))
    user = settings.get("smtp_user")
    password = settings.get("smtp_pass")

    if not host or not user or not password:
        raise HTTPException(status_code=400, detail="Missing SMTP configuration")
        
    try:
        # Simulate connection if it's a known fake host or just try real connection
        if host == "smtp.example.com":
             return {"success": True, "message": "Simulated connection successful"}
             
        # Real connection attempt (with timeout)
        server = smtplib.SMTP(host, port, timeout=5)
        server.starttls()
        server.login(user, password)
        server.quit()
        
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@router.post("/generate-csid", status_code=status.HTTP_200_OK, dependencies=[Depends(require_permission("settings.manage"))])
def generate_csid(
    request: SettingsUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Simulate ZATCA CSID generation.
    """
    settings = request.settings
    otp = settings.get("zatca_otp")
    common_name = settings.get("zatca_csr_common_name")
    
    if not otp or not common_name:
         raise HTTPException(status_code=400, detail="Missing OTP or Organization Name")
         
    # Simulation Logic
    import random
    if otp == "000000":
         raise HTTPException(status_code=400, detail="Invalid OTP")
         
    return {
        "success": True, 
        "message": "CSID generated successfully", 
        "csid": f"CSID-{random.randint(1000,9999)}-{common_name}"
    }


