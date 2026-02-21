"""
AMAN ERP - Permission Utilities
Server-side permission enforcement for API endpoints.
PERM-001: Field-Level Permissions
PERM-002: Warehouse-Level Permissions
PERM-003: Cost-Center-Level Permissions
PERM-004: Permission Audit Logging
"""

from fastapi import Depends, HTTPException, status, Request
from functools import wraps
from typing import List, Union, Any, Optional, Set, Dict
import logging
import json

from routers.auth import get_current_user

logger = logging.getLogger(__name__)

# Permission aliases: if a user has the KEY permission, they implicitly also have the VALUE permissions.
# This bridges "umbrella" permissions to the specific ones actually checked by routers.
PERMISSION_ALIASES: Dict[str, List[str]] = {
    # inventory.* is an umbrella for stock + products
    "inventory.view":   ["stock.view", "products.view"],
    "inventory.delete": ["products.delete", "stock.adjustment"],
    "inventory.*":      ["stock.view", "stock.adjustment", "stock.transfer", "stock.manage",
                         "products.view", "products.create", "products.edit", "products.delete"],
    # projects.manage covers all project CRUD
    "projects.manage":  ["projects.view", "projects.create", "projects.edit", "projects.delete"],
    # admin.users is an alias that grants user-related admin access
    "admin.users":      ["admin.roles", "settings.view"],
    # sales.edit/delete — route to the actual enforced keys
    "sales.edit":       ["sales.create"],
    "sales.delete":     ["sales.create"],
    # buying.reports routes to buying.view for now
    "buying.reports":   ["buying.view"],
    # hr.reports routes to hr.view
    "hr.reports":       ["hr.view"],
}


def check_permission(user_permissions: list, required_permission: str) -> bool:
    """
    Check if user has the required permission.
    Supports:
    - Exact match: 'products.create'
    - Wildcard: '*' (full access)
    - Section wildcard: 'products.*'
    - Permission aliases (PERMISSION_ALIASES above)
    """
    if not user_permissions:
        return False
    
    # Full admin access
    if "*" in user_permissions:
        return True
    
    # Exact match
    if required_permission in user_permissions:
        return True
    
    # Section wildcard (e.g., 'products.*' matches 'products.create')
    req_parts = required_permission.split(".")
    if len(req_parts) >= 1:
        section_wildcard = f"{req_parts[0]}.*"
        if section_wildcard in user_permissions:
            return True

    # Alias expansion: check if any user permission is an alias that covers required_permission
    for user_perm in user_permissions:
        implied = PERMISSION_ALIASES.get(user_perm, [])
        if required_permission in implied:
            return True
    
    return False


def require_permission(permission: Union[str, List[str]]):
    """
    FastAPI dependency that checks if the current user has the required permission.
    Usage:
        @router.delete("/products/{id}", dependencies=[Depends(require_permission("products.delete"))])
        def delete_product(id: int, ...):
            ...
    
    Or for multiple permissions (user needs ANY of them):
        @router.post("/...", dependencies=[Depends(require_permission(["sales.create", "admin"]))])
    """
    async def permission_checker(current_user: Union[dict, Any] = Depends(get_current_user)):
        # Get user permissions
        if isinstance(current_user, dict):
            user_perms = current_user.get("permissions", [])
            username = current_user.get("username", "unknown")
        else:
            user_perms = getattr(current_user, 'permissions', []) or []
            username = getattr(current_user, 'username', 'unknown')
        
        # If permission is a string, convert to list
        required_perms = [permission] if isinstance(permission, str) else permission
        
        # Check if user has ANY of the required permissions
        has_permission = any(check_permission(user_perms, perm) for perm in required_perms)
        
        if not has_permission:
            logger.warning(f"🚫 Permission denied: User {username} tried to access {permission}")
            # PERM-004: Log denied access
            _log_permission_denied(current_user, permission)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"ليس لديك صلاحية لتنفيذ هذا الإجراء: {permission}"
            )
        
        return current_user
    
    return permission_checker


def validate_branch_access(current_user: dict, requested_branch_id: Union[int, None, str] = None) -> Union[int, None]:
    """
    Enforces branch access scope.
    """
    # Handle both dict and Pydantic model
    if isinstance(current_user, dict):
        allowed_branches = current_user.get("allowed_branches", [])
        role = current_user.get("role")
        permissions = current_user.get("permissions", [])
    else:
        allowed_branches = getattr(current_user, "allowed_branches", [])
        role = getattr(current_user, "role", None)
        permissions = getattr(current_user, "permissions", [])

    # CRITICAL FIX: Admins have full access regardless of allowed_branches
    if role in ['admin', 'system_admin', 'superuser'] or "*" in permissions:
        if not requested_branch_id or requested_branch_id == "":
            return None
        try:
            return int(requested_branch_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid branch ID")
    
    # If no restrictions, return as is (handling empty string/None)
    if not allowed_branches:
        if requested_branch_id == "": return None 
        return int(requested_branch_id) if requested_branch_id else None

    # Handle requested_branch_id
    if requested_branch_id in [None, ""]:
        # User requested ALL, but is restricted.
        if len(allowed_branches) == 1:
            return allowed_branches[0] # Auto-select the only allowed branch
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="يرجى تحديد الفرع (لديك صلاحية على فروع محددة فقط)"
            )
            
    # Cast to int for comparison
    try:
        rid = int(requested_branch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid branch ID")

    if rid not in allowed_branches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="ليس لديك صلاحية للوصول إلى بيانات هذا الفرع"
        )
    
    return rid


# ===================== PERM-001: Field-Level Permissions =====================

# Default hidden fields by role (can be overridden per company via DB)
DEFAULT_FIELD_RESTRICTIONS = {
    "salesperson": {
        "products": ["cost_price", "average_cost", "last_purchase_price"],
        "invoice_lines": ["cost_price", "profit_margin"],
        "inventory": ["unit_cost", "total_cost"],
    },
    "accountant": {
        "employees": ["salary", "bank_account", "iban", "gosi_number"],
        "payroll_entries": ["*"],  # Hide entire payroll details
    },
    "warehouse_keeper": {
        "products": ["cost_price", "average_cost", "last_purchase_price", "selling_price"],
        "invoices": ["*"],
    }
}


def get_field_restrictions(current_user, company_conn=None) -> Dict[str, List[str]]:
    """
    PERM-001: Get field-level restrictions for current user.
    Returns dict of {resource: [hidden_fields]}
    """
    if isinstance(current_user, dict):
        role = current_user.get("role")
        permissions = current_user.get("permissions", [])
        user_id = current_user.get("id")
    else:
        role = getattr(current_user, "role", None)
        permissions = getattr(current_user, "permissions", [])
        user_id = getattr(current_user, "id", None)

    # Admins have no restrictions
    if role in ['admin', 'system_admin', 'superuser'] or "*" in (permissions or []):
        return {}

    restrictions = {}

    # Check DB for custom field restrictions (per-user or per-role)
    if company_conn and user_id:
        try:
            # Check user-specific restrictions first
            row = company_conn.execute(
                __import__('sqlalchemy', fromlist=['text']).text(
                    "SELECT field_restrictions FROM user_field_permissions WHERE user_id = :uid"
                ), {"uid": user_id}
            ).scalar()
            if row:
                return json.loads(row) if isinstance(row, str) else row
            
            # Fallback to role-based restrictions from DB
            if role:
                row = company_conn.execute(
                    __import__('sqlalchemy', fromlist=['text']).text(
                        "SELECT field_restrictions FROM role_field_permissions WHERE role_name = :role"
                    ), {"role": role}
                ).scalar()
                if row:
                    return json.loads(row) if isinstance(row, str) else row
        except Exception:
            pass  # Table might not exist yet

    # Fallback to default restrictions
    return DEFAULT_FIELD_RESTRICTIONS.get(role, {})


def filter_fields(data: Union[dict, list], resource: str, current_user, company_conn=None):
    """
    PERM-001: Filter out restricted fields from response data.
    Usage in endpoint:
        result = filter_fields(product_dict, "products", current_user, db)
    """
    restrictions = get_field_restrictions(current_user, company_conn)
    hidden_fields = restrictions.get(resource, [])

    if not hidden_fields:
        return data

    if hidden_fields == ["*"]:
        # Hide entire resource
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"ليس لديك صلاحية لعرض بيانات {resource}"
        )

    if isinstance(data, list):
        return [{k: v for k, v in item.items() if k not in hidden_fields}
                for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        return {k: v for k, v in data.items() if k not in hidden_fields}

    return data


# ===================== PERM-002: Warehouse-Level Permissions =====================

def get_allowed_warehouses(current_user, company_conn=None) -> Optional[List[int]]:
    """
    PERM-002: Get list of warehouse IDs the user can access.
    Returns None if user has access to ALL warehouses (admin).
    Returns [] if user has NO warehouse access.
    Returns [1, 2, 3] if restricted to specific warehouses.
    """
    if isinstance(current_user, dict):
        role = current_user.get("role")
        permissions = current_user.get("permissions", [])
        user_id = current_user.get("id")
    else:
        role = getattr(current_user, "role", None)
        permissions = getattr(current_user, "permissions", [])
        user_id = getattr(current_user, "id", None)

    # Admins have access to all warehouses
    if role in ['admin', 'system_admin', 'superuser'] or "*" in (permissions or []):
        return None  # None = unrestricted

    if not company_conn or not user_id:
        return None

    try:
        from sqlalchemy import text
        rows = company_conn.execute(text(
            "SELECT warehouse_id FROM user_warehouses WHERE user_id = :uid"
        ), {"uid": user_id}).fetchall()

        if not rows:
            return None  # No restrictions defined = access all

        return [r[0] for r in rows]
    except Exception:
        return None  # Table might not exist yet


def build_warehouse_filter(current_user, company_conn=None, 
                           warehouse_column: str = "warehouse_id",
                           table_alias: str = "") -> tuple:
    """
    PERM-002: Build SQL filter clause for warehouse restriction.
    Returns (sql_clause, params_dict)
    Usage:
        wh_filter, wh_params = build_warehouse_filter(user, db, "inv.warehouse_id")
        query = f"SELECT * FROM inventory inv WHERE 1=1 {wh_filter}"
        result = db.execute(text(query), {**other_params, **wh_params})
    """
    allowed = get_allowed_warehouses(current_user, company_conn)
    if allowed is None:
        return "", {}

    if not allowed:
        return f" AND 1=0", {}  # No access

    col = f"{table_alias}.{warehouse_column}" if table_alias else warehouse_column
    # Use parameterized query with IN clause
    placeholders = ", ".join(str(int(w)) for w in allowed)
    return f" AND {col} IN ({placeholders})", {}


# ===================== PERM-003: Cost-Center-Level Permissions =====================

def get_allowed_cost_centers(current_user, company_conn=None) -> Optional[List[int]]:
    """
    PERM-003: Get list of cost center IDs the user can access.
    Returns None if unrestricted.
    """
    if isinstance(current_user, dict):
        role = current_user.get("role")
        permissions = current_user.get("permissions", [])
        user_id = current_user.get("id")
    else:
        role = getattr(current_user, "role", None)
        permissions = getattr(current_user, "permissions", [])
        user_id = getattr(current_user, "id", None)

    if role in ['admin', 'system_admin', 'superuser'] or "*" in (permissions or []):
        return None

    if not company_conn or not user_id:
        return None

    try:
        from sqlalchemy import text
        rows = company_conn.execute(text(
            "SELECT cost_center_id FROM user_cost_centers WHERE user_id = :uid"
        ), {"uid": user_id}).fetchall()

        if not rows:
            return None  # No restrictions = access all

        return [r[0] for r in rows]
    except Exception:
        return None


def build_cost_center_filter(current_user, company_conn=None,
                              cc_column: str = "cost_center_id",
                              table_alias: str = "") -> tuple:
    """
    PERM-003: Build SQL filter clause for cost center restriction.
    Returns (sql_clause, params_dict)
    """
    allowed = get_allowed_cost_centers(current_user, company_conn)
    if allowed is None:
        return "", {}

    if not allowed:
        return f" AND 1=0", {}

    col = f"{table_alias}.{cc_column}" if table_alias else cc_column
    placeholders = ", ".join(str(int(c)) for c in allowed)
    return f" AND {col} IN ({placeholders})", {}


# ===================== PERM-004: Permission Audit Logging =====================

def _log_permission_denied(current_user, permission):
    """Log permission denied events silently"""
    try:
        if isinstance(current_user, dict):
            company_id = current_user.get("company_id")
            user_id = current_user.get("id")
            username = current_user.get("username", "unknown")
        else:
            company_id = getattr(current_user, "company_id", None)
            user_id = getattr(current_user, "id", None)
            username = getattr(current_user, "username", "unknown")

        if not company_id:
            return

        from database import get_db_connection
        from sqlalchemy import text
        db = get_db_connection(company_id)
        try:
            db.execute(text("""
                INSERT INTO audit_logs (user_id, username, action, resource_type, details, created_at)
                VALUES (:uid, :uname, 'permission_denied', 'security',
                        :details, CURRENT_TIMESTAMP)
            """), {
                "uid": user_id,
                "uname": username,
                "details": json.dumps({"denied_permission": str(permission)})
            })
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            db.close()
    except Exception:
        pass  # Never let audit logging break the app


def log_permission_change(company_conn, admin_user_id: int, admin_username: str,
                          target_user_id: int, change_type: str, details: dict):
    """
    PERM-004: Log permission changes (role changes, warehouse assignments, etc.)
    """
    try:
        from sqlalchemy import text
        company_conn.execute(text("""
            INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, details, created_at)
            VALUES (:uid, :uname, :action, 'permissions', :target, :details, CURRENT_TIMESTAMP)
        """), {
            "uid": admin_user_id,
            "uname": admin_username,
            "action": change_type,
            "target": str(target_user_id),
            "details": json.dumps(details)
        })
    except Exception as e:
        logger.warning(f"Failed to log permission change: {e}")

