"""
AMAN ERP - Roles Management Router
API endpoints for managing roles and permissions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel
import logging

from database import get_db_connection
from routers.auth import get_current_user, UserResponse
from utils.permissions import require_permission
from schemas.roles import RoleCreate, RoleUpdate

router = APIRouter(prefix="/roles", tags=["إدارة الأدوار"])
logger = logging.getLogger(__name__)


# --- Available Permissions ---
AVAILABLE_PERMISSIONS = [
    # Sales
    {"key": "sales.view", "label_ar": "عرض المبيعات", "label_en": "View Sales"},
    {"key": "sales.create", "label_ar": "إنشاء فواتير", "label_en": "Create Invoices"},
    {"key": "sales.edit", "label_ar": "تعديل فواتير", "label_en": "Edit Invoices"},
    {"key": "sales.delete", "label_ar": "حذف فواتير", "label_en": "Delete Invoices"},
    {"key": "sales.reports", "label_ar": "تقارير المبيعات", "label_en": "Sales Reports"},
    # Buying
    {"key": "buying.view", "label_ar": "عرض المشتريات", "label_en": "View Purchases"},
    {"key": "buying.create", "label_ar": "إنشاء فواتير", "label_en": "Create Purchase Invoices"},
    {"key": "buying.edit", "label_ar": "تعديل فواتير", "label_en": "Edit Purchase Invoices"},
    {"key": "buying.delete", "label_ar": "حذف فواتير", "label_en": "Delete Purchase Invoices"},
    {"key": "buying.reports", "label_ar": "تقارير المشتريات", "label_en": "Purchase Reports"},
    {"key": "buying.approve", "label_ar": "اعتماد أوامر الشراء", "label_en": "Approve Purchase Orders"},
    {"key": "buying.receive", "label_ar": "استلام البضائع", "label_en": "Receive Goods"},
    # Stock
    {"key": "stock.view", "label_ar": "عرض المخزون", "label_en": "View Stock"},
    {"key": "stock.view_cost", "label_ar": "عرض سعر التكلفة", "label_en": "View Cost Price"},
    {"key": "stock.adjustment", "label_ar": "تسوية المخزون", "label_en": "Stock Adjustment"},
    {"key": "stock.transfer", "label_ar": "نقل المخزون", "label_en": "Stock Transfer"},
    {"key": "stock.manage", "label_ar": "إدارة المخازن", "label_en": "Manage Stock/Warehouses"},
    {"key": "stock.reports", "label_ar": "تقارير المخزون", "label_en": "Stock Reports"},
    # Products
    {"key": "products.view", "label_ar": "عرض المنتجات", "label_en": "View Products"},
    {"key": "products.create", "label_ar": "إنشاء منتج", "label_en": "Create Products"},
    {"key": "products.edit", "label_ar": "تعديل منتج", "label_en": "Edit Products"},
    {"key": "products.delete", "label_ar": "حذف منتج", "label_en": "Delete Products"},
    # Inventory
    {"key": "inventory.view", "label_ar": "عرض الجرد", "label_en": "View Inventory"},
    {"key": "inventory.delete", "label_ar": "حذف من الجرد", "label_en": "Delete Inventory"},
    # Accounting
    {"key": "accounting.view", "label_ar": "عرض المحاسبة", "label_en": "View Accounting"},
    {"key": "accounting.edit", "label_ar": "تعديل المحاسبة", "label_en": "Edit Accounting"},
    {"key": "accounting.manage", "label_ar": "إدارة الحسابات", "label_en": "Manage Accounts"},
    {"key": "accounting.budgets.view", "label_ar": "عرض الموازنات", "label_en": "View Budgets"},
    {"key": "accounting.budgets.manage", "label_ar": "إدارة الموازنات", "label_en": "Manage Budgets"},
    # Reports
    {"key": "reports.view", "label_ar": "عرض التقارير", "label_en": "View Reports"},
    {"key": "reports.financial", "label_ar": "التقارير المالية", "label_en": "Financial Reports"},
    # HR
    {"key": "hr.view", "label_ar": "عرض الموارد البشرية", "label_en": "View HR"},
    {"key": "hr.manage", "label_ar": "إدارة الموارد البشرية", "label_en": "Manage HR"},
    {"key": "hr.reports", "label_ar": "تقارير الموارد البشرية", "label_en": "HR Reports"},
    {"key": "hr.attendance.view", "label_ar": "عرض الحضور والانصراف", "label_en": "View Attendance"},
    {"key": "hr.attendance.manage", "label_ar": "إدارة الحضور (تعديل)", "label_en": "Manage Attendance"},
    {"key": "hr.loans.view", "label_ar": "عرض القروض والسلف", "label_en": "View Loans"},
    {"key": "hr.loans.manage", "label_ar": "إدارة القروض", "label_en": "Manage Loans"},
    {"key": "hr.leaves.manage", "label_ar": "إدارة الإجازات", "label_en": "Manage Leaves"},
    # Assets
    {"key": "assets.view", "label_ar": "عرض الأصول الثابتة", "label_en": "View Fixed Assets"},
    {"key": "assets.create", "label_ar": "إضافة أصل", "label_en": "Add Asset"},
    {"key": "assets.manage", "label_ar": "إدارة الأصول", "label_en": "Manage Assets"},
    # Treasury & Reconciliation
    {"key": "treasury.view", "label_ar": "عرض الخزينة والبنوك", "label_en": "View Treasury"},
    {"key": "treasury.create", "label_ar": "إنشاء عمليات خزينة", "label_en": "Create Treasury Transactions"},
    {"key": "treasury.edit", "label_ar": "تعديل عمليات خزينة", "label_en": "Edit Treasury Transactions"},
    {"key": "treasury.delete", "label_ar": "حذف عمليات خزينة", "label_en": "Delete Treasury Transactions"},
    {"key": "treasury.manage", "label_ar": "إدارة الخزينة", "label_en": "Manage Treasury"},
    {"key": "reconciliation.view", "label_ar": "عرض تسوية البنك", "label_en": "View Reconciliation"},
    {"key": "reconciliation.create", "label_ar": "إنشاء تسوية", "label_en": "Create Reconciliation"},
    {"key": "reconciliation.approve", "label_ar": "اعتماد تسوية", "label_en": "Approve Reconciliation"},
    {"key": "notifications.view", "label_ar": "عرض التنبيهات", "label_en": "View Notifications"},
    # Cost Centers
    {"key": "accounting.cost_centers.view", "label_ar": "عرض مراكز التكلفة", "label_en": "View Cost Centers"},
    {"key": "accounting.cost_centers.manage", "label_ar": "إدارة مراكز التكلفة", "label_en": "Manage Cost Centers"},
    # Audit
    {"key": "audit.view", "label_ar": "عرض سجلات المراقبة", "label_en": "View Audit Logs"},
    {"key": "audit.manage", "label_ar": "إدارة سجلات المراقبة", "label_en": "Manage Audit Logs"},
    # Admin
    {"key": "admin.users", "label_ar": "إدارة المستخدمين", "label_en": "Manage Users"},
    {"key": "admin.roles", "label_ar": "إدارة الأدوار", "label_en": "Manage Roles"},
    {"key": "admin.branches", "label_ar": "إدارة الفروع", "label_en": "Manage Branches"},
    {"key": "admin.branches.manage", "label_ar": "إدارة الفروع (تعديل/حذف)", "label_en": "Manage Branches (Edit/Delete)"},
    {"key": "admin.companies", "label_ar": "إدارة الشركات (SaaS)", "label_en": "Manage Companies (SaaS)"},
    {"key": "branches.view", "label_ar": "عرض الفروع", "label_en": "View Branches"},
    {"key": "admin", "label_ar": "صلاحية إدارة النظام", "label_en": "System Admin Access"},
    # Settings
    {"key": "settings.view", "label_ar": "عرض الإعدادات", "label_en": "View Settings"},
    {"key": "settings.manage", "label_ar": "تعديل الإعدادات (عام)", "label_en": "Manage Settings (General)"},
    {"key": "settings.edit", "label_ar": "تعديل الإعدادات", "label_en": "Edit Settings"},
    # Contracts
    {"key": "contracts.view", "label_ar": "عرض العقود", "label_en": "View Contracts"},
    {"key": "contracts.create", "label_ar": "إنشاء عقود", "label_en": "Create Contracts"},
    {"key": "contracts.edit", "label_ar": "تعديل عقود", "label_en": "Edit Contracts"},
    {"key": "contracts.manage", "label_ar": "إدارة العقود", "label_en": "Manage Contracts"},
    # POS
    {"key": "pos.view", "label_ar": "عرض نقطة البيع", "label_en": "View POS"},
    {"key": "pos.create", "label_ar": "إنشاء طلبات نقطة البيع", "label_en": "Create POS Orders"},
    {"key": "pos.manage", "label_ar": "إدارة نقطة البيع", "label_en": "Manage POS"},
    {"key": "pos.sessions", "label_ar": "إدارة جلسات نقطة البيع", "label_en": "Manage POS Sessions"},
    {"key": "pos.returns", "label_ar": "مرتجعات نقطة البيع", "label_en": "POS Returns"},
    # Projects
    {"key": "projects.view", "label_ar": "عرض المشاريع", "label_en": "View Projects"},
    {"key": "projects.create", "label_ar": "إنشاء مشاريع", "label_en": "Create Projects"},
    {"key": "projects.edit", "label_ar": "تعديل مشاريع", "label_en": "Edit Projects"},
    {"key": "projects.delete", "label_ar": "حذف مشاريع", "label_en": "Delete Projects"},
    {"key": "projects.manage", "label_ar": "إدارة المشاريع", "label_en": "Manage Projects"},
    # Currencies
    {"key": "currencies.view", "label_ar": "عرض العملات", "label_en": "View Currencies"},
    {"key": "currencies.manage", "label_ar": "إدارة العملات", "label_en": "Manage Currencies"},
    # Taxes
    {"key": "taxes.view", "label_ar": "عرض الضرائب", "label_en": "View Taxes"},
    {"key": "taxes.manage", "label_ar": "إدارة الضرائب", "label_en": "Manage Taxes"},
    # Manufacturing
    {"key": "manufacturing.view", "label_ar": "عرض التصنيع", "label_en": "View Manufacturing"},
    {"key": "manufacturing.create", "label_ar": "إنشاء أوامر تصنيع", "label_en": "Create Production Orders"},
    {"key": "manufacturing.manage", "label_ar": "إدارة التصنيع", "label_en": "Manage Manufacturing"},
    # Expenses
    {"key": "expenses.view", "label_ar": "عرض المصاريف", "label_en": "View Expenses"},
    {"key": "expenses.create", "label_ar": "إنشاء مصاريف", "label_en": "Create Expenses"},
    {"key": "expenses.edit", "label_ar": "تعديل مصاريف", "label_en": "Edit Expenses"},
    {"key": "expenses.delete", "label_ar": "حذف مصاريف", "label_en": "Delete Expenses"},
    {"key": "expenses.approve", "label_ar": "اعتماد مصاريف", "label_en": "Approve Expenses"},
    # Dashboard
    {"key": "dashboard.view", "label_ar": "عرض لوحة المعلومات", "label_en": "View Dashboard"},
    # Approvals (Phase 7)
    {"key": "approvals.view", "label_ar": "عرض الاعتمادات", "label_en": "View Approvals"},
    {"key": "approvals.manage", "label_ar": "إدارة سلاسل الاعتماد", "label_en": "Manage Approval Workflows"},
    {"key": "approvals.create", "label_ar": "إنشاء طلبات اعتماد", "label_en": "Create Approval Requests"},
    {"key": "approvals.approve", "label_ar": "اعتماد ورفض الطلبات", "label_en": "Approve/Reject Requests"},
    # Security (Phase 7)
    {"key": "security.view", "label_ar": "عرض إعدادات الأمان", "label_en": "View Security Settings"},
    {"key": "security.manage", "label_ar": "إدارة السياسات الأمنية", "label_en": "Manage Security Policies"},
    # Data Import (Phase 7)
    {"key": "data_import.view", "label_ar": "عرض استيراد البيانات", "label_en": "View Data Import"},
    {"key": "data_import.manage", "label_ar": "تنفيذ استيراد البيانات", "label_en": "Manage Data Import"},
    {"key": "data_import.create", "label_ar": "رفع ملفات الاستيراد", "label_en": "Upload Import Files"},
    # Reports extended
    {"key": "reports.create", "label_ar": "إنشاء تقارير مخصصة", "label_en": "Create Custom Reports"},
    {"key": "reports.delete", "label_ar": "حذف تقارير", "label_en": "Delete Reports"},
    # Settings extended
    {"key": "settings.create", "label_ar": "إضافة إعدادات", "label_en": "Create Settings"},
    {"key": "settings.delete", "label_ar": "حذف إعدادات", "label_en": "Delete Settings"},
    # HR Payroll
    {"key": "hr.payroll.view", "label_ar": "عرض الرواتب", "label_en": "View Payroll"},
    {"key": "hr.payroll.manage", "label_ar": "إدارة الرواتب", "label_en": "Manage Payroll"},
    # Manufacturing extended
    {"key": "manufacturing.delete", "label_ar": "حذف بيانات التصنيع", "label_en": "Delete Manufacturing Data"},
    {"key": "manufacturing.reports", "label_ar": "تقارير التصنيع", "label_en": "Manufacturing Reports"},
]


# --- Default Roles ---
DEFAULT_ROLES = {
    "admin": ["*"],
    "manager": [
        "sales.*", "buying.*", "inventory.*", "stock.*",
        "treasury.view", "treasury.create", "treasury.edit",
        "reports.view", "reports.create", "reports.financial",
        "hr.view", "hr.reports", "hr.payroll.view",
        "products.*", "contracts.*", "pos.*",
        "manufacturing.view", "manufacturing.create",
        "assets.view", "assets.create",
        "approvals.view", "approvals.create", "approvals.approve",
        "security.view", "data_import.view",
        "expenses.view", "expenses.approve",
        "projects.view", "projects.create",
        "taxes.view", "currencies.view",
        "reconciliation.view", "dashboard.view"
    ],
    "accountant": [
        "accounting.*", "reports.financial", "reports.view",
        "treasury.*", "reconciliation.*",
        "sales.view", "buying.view", "contracts.view",
        "currencies.*", "taxes.*",
        "expenses.view", "expenses.approve",
        "assets.view", "hr.payroll.view", "dashboard.view"
    ],
    "sales": [
        "sales.*", "products.view", "stock.view",
        "pos.*", "contracts.view", "contracts.create",
        "reports.view", "approvals.create", "dashboard.view"
    ],
    "purchasing": [
        "buying.*", "products.view", "stock.view",
        "inventory.view", "reports.view",
        "approvals.create", "dashboard.view"
    ],
    "inventory": [
        "inventory.*", "stock.*", "products.*",
        "reports.view", "dashboard.view"
    ],
    "hr_manager": [
        "hr.*", "hr.payroll.*",
        "expenses.view", "reports.view", "dashboard.view"
    ],
    "cashier": [
        "pos.*", "sales.view", "products.view", "stock.view",
        "dashboard.view"
    ],
    "manufacturing_user": [
        "manufacturing.*", "products.view", "stock.view",
        "inventory.view", "dashboard.view"
    ],
    "viewer": [
        "sales.view", "buying.view", "stock.view", "products.view",
        "accounting.view", "hr.view", "reports.view",
        "treasury.view", "manufacturing.view", "dashboard.view"
    ]
}


# --- Endpoints ---

@router.get("/permissions", response_model=List[dict], dependencies=[Depends(require_permission("admin.roles"))])
def list_available_permissions(current_user: UserResponse = Depends(get_current_user)):
    """عرض قائمة الصلاحيات المتاحة"""
    return AVAILABLE_PERMISSIONS


@router.get("/", response_model=List[dict], dependencies=[Depends(require_permission("admin.roles"))])
def list_roles(
    company_id: Optional[str] = None,
    current_user: Any = Depends(get_current_user)
):
    """عرض قائمة الأدوار"""
    target_company_id = company_id or getattr(current_user, 'company_id', None)
    if not target_company_id:
        return []

    db = get_db_connection(target_company_id)
    try:
        result = db.execute(text("""
            SELECT id, role_name, role_name_ar, description, permissions, 
                   is_system_role, created_at
            FROM roles
            ORDER BY is_system_role DESC, role_name
        """)).fetchall()
        
        roles = []
        for row in result:
            roles.append({
                "id": row.id,
                "role_name": row.role_name,
                "role_name_ar": row.role_name_ar,
                "description": row.description,
                "permissions": row.permissions or [],
                "is_system_role": row.is_system_role,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        return roles
    finally:
        db.close()


@router.get("/{role_id}", response_model=dict, dependencies=[Depends(require_permission("admin.roles"))])
def get_role(
    role_id: int, 
    company_id: Optional[str] = None,
    current_user: Any = Depends(get_current_user)
):
    """جلب تفاصيل دور محدد"""
    target_company_id = company_id or getattr(current_user, 'company_id', None)
    if not target_company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")

    db = get_db_connection(target_company_id)
    try:
        row = db.execute(text("""
            SELECT id, role_name, role_name_ar, description, permissions, 
                   is_system_role, created_at
            FROM roles WHERE id = :id
        """), {"id": role_id}).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="الدور غير موجود")
        
        return {
            "id": row.id,
            "role_name": row.role_name,
            "role_name_ar": row.role_name_ar,
            "description": row.description,
            "permissions": row.permissions or [],
            "is_system_role": row.is_system_role,
            "created_at": row.created_at.isoformat() if row.created_at else None
        }
    finally:
        db.close()


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("admin.roles"))])
def create_role(
    role: RoleCreate, 
    company_id: Optional[str] = None,
    current_user: Any = Depends(get_current_user)
):
    """إنشاء دور جديد"""
    target_company_id = company_id or getattr(current_user, 'company_id', None)
    if not target_company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")

    db = get_db_connection(target_company_id)
    try:
        # Check name uniqueness
        exists = db.execute(text("SELECT 1 FROM roles WHERE role_name = :name"), {"name": role.role_name}).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail="اسم الدور موجود بالفعل")
        
        import json
        result = db.execute(text("""
            INSERT INTO roles (role_name, role_name_ar, description, permissions, is_system_role)
            VALUES (:name, :name_ar, :desc, :perms, FALSE)
            RETURNING id
        """), {
            "name": role.role_name,
            "name_ar": role.role_name_ar,
            "desc": role.description,
            "perms": json.dumps(role.permissions)
        }).fetchone()
        
        db.commit()
        return {"id": result[0], "message": "تم إنشاء الدور بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/{role_id}", dependencies=[Depends(require_permission("admin.roles"))])
def update_role(
    role_id: int, 
    role: RoleUpdate, 
    company_id: Optional[str] = None,
    current_user: Any = Depends(get_current_user)
):
    """تحديث دور"""
    target_company_id = company_id or getattr(current_user, 'company_id', None)
    if not target_company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")

    db = get_db_connection(target_company_id)
    try:
        # Check if role exists and is not system role
        existing = db.execute(text("SELECT is_system_role, role_name FROM roles WHERE id = :id"), {"id": role_id}).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="الدور غير موجود")
        
        if existing.is_system_role:
            raise HTTPException(status_code=400, detail="لا يمكن تعديل الأدوار الافتراضية للنظام")
        
        # Build update query dynamically
        updates = []
        params = {"id": role_id}
        
        if role.role_name is not None:
            updates.append("role_name = :name")
            params["name"] = role.role_name
        
        if role.role_name_ar is not None:
            updates.append("role_name_ar = :name_ar")
            params["name_ar"] = role.role_name_ar
        
        if role.description is not None:
            updates.append("description = :desc")
            params["desc"] = role.description
        
        if role.permissions is not None:
            import json
            updates.append("permissions = :perms")
            params["perms"] = json.dumps(role.permissions)
        
        if updates:
            query = f"UPDATE roles SET {', '.join(updates)} WHERE id = :id"
            db.execute(text(query), params)
            db.commit()
        
        return {"message": "تم تحديث الدور بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{role_id}", dependencies=[Depends(require_permission("admin.roles"))])
def delete_role(
    role_id: int, 
    company_id: Optional[str] = None,
    current_user: Any = Depends(get_current_user)
):
    """حذف دور"""
    target_company_id = company_id or getattr(current_user, 'company_id', None)
    if not target_company_id:
        raise HTTPException(status_code=400, detail="Company ID missing")

    db = get_db_connection(target_company_id)
    try:
        # Check if role exists and is not system role
        existing = db.execute(text("SELECT is_system_role FROM roles WHERE id = :id"), {"id": role_id}).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="الدور غير موجود")
        
        if existing.is_system_role:
            raise HTTPException(status_code=400, detail="لا يمكن حذف الأدوار الافتراضية للنظام")
        
        # Check if any users are using this role
        usage = db.execute(text("SELECT COUNT(*) FROM company_users WHERE role = (SELECT role_name FROM roles WHERE id = :id)"), {"id": role_id}).scalar()
        if usage > 0:
            raise HTTPException(status_code=400, detail=f"لا يمكن حذف الدور لأنه مستخدم من قبل {usage} مستخدم")
        
        db.execute(text("DELETE FROM roles WHERE id = :id"), {"id": role_id})
        db.commit()
        
        return {"message": "تم حذف الدور بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
