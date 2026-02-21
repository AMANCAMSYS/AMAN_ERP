from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from database import get_db_connection
from routers.auth import get_current_user
from schemas import BranchCreate, BranchResponse
from utils.permissions import require_permission

router = APIRouter(
    prefix="/api/branches",
    tags=["branches"]
)

@router.get("", response_model=List[BranchResponse], dependencies=[Depends(require_permission("branches.view"))])
def list_branches(
    current_user = Depends(get_current_user)
):
    """List all branches for the current company"""
    company_id = getattr(current_user, 'company_id', None) or (current_user.get('company_id') if isinstance(current_user, dict) else None)
    if not company_id:
        if getattr(current_user, 'role', None) == 'system_admin' or (isinstance(current_user, dict) and current_user.get('role') == 'system_admin'):
            return []
        raise HTTPException(status_code=400, detail="User not associated with any company")
        
    conn = get_db_connection(company_id)
    try:
        # Robust user info extraction
        if isinstance(current_user, dict):
            user_id = current_user.get('id')
            user_role = current_user.get('role', 'user')
        else:
            user_id = getattr(current_user, 'id', None)
            user_role = getattr(current_user, 'role', 'user')

        if user_role in ['admin', 'superuser', 'system_admin']:
            query = text("""
                SELECT id, branch_code, branch_name, branch_name_en, address, 
                       city, country, phone, email, is_active, is_default, created_at
                FROM branches
                ORDER BY id
            """)
            result = conn.execute(query).fetchall()
        else:
            # Filter by allowed branches
            query = text("""
                SELECT b.id, b.branch_code, b.branch_name, b.branch_name_en, b.address, 
                       b.city, b.country, b.phone, b.email, b.is_active, b.is_default, b.created_at
                FROM branches b
                JOIN user_branches ub ON b.id = ub.branch_id
                WHERE ub.user_id = :uid
                ORDER BY b.id
            """)
            result = conn.execute(query, {"uid": user_id}).fetchall()
            
            if not result:
                return []
        
        branches = []
        for row in result:
            branches.append({
                "id": row.id,
                "branch_code": row.branch_code,
                "branch_name": row.branch_name,
                "branch_name_en": row.branch_name_en,
                "address": row.address,
                "city": row.city,
                "country": row.country,
                "phone": row.phone,
                "email": row.email,
                "is_active": row.is_active,
                "is_default": row.is_default,
                "created_at": row.created_at
            })
        return branches
    except Exception as e:
        print(f"Error listing branches: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.post("", response_model=BranchResponse)
def create_branch(
    branch: BranchCreate,
    current_user = Depends(require_permission("admin.branches"))
):
    """Create a new branch"""
    conn = get_db_connection(current_user.company_id)
    try:
        # Check if this is the first branch
        count_res = conn.execute(text("SELECT COUNT(*) FROM branches")).scalar()
        is_first = (count_res == 0)
        
        # Check duplicate code
        if branch.branch_code:
            existing = conn.execute(
                text("SELECT 1 FROM branches WHERE branch_code = :code"),
                {"code": branch.branch_code}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Branch code already exists")
        
        query = text("""
            INSERT INTO branches (
                branch_code, branch_name, branch_name_en, address, 
                city, country, phone, email, is_active, is_default
            ) VALUES (
                :code, :name, :name_en, :address, 
                :city, :country, :phone, :email, :active, :is_default
            ) RETURNING id, created_at, is_default
        """)
        
        params = {
            "code": branch.branch_code,
            "name": branch.branch_name,
            "name_en": branch.branch_name_en,
            "address": branch.address,
            "city": branch.city,
            "country": branch.country,
            "phone": branch.phone,
            "email": branch.email,
            "active": branch.is_active,
            "is_default": is_first  # Make first branch default
        }
        
        result = conn.execute(query, params).fetchone()
        branch_id = result.id
        
        # 2. Link creator to the branch in user_branches
        # Extract user_id robustly
        if isinstance(current_user, dict):
            user_id = current_user.get('id')
        else:
            user_id = getattr(current_user, 'id', None)
            
        if user_id:
            conn.execute(
                text("INSERT INTO user_branches (user_id, branch_id) VALUES (:uid, :bid) ON CONFLICT DO NOTHING"),
                {"uid": user_id, "bid": branch_id}
            )
            
        conn.commit()
        
        # Construct response
        response_data = branch.model_dump()
        response_data["id"] = branch_id
        response_data["created_at"] = result.created_at
        response_data["is_default"] = result.is_default
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error creating branch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: int,
    branch: BranchCreate,
    current_user = Depends(require_permission("admin.branches"))
):
    """Update a branch"""
    conn = get_db_connection(current_user.company_id)
    try:
        # Check existence
        existing = conn.execute(
            text("SELECT 1 FROM branches WHERE id = :id"),
            {"id": branch_id}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Branch not found")

        # Check duplicate code if changed
        if branch.branch_code:
            duplicate = conn.execute(
                text("SELECT 1 FROM branches WHERE branch_code = :code AND id != :id"),
                {"code": branch.branch_code, "id": branch_id}
            ).fetchone()
            if duplicate:
                raise HTTPException(status_code=400, detail="Branch code already used by another branch")

        query = text("""
            UPDATE branches SET
                branch_code = :code,
                branch_name = :name,
                branch_name_en = :name_en,
                address = :address,
                city = :city,
                country = :country,
                phone = :phone,
                email = :email,
                is_active = :active
            WHERE id = :id
            RETURNING id, created_at, is_default
        """)
        
        params = {
            "id": branch_id,
            "code": branch.branch_code,
            "name": branch.branch_name,
            "name_en": branch.branch_name_en,
            "address": branch.address,
            "city": branch.city,
            "country": branch.country,
            "phone": branch.phone,
            "email": branch.email,
            "active": branch.is_active
        }
        
        result = conn.execute(query, params).fetchone()
        conn.commit()
        
        response_data = branch.model_dump()
        response_data["id"] = result.id
        response_data["created_at"] = result.created_at
        response_data["is_default"] = result.is_default
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error updating branch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()

@router.delete("/{branch_id}")
def delete_branch(
    branch_id: int,
    current_user = Depends(require_permission("admin.branches"))
):
    """Delete a branch (soft delete or check dependencies)"""
    conn = get_db_connection(current_user.company_id)
    try:
        # Start transaction
        # Check if default
        check = conn.execute(
            text("SELECT is_default FROM branches WHERE id = :id"),
            {"id": branch_id}
        ).fetchone()
        
        if not check:
            raise HTTPException(status_code=404, detail="Branch not found")
            
        if check.is_default:
            raise HTTPException(status_code=400, detail="Cannot delete the default branch")
            
        # Check usage (e.g. invoices, users)
        # For now, simplistic check or just prevent delete if used
        # We'll just define it as restricted if used.
        
        # Let's delete if no heavy dependencies, or better, just deactivate? 
        # User asked for delete likely.
        
        conn.execute(
            text("DELETE FROM branches WHERE id = :id"),
            {"id": branch_id}
        )
        conn.commit()
        return {"success": True, "message": "Branch deleted"}
        
    except Exception as e:
        conn.rollback()
        # Postgres Foreign Key violation will raise IntegrityError
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Cannot delete branch because it is used by other records (Invoices, Users, etc.)")
        print(f"Error deleting branch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        conn.close()
