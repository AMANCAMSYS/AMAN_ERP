"""
Service Management Router — SVC-001 + SVC-002
- Service / Maintenance Requests (CRUD + assign + costs + stats)
- Document Management (upload + versions + search)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import text
from typing import List, Optional
from datetime import date
import logging
import os
import uuid
import shutil

from database import get_db_connection
from routers.auth import get_current_user, UserResponse
from utils.permissions import require_permission, require_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/services", tags=["Services"], dependencies=[Depends(require_module("services"))])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads", "documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# SVC-001: Service / Maintenance Requests
# ─────────────────────────────────────────────

@router.get("/requests", dependencies=[Depends(require_permission("services.view"))])
def list_service_requests(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    customer_id: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT sr.*,
                   p.name as customer_name,
                   u.full_name as assigned_to_name,
                   cu.full_name as created_by_name
            FROM service_requests sr
            LEFT JOIN parties p ON sr.customer_id = p.id
            LEFT JOIN company_users u ON sr.assigned_to = u.id
            LEFT JOIN company_users cu ON sr.created_by = cu.id
            WHERE 1=1
        """
        params = {}
        if status:
            query += " AND sr.status = :status"
            params["status"] = status
        if priority:
            query += " AND sr.priority = :priority"
            params["priority"] = priority
        if assigned_to:
            query += " AND sr.assigned_to = :assigned_to"
            params["assigned_to"] = assigned_to
        if customer_id:
            query += " AND sr.customer_id = :customer_id"
            params["customer_id"] = customer_id
        query += " ORDER BY sr.created_at DESC"
        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/requests/stats", dependencies=[Depends(require_permission("services.view"))])
def get_service_stats(current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        stats = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'assigned') as assigned,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                COUNT(*) FILTER (WHERE status = 'on_hold') as on_hold,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
                COUNT(*) FILTER (WHERE priority = 'critical' AND status NOT IN ('completed','cancelled')) as critical_open,
                COALESCE(AVG(actual_hours) FILTER (WHERE status = 'completed'), 0) as avg_hours,
                COALESCE(SUM(actual_cost) FILTER (WHERE status = 'completed'), 0) as total_cost
            FROM service_requests
        """)).fetchone()
        return dict(stats._mapping) if stats else {}
    finally:
        db.close()


@router.get("/requests/{request_id}", dependencies=[Depends(require_permission("services.view"))])
def get_service_request(request_id: int, current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        req = db.execute(text("""
            SELECT sr.*,
                   p.name as customer_name,
                   u.full_name as assigned_to_name,
                   cu.full_name as created_by_name
            FROM service_requests sr
            LEFT JOIN parties p ON sr.customer_id = p.id
            LEFT JOIN company_users u ON sr.assigned_to = u.id
            LEFT JOIN company_users cu ON sr.created_by = cu.id
            WHERE sr.id = :id
        """), {"id": request_id}).fetchone()
        if not req:
            raise HTTPException(status_code=404, detail="طلب الصيانة غير موجود")
        result = dict(req._mapping)
        # Fetch costs
        costs = db.execute(text(
            "SELECT * FROM service_request_costs WHERE service_request_id = :id ORDER BY created_at"
        ), {"id": request_id}).fetchall()
        result["costs"] = [dict(c._mapping) for c in costs]
        return result
    finally:
        db.close()


@router.post("/requests", dependencies=[Depends(require_permission("services.create"))])
def create_service_request(data: dict, current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        req_id = db.execute(text("""
            INSERT INTO service_requests (
                title, description, category, priority, status,
                customer_id, asset_id, assigned_to,
                estimated_hours, estimated_cost, scheduled_date,
                location, notes, created_by
            ) VALUES (
                :title, :description, :category, :priority, 'pending',
                :customer_id, :asset_id, :assigned_to,
                :estimated_hours, :estimated_cost, :scheduled_date,
                :location, :notes, :uid
            ) RETURNING id
        """), {
            "title": data.get("title", ""),
            "description": data.get("description"),
            "category": data.get("category", "maintenance"),
            "priority": data.get("priority", "medium"),
            "customer_id": data.get("customer_id") or None,
            "asset_id": data.get("asset_id") or None,
            "assigned_to": data.get("assigned_to") or None,
            "estimated_hours": data.get("estimated_hours") or None,
            "estimated_cost": data.get("estimated_cost") or 0,
            "scheduled_date": data.get("scheduled_date") or None,
            "location": data.get("location"),
            "notes": data.get("notes"),
            "uid": current_user.id
        }).scalar()

        # If technician assigned immediately, update status
        if data.get("assigned_to"):
            db.execute(text("""
                UPDATE service_requests SET status = 'assigned', assigned_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {"id": req_id})

        db.commit()
        return get_service_request(req_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/requests/{request_id}", dependencies=[Depends(require_permission("services.edit"))])
def update_service_request(request_id: int, data: dict, current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT id, status FROM service_requests WHERE id = :id"), {"id": request_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="طلب الصيانة غير موجود")

        fields = []
        params = {"id": request_id}
        updatable = [
            "title", "description", "category", "priority", "status",
            "customer_id", "asset_id", "assigned_to",
            "estimated_hours", "actual_hours", "estimated_cost", "actual_cost",
            "scheduled_date", "completion_date", "location", "notes"
        ]
        for f in updatable:
            if f in data:
                fields.append(f"{f} = :{f}")
                params[f] = data[f] if data[f] != "" else None

        # Auto-set assigned_at
        if "assigned_to" in data and data["assigned_to"]:
            fields.append("assigned_at = CURRENT_TIMESTAMP")
        # Auto-set completion_date
        if data.get("status") == "completed" and not data.get("completion_date"):
            fields.append("completion_date = CURRENT_DATE")

        fields.append("updated_at = CURRENT_TIMESTAMP")

        if fields:
            db.execute(text(f"UPDATE service_requests SET {', '.join(fields)} WHERE id = :id"), params)
            db.commit()

        return get_service_request(request_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/requests/{request_id}", dependencies=[Depends(require_permission("services.delete"))])
def delete_service_request(request_id: int, current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        deleted = db.execute(text("DELETE FROM service_requests WHERE id = :id RETURNING id"), {"id": request_id}).fetchone()
        if not deleted:
            raise HTTPException(status_code=404, detail="طلب الصيانة غير موجود")
        db.commit()
        return {"message": "تم حذف طلب الصيانة بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/requests/{request_id}/assign", dependencies=[Depends(require_permission("services.edit"))])
def assign_technician(request_id: int, data: dict, current_user: UserResponse = Depends(get_current_user)):
    """Assign or reassign a technician to a service request."""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT id FROM service_requests WHERE id = :id"), {"id": request_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="طلب الصيانة غير موجود")

        db.execute(text("""
            UPDATE service_requests
            SET assigned_to = :tech_id, assigned_at = CURRENT_TIMESTAMP,
                status = CASE WHEN status = 'pending' THEN 'assigned' ELSE status END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": request_id, "tech_id": data.get("assigned_to")})
        db.commit()
        return get_service_request(request_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/requests/{request_id}/costs", dependencies=[Depends(require_permission("services.edit"))])
def add_service_cost(request_id: int, data: dict, current_user: UserResponse = Depends(get_current_user)):
    """Add a cost line to a service request."""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT id FROM service_requests WHERE id = :id"), {"id": request_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="طلب الصيانة غير موجود")

        qty = float(data.get("quantity", 1))
        unit = float(data.get("unit_cost", 0))
        total = round(qty * unit, 2)

        db.execute(text("""
            INSERT INTO service_request_costs (service_request_id, cost_type, description, quantity, unit_cost, total_cost)
            VALUES (:rid, :ctype, :desc, :qty, :ucost, :total)
        """), {
            "rid": request_id,
            "ctype": data.get("cost_type", "other"),
            "desc": data.get("description", ""),
            "qty": qty, "ucost": unit, "total": total
        })

        # Update total actual cost on the request
        db.execute(text("""
            UPDATE service_requests
            SET actual_cost = COALESCE((SELECT SUM(total_cost) FROM service_request_costs WHERE service_request_id = :id), 0),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": request_id})

        db.commit()
        return get_service_request(request_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/requests/{request_id}/costs/{cost_id}", dependencies=[Depends(require_permission("services.edit"))])
def delete_service_cost(request_id: int, cost_id: int, current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM service_request_costs WHERE id = :cid AND service_request_id = :rid"),
                   {"cid": cost_id, "rid": request_id})
        # Recalculate
        db.execute(text("""
            UPDATE service_requests
            SET actual_cost = COALESCE((SELECT SUM(total_cost) FROM service_request_costs WHERE service_request_id = :id), 0),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": request_id})
        db.commit()
        return {"message": "تم حذف التكلفة بنجاح"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ─────────────────────────────────────────────
# SVC-002: Document Management
# ─────────────────────────────────────────────

@router.get("/documents", dependencies=[Depends(require_permission("services.view"))])
def list_documents(
    category: Optional[str] = None,
    search: Optional[str] = None,
    related_module: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT d.*, u.full_name as created_by_name
            FROM documents d
            LEFT JOIN company_users u ON d.created_by = u.id
            WHERE 1=1
        """
        params = {}
        if category:
            query += " AND d.category = :category"
            params["category"] = category
        if related_module:
            query += " AND d.related_module = :related_module"
            params["related_module"] = related_module
        if search:
            query += " AND (d.title ILIKE :search OR d.description ILIKE :search OR d.tags ILIKE :search)"
            params["search"] = f"%{search}%"
        query += " ORDER BY d.created_at DESC"
        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/documents/{doc_id}", dependencies=[Depends(require_permission("services.view"))])
def get_document(doc_id: int, current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        doc = db.execute(text("""
            SELECT d.*, u.full_name as created_by_name
            FROM documents d
            LEFT JOIN company_users u ON d.created_by = u.id
            WHERE d.id = :id
        """), {"id": doc_id}).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="المستند غير موجود")
        result = dict(doc._mapping)
        # Fetch versions
        versions = db.execute(text("""
            SELECT dv.*, u.full_name as uploaded_by_name
            FROM document_versions dv
            LEFT JOIN company_users u ON dv.uploaded_by = u.id
            WHERE dv.document_id = :id ORDER BY dv.version_number DESC
        """), {"id": doc_id}).fetchall()
        result["versions"] = [dict(v._mapping) for v in versions]
        return result
    finally:
        db.close()


@router.post("/documents", dependencies=[Depends(require_permission("services.create"))])
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    description: str = Form(""),
    category: str = Form("general"),
    tags: str = Form(""),
    access_level: str = Form("company"),
    related_module: str = Form(""),
    related_id: int = Form(0),
    current_user: UserResponse = Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        # SEC-FIX-016/017: Validate file size and type
        from utils.sql_safety import (
            validate_file_size, validate_file_extension,
            MAX_DOCUMENT_SIZE, ALLOWED_DOCUMENT_EXTENSIONS, BLOCKED_FILE_EXTENSIONS
        )
        validate_file_extension(file.filename, ALLOWED_DOCUMENT_EXTENSIONS, "المستند")
        
        # Save file
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        company_dir = os.path.join(UPLOAD_DIR, current_user.company_id)
        os.makedirs(company_dir, exist_ok=True)
        file_path = os.path.join(company_dir, unique_name)

        content = await file.read()
        validate_file_size(content, MAX_DOCUMENT_SIZE, "المستند")
        
        with open(file_path, "wb") as f:
            f.write(content)
        file_size = len(content)

        used_title = title if title else file.filename

        doc_id = db.execute(text("""
            INSERT INTO documents (title, description, category, file_name, file_path, file_size,
                                   mime_type, tags, access_level, related_module, related_id, created_by)
            VALUES (:title, :desc, :cat, :fname, :fpath, :fsize,
                    :mime, :tags, :access, :rmod, :rid, :uid)
            RETURNING id
        """), {
            "title": used_title,
            "desc": description,
            "cat": category,
            "fname": file.filename,
            "fpath": file_path,
            "fsize": file_size,
            "mime": file.content_type,
            "tags": tags,
            "access": access_level,
            "rmod": related_module or None,
            "rid": related_id if related_id else None,
            "uid": current_user.id
        }).scalar()

        # First version
        db.execute(text("""
            INSERT INTO document_versions (document_id, version_number, file_name, file_path, file_size, change_notes, uploaded_by)
            VALUES (:did, 1, :fname, :fpath, :fsize, 'الإصدار الأول', :uid)
        """), {
            "did": doc_id, "fname": file.filename,
            "fpath": file_path, "fsize": file_size, "uid": current_user.id
        })

        db.commit()
        return get_document(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/documents/{doc_id}", dependencies=[Depends(require_permission("services.edit"))])
def update_document_meta(doc_id: int, data: dict, current_user: UserResponse = Depends(get_current_user)):
    """Update document metadata (title, description, category, tags, access_level)."""
    db = get_db_connection(current_user.company_id)
    try:
        existing = db.execute(text("SELECT id FROM documents WHERE id = :id"), {"id": doc_id}).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="المستند غير موجود")

        fields = []
        params = {"id": doc_id}
        for f in ["title", "description", "category", "tags", "access_level"]:
            if f in data:
                fields.append(f"{f} = :{f}")
                params[f] = data[f]
        fields.append("updated_at = CURRENT_TIMESTAMP")
        db.execute(text(f"UPDATE documents SET {', '.join(fields)} WHERE id = :id"), params)
        db.commit()
        return get_document(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/documents/{doc_id}/versions", dependencies=[Depends(require_permission("services.edit"))])
async def upload_new_version(
    doc_id: int,
    file: UploadFile = File(...),
    change_notes: str = Form(""),
    current_user: UserResponse = Depends(get_current_user)
):
    """Upload a new version of an existing document."""
    db = get_db_connection(current_user.company_id)
    try:
        doc = db.execute(text("SELECT id, current_version FROM documents WHERE id = :id"), {"id": doc_id}).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="المستند غير موجود")

        new_version = doc.current_version + 1

        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_name = f"{uuid.uuid4().hex}{ext}"
        company_dir = os.path.join(UPLOAD_DIR, current_user.company_id)
        os.makedirs(company_dir, exist_ok=True)
        file_path = os.path.join(company_dir, unique_name)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        file_size = len(content)

        db.execute(text("""
            INSERT INTO document_versions (document_id, version_number, file_name, file_path, file_size, change_notes, uploaded_by)
            VALUES (:did, :ver, :fname, :fpath, :fsize, :notes, :uid)
        """), {
            "did": doc_id, "ver": new_version,
            "fname": file.filename, "fpath": file_path,
            "fsize": file_size, "notes": change_notes or f"الإصدار {new_version}",
            "uid": current_user.id
        })

        db.execute(text("""
            UPDATE documents SET current_version = :ver, file_name = :fname, file_path = :fpath,
                                 file_size = :fsize, mime_type = :mime, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {
            "ver": new_version, "fname": file.filename,
            "fpath": file_path, "fsize": file_size,
            "mime": file.content_type, "id": doc_id
        })

        db.commit()
        return get_document(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/documents/{doc_id}", dependencies=[Depends(require_permission("services.delete"))])
def delete_document(doc_id: int, current_user: UserResponse = Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # Get file paths to clean up
        versions = db.execute(text("SELECT file_path FROM document_versions WHERE document_id = :id"), {"id": doc_id}).fetchall()
        doc = db.execute(text("SELECT file_path FROM documents WHERE id = :id"), {"id": doc_id}).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="المستند غير موجود")

        db.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})
        db.commit()

        # Clean up files
        paths = set()
        if doc.file_path:
            paths.add(doc.file_path)
        for v in versions:
            if v.file_path:
                paths.add(v.file_path)
        for p in paths:
            try:
                # SEC-FIX-018: Prevent path traversal in file deletion
                from utils.sql_safety import validate_file_path_safety
                if os.path.exists(p) and validate_file_path_safety(p, UPLOAD_DIR):
                    os.remove(p)
                elif os.path.exists(p):
                    logger.warning(f"Blocked path traversal deletion attempt: {p}")
            except Exception:
                pass

        return {"message": "تم حذف المستند بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/technicians", dependencies=[Depends(require_permission("services.view"))])
def list_technicians(current_user: UserResponse = Depends(get_current_user)):
    """List users who can be assigned to service requests."""
    db = get_db_connection(current_user.company_id)
    try:
        users = db.execute(text("""
            SELECT id, full_name, email FROM company_users WHERE is_active = true ORDER BY full_name
        """)).fetchall()
        return [dict(u._mapping) for u in users]
    finally:
        db.close()
