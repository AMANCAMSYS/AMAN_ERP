"""
AMAN ERP - CRM Router
CRM-002: Sales Opportunities (Leads → Won/Lost pipeline)
CRM-004: Support Tickets with comments and SLA
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from utils.i18n import http_error
from sqlalchemy import text
from typing import Optional

from datetime import datetime, timezone
from pydantic import BaseModel
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission, require_module
from utils.accounting import generate_sequential_number
from utils.audit import log_activity
from services.notification_service import notification_service

router = APIRouter(prefix="/crm", tags=["إدارة العلاقات CRM"], dependencies=[Depends(require_module("crm"))])
logger = logging.getLogger(__name__)


# ======================== Schemas ========================

class OpportunityCreate(BaseModel):
    title: str
    customer_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    stage: str = "lead"
    probability: int = 10
    expected_value: float = 0
    expected_close_date: Optional[str] = None
    currency: Optional[str] = None
    source: Optional[str] = None
    assigned_to: Optional[int] = None
    branch_id: Optional[int] = None
    notes: Optional[str] = None

class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_value: Optional[float] = None
    expected_close_date: Optional[str] = None
    assigned_to: Optional[int] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None

class ActivityCreate(BaseModel):
    activity_type: str  # call, email, meeting, note, task
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None

class TicketCreate(BaseModel):
    subject: str
    description: Optional[str] = None
    customer_id: Optional[int] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    assigned_to: Optional[int] = None
    branch_id: Optional[int] = None
    sla_hours: int = 24

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    resolution: Optional[str] = None

class CommentCreate(BaseModel):
    comment: str
    is_internal: bool = False
    attachment_url: Optional[str] = None


# Valid stages and their probabilities
OPPORTUNITY_STAGES = {
    "lead": 10,
    "qualified": 25,
    "proposal": 50,
    "negotiation": 75,
    "won": 100,
    "lost": 0
}

# Whitelist of fields that may be updated via update_opportunity (FR-008)
OPPORTUNITY_ALLOWED_FIELDS = {
    "title", "stage", "probability", "expected_value",
    "expected_close_date", "assigned_to", "notes", "lost_reason"
}


# ======================== CRM-002: Sales Opportunities ========================

@router.get("/opportunities", dependencies=[Depends(require_permission(["sales.view", "projects.view"]))])
def list_opportunities(
    stage: Optional[str] = None,
    assigned_to: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT o.*, p.name as customer_name,
                   cu.username as assigned_name
            FROM sales_opportunities o
            LEFT JOIN parties p ON o.customer_id = p.id
            LEFT JOIN company_users cu ON o.assigned_to = cu.id
            WHERE 1=1
        """
        params = {}
        if stage:
            query += " AND o.stage = :stage"
            params["stage"] = stage
        if assigned_to:
            query += " AND o.assigned_to = :assigned"
            params["assigned"] = assigned_to
        
        query += " ORDER BY o.updated_at DESC"
        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/opportunities/pipeline", dependencies=[Depends(require_permission(["sales.view", "projects.view"]))])
def get_pipeline_summary(current_user=Depends(get_current_user)):
    """Get opportunity pipeline summary by stage."""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT stage, COUNT(*) as count, 
                   COALESCE(SUM(expected_value), 0) as total_value,
                   COALESCE(AVG(probability), 0) as avg_probability
            FROM sales_opportunities
            WHERE stage NOT IN ('won', 'lost')
            GROUP BY stage
            ORDER BY 
                CASE stage 
                    WHEN 'lead' THEN 1 
                    WHEN 'qualified' THEN 2 
                    WHEN 'proposal' THEN 3 
                    WHEN 'negotiation' THEN 4 
                END
        """)).fetchall()
        
        # Also get won/lost stats
        stats = db.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE stage = 'won') as won_count,
                COALESCE(SUM(expected_value) FILTER (WHERE stage = 'won'), 0) as won_value,
                COUNT(*) FILTER (WHERE stage = 'lost') as lost_count,
                COUNT(*) as total
            FROM sales_opportunities
        """)).fetchone()
        
        return {
            "pipeline": [dict(r._mapping) for r in rows],
            "stats": dict(stats._mapping) if stats else {},
            "stages": OPPORTUNITY_STAGES
        }
    finally:
        db.close()


@router.get("/opportunities/{opp_id}", dependencies=[Depends(require_permission(["sales.view", "projects.view"]))])
def get_opportunity(opp_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        opp = db.execute(text("""
            SELECT o.*, p.name as customer_name, cu.username as assigned_name
            FROM sales_opportunities o
            LEFT JOIN parties p ON o.customer_id = p.id
            LEFT JOIN company_users cu ON o.assigned_to = cu.id
            WHERE o.id = :id
        """), {"id": opp_id}).fetchone()
        if not opp:
            raise HTTPException(**http_error(404, "opportunity_not_found"))
        
        activities = db.execute(text("""
            SELECT * FROM opportunity_activities WHERE opportunity_id = :id ORDER BY created_at DESC
        """), {"id": opp_id}).fetchall()
        
        result = dict(opp._mapping)
        result["activities"] = [dict(a._mapping) for a in activities]
        return result
    finally:
        db.close()


@router.post("/opportunities", status_code=201, dependencies=[Depends(require_permission(["sales.create", "projects.create"]))])
def create_opportunity(data: OpportunityCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        opp_id = db.execute(text("""
            INSERT INTO sales_opportunities (
                title, customer_id, contact_name, contact_email, contact_phone,
                stage, probability, expected_value, expected_close_date,
                currency, source, assigned_to, branch_id, notes, created_by
            ) VALUES (
                :title, :cust, :cname, :cemail, :cphone,
                :stage, :prob, :val, :close,
                :curr, :src, :assigned, :branch, :notes, :user
            ) RETURNING id
        """), {
            "title": data.title, "cust": data.customer_id,
            "cname": data.contact_name, "cemail": data.contact_email,
            "cphone": data.contact_phone, "stage": data.stage,
            "prob": data.probability, "val": data.expected_value,
            "close": data.expected_close_date, "curr": data.currency,
            "src": data.source, "assigned": data.assigned_to,
            "branch": data.branch_id, "notes": data.notes,
            "user": current_user.id
        }).scalar()
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_create_opportunity", resource_type="opportunity", resource_id=str(opp_id), details={"title": data.title, "stage": data.stage}, request=request)
        return {"id": opp_id, "message": "تم إنشاء الفرصة البيعية"}
    finally:
        db.close()


@router.put("/opportunities/{opp_id}", dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
async def update_opportunity(opp_id: int, data: OpportunityUpdate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.model_dump().items()
                   if v is not None and k in OPPORTUNITY_ALLOWED_FIELDS}
        if not updates:
            raise HTTPException(**http_error(400, "no_data_to_update"))
        
        # Auto-set probability based on stage
        if "stage" in updates and updates["stage"] in OPPORTUNITY_STAGES:
            if "probability" not in updates:
                updates["probability"] = OPPORTUNITY_STAGES[updates["stage"]]
        
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = opp_id
        db.execute(text(f"UPDATE sales_opportunities SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_update_opportunity", resource_type="opportunity", resource_id=str(opp_id), details={"fields_updated": list(updates.keys())}, request=request)

        # Dispatch notification when opportunity stage changes to won or lost
        stage = updates.get("stage")
        if stage in ("won", "lost"):
            try:
                assigned = db.execute(
                    text("SELECT assigned_to FROM sales_opportunities WHERE id = :id"),
                    {"id": opp_id}
                ).scalar()
                if assigned:
                    await notification_service.dispatch(
                        db=get_db_connection(current_user.company_id),
                        company_id=current_user.company_id,
                        recipient_id=assigned,
                        event_type=f"crm.opportunity_{stage}",
                        title=f"الفرصة البيعية {'مكتسبة' if stage == 'won' else 'خاسرة'}",
                        body=f"تم تحديث الفرصة #{opp_id} إلى مرحلة {stage}",
                        feature_source="crm",
                        reference_type="opportunity",
                        reference_id=opp_id,
                        link=f"/crm/opportunities/{opp_id}",
                    )
            except Exception as notif_err:
                logger.warning("Failed to dispatch opportunity stage notification: %s", notif_err)

        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.delete("/opportunities/{opp_id}", dependencies=[Depends(require_permission(["sales.delete", "projects.delete"]))])
def delete_opportunity(opp_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM sales_opportunities WHERE id = :id"), {"id": opp_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_delete_opportunity", resource_type="opportunity", resource_id=str(opp_id), details={}, request=request)
        return {"message": "تم حذف الفرصة"}
    finally:
        db.close()


@router.post("/opportunities/{opp_id}/activities", status_code=201,
             dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
def add_activity(opp_id: int, data: ActivityCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        aid = db.execute(text("""
            INSERT INTO opportunity_activities (opportunity_id, activity_type, title, description, due_date, created_by)
            VALUES (:opp, :type, :title, :desc, :due, :user) RETURNING id
        """), {
            "opp": opp_id, "type": data.activity_type,
            "title": data.title, "desc": data.description,
            "due": data.due_date, "user": current_user.id
        }).scalar()
        
        # Update opportunity's updated_at
        db.execute(text("UPDATE sales_opportunities SET updated_at = NOW() WHERE id = :id"), {"id": opp_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_add_activity", resource_type="activity", resource_id=str(aid), details={"opportunity_id": opp_id, "activity_type": data.activity_type, "title": data.title}, request=request)
        return {"id": aid}
    finally:
        db.close()


# ======================== CRM-004: Support Tickets ========================

@router.get("/tickets", dependencies=[Depends(require_permission(["sales.view", "projects.view"]))])
def list_tickets(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        query = """
            SELECT t.*, p.name as customer_name, cu.username as assigned_name
            FROM support_tickets t
            LEFT JOIN parties p ON t.customer_id = p.id
            LEFT JOIN company_users cu ON t.assigned_to = cu.id
            WHERE 1=1
        """
        params = {}
        if status_filter:
            query += " AND t.status = :status"
            params["status"] = status_filter
        if priority:
            query += " AND t.priority = :priority"
            params["priority"] = priority
        if assigned_to:
            query += " AND t.assigned_to = :assigned"
            params["assigned"] = assigned_to
        
        query += " ORDER BY CASE t.priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, t.created_at DESC"
        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/tickets/stats", dependencies=[Depends(require_permission(["sales.view", "projects.view"]))])
def get_ticket_stats(current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        stats = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'open') as open_count,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
                COUNT(*) FILTER (WHERE status = 'resolved') as resolved_count,
                COUNT(*) FILTER (WHERE status = 'closed') as closed_count,
                COUNT(*) FILTER (WHERE priority = 'critical' AND status NOT IN ('resolved', 'closed')) as critical_open,
                COALESCE(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600) 
                    FILTER (WHERE resolved_at IS NOT NULL), 0) as avg_resolution_hours
            FROM support_tickets
        """)).fetchone()
        return dict(stats._mapping) if stats else {}
    finally:
        db.close()


@router.get("/tickets/{ticket_id}", dependencies=[Depends(require_permission(["sales.view", "projects.view"]))])
def get_ticket(ticket_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        ticket = db.execute(text("""
            SELECT t.*, p.name as customer_name, cu.username as assigned_name
            FROM support_tickets t
            LEFT JOIN parties p ON t.customer_id = p.id
            LEFT JOIN company_users cu ON t.assigned_to = cu.id
            WHERE t.id = :id
        """), {"id": ticket_id}).fetchone()
        if not ticket:
            raise HTTPException(404, "التذكرة غير موجودة")
        
        comments = db.execute(text("""
            SELECT tc.*, cu.username as author_name
            FROM ticket_comments tc
            LEFT JOIN company_users cu ON tc.created_by = cu.id
            WHERE tc.ticket_id = :id ORDER BY tc.created_at ASC
        """), {"id": ticket_id}).fetchall()
        
        result = dict(ticket._mapping)
        result["comments"] = [dict(c._mapping) for c in comments]
        
        # SLA check (FR-007)
        if ticket.status not in ('resolved', 'closed'):
            sla_hours = ticket.sla_hours
            if not sla_hours:
                result["sla_status"] = "sla_not_configured"
            else:
                now = datetime.now(timezone.utc)
                hours_open = (now - ticket.created_at).total_seconds() / 3600
                result["sla_breached"] = hours_open > sla_hours
                result["hours_open"] = round(hours_open, 1)
                result["sla_status"] = "breached" if hours_open > sla_hours else "within_sla"
        
        return result
    finally:
        db.close()


@router.post("/tickets", status_code=201,
             dependencies=[Depends(require_permission(["sales.create", "projects.create"]))])
def create_ticket(data: TicketCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        ticket_num = generate_sequential_number(db, f"TKT-{datetime.now().year}", "support_tickets", "ticket_number")
        
        tid = db.execute(text("""
            INSERT INTO support_tickets (
                ticket_number, subject, description, customer_id,
                contact_name, contact_email, contact_phone,
                priority, category, assigned_to, branch_id, sla_hours, created_by
            ) VALUES (
                :num, :subject, :desc, :cust,
                :cname, :cemail, :cphone,
                :priority, :category, :assigned, :branch, :sla, :user
            ) RETURNING id
        """), {
            "num": ticket_num, "subject": data.subject, "desc": data.description,
            "cust": data.customer_id, "cname": data.contact_name,
            "cemail": data.contact_email, "cphone": data.contact_phone,
            "priority": data.priority, "category": data.category,
            "assigned": data.assigned_to, "branch": data.branch_id,
            "sla": data.sla_hours, "user": current_user.id
        }).scalar()
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_create_ticket", resource_type="ticket", resource_id=str(tid), details={"ticket_number": ticket_num, "subject": data.subject, "priority": data.priority}, request=request)
        
        return {"id": tid, "ticket_number": ticket_num, "message": "تم إنشاء التذكرة"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/tickets/{ticket_id}", dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
async def update_ticket(ticket_id: int, data: TicketUpdate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(**http_error(400, "no_data_to_update"))
        
        # Auto-set timestamps
        if updates.get("status") == "resolved":
            updates["resolved_at"] = datetime.now()
        elif updates.get("status") == "closed":
            updates["closed_at"] = datetime.now()
        
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = ticket_id
        db.execute(text(f"UPDATE support_tickets SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_update_ticket", resource_type="ticket", resource_id=str(ticket_id), details={"fields_updated": list(updates.keys())}, request=request)

        # Dispatch notification when ticket is assigned to a user
        assigned_to = updates.get("assigned_to")
        if assigned_to:
            try:
                await notification_service.dispatch(
                    db=get_db_connection(current_user.company_id),
                    company_id=current_user.company_id,
                    recipient_id=assigned_to,
                    event_type="crm.ticket_assigned",
                    title="تم تعيين تذكرة دعم إليك",
                    body=f"تم تعيين التذكرة #{ticket_id} إليك",
                    feature_source="crm",
                    reference_type="ticket",
                    reference_id=ticket_id,
                    link=f"/crm/tickets/{ticket_id}",
                )
            except Exception as notif_err:
                logger.warning("Failed to dispatch ticket assignment notification: %s", notif_err)

        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.post("/tickets/{ticket_id}/comments", status_code=201,
             dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
def add_comment(ticket_id: int, data: CommentCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        cid = db.execute(text("""
            INSERT INTO ticket_comments (ticket_id, comment, is_internal, attachment_url, created_by)
            VALUES (:tid, :comment, :internal, :attach, :user) RETURNING id
        """), {
            "tid": ticket_id, "comment": data.comment,
            "internal": data.is_internal, "attach": data.attachment_url,
            "user": current_user.id
        }).scalar()
        
        db.execute(text("UPDATE support_tickets SET updated_at = NOW() WHERE id = :id"), {"id": ticket_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_add_ticket_comment", resource_type="ticket_comment", resource_id=str(cid), details={"ticket_id": ticket_id, "is_internal": data.is_internal}, request=request)
        return {"id": cid}
    finally:
        db.close()


# ======================== CRM-001: Convert Opportunity to Quotation ========================

@router.post("/opportunities/{opp_id}/convert-quotation", status_code=201,
             dependencies=[Depends(require_permission("sales.create"))])
def convert_to_quotation(opp_id: int, request: Request, current_user=Depends(get_current_user)):
    """تحويل فرصة بيعية إلى عرض سعر"""
    db = get_db_connection(current_user.company_id)
    try:
        opp = db.execute(text("SELECT * FROM sales_opportunities WHERE id = :id"), {"id": opp_id}).fetchone()
        if not opp:
            raise HTTPException(**http_error(404, "opportunity_not_found"))
        opp = opp._mapping

        # T003: Block duplicate conversion — check if quotation already exists
        if opp.get("won_quotation_id"):
            raise HTTPException(
                status_code=409,
                detail={"error": "quotation_already_exists", "quotation_id": opp["won_quotation_id"]}
            )

        # T008: Use http_error helper (Constitution IV)
        if not opp.get("customer_id"):
            raise HTTPException(**http_error(400, "opportunity_no_customer"))

        # T004: Fix generate_sequential_number column name: "quotation_number" → "sq_number"
        quot_num = generate_sequential_number(db, f"QT-{datetime.now().year}", "sales_quotations", "sq_number")

        # T005: Fix INSERT column names: quotation_number → sq_number, valid_until → expiry_date
        quot_id = db.execute(text("""
            INSERT INTO sales_quotations (
                sq_number, customer_id, quotation_date, expiry_date,
                subtotal, tax_amount, discount, total, status, notes, created_by, branch_id
            ) VALUES (
                :num, :cust, CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days',
                :amt, 0, 0, :amt, 'draft',
                :notes, :uid, :branch
            ) RETURNING id
        """), {
            "num": quot_num,
            "cust": opp["customer_id"],
            "amt": opp.get("expected_value") or 0,
            "notes": f"تم التحويل من فرصة: {opp['title']}",
            "uid": current_user.id,
            "branch": opp.get("branch_id")
        }).scalar()

        # T006: Fix line INSERT column name: quotation_id → sq_id
        if opp.get("expected_value") and opp["expected_value"] > 0:
            db.execute(text("""
                INSERT INTO sales_quotation_lines (sq_id, description, quantity, unit_price, tax_rate, discount, total)
                VALUES (:qid, :desc, 1, :price, 0, 0, :price)
            """), {
                "qid": quot_id,
                "desc": opp["title"],
                "price": opp["expected_value"]
            })

        # T007: Write won_quotation_id back to opportunity + update stage to 'proposal'
        db.execute(text("""
            UPDATE sales_opportunities
            SET stage = 'proposal', won_quotation_id = :qid, updated_at = NOW()
            WHERE id = :id
        """), {"qid": quot_id, "id": opp_id})
        db.commit()

        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_convert_opportunity_to_quotation", resource_type="opportunity", resource_id=str(opp_id), details={"quotation_id": quot_id, "quotation_number": quot_num}, request=request)
        return {"quotation_id": quot_id, "quotation_number": quot_num, "message": "تم تحويل الفرصة إلى عرض سعر"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error converting opportunity to quotation: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


# ======================== CRM-003: Marketing Campaigns ========================

from schemas.campaign import CampaignCreate, TrackingWebhookPayload

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    campaign_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    target_audience: Optional[str] = None
    description: Optional[str] = None
    segment_id: Optional[int] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    scheduled_date: Optional[str] = None
    estimated_cost: Optional[float] = None


@router.get("/campaigns", dependencies=[Depends(require_permission("crm.campaign_view"))])
def list_campaigns(
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        conditions = ["1=1"]
        params = {}
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if campaign_type:
            conditions.append("campaign_type = :type")
            params["type"] = campaign_type

        rows = db.execute(text(f"""
            SELECT c.*, u.full_name as created_by_name
            FROM marketing_campaigns c
            LEFT JOIN company_users u ON c.created_by = u.id
            WHERE {' AND '.join(conditions)}
            ORDER BY c.created_at DESC
        """), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/campaigns/{campaign_id}", dependencies=[Depends(require_permission("crm.campaign_view"))])
def get_campaign(campaign_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("""
            SELECT c.*, s.name as segment_name
            FROM marketing_campaigns c
            LEFT JOIN crm_customer_segments s ON c.segment_id = s.id
            WHERE c.id = :id
        """), {"id": campaign_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="الحملة غير موجودة")
        data = dict(row._mapping)
        # Compute rates
        sent = data.get("total_sent") or 0
        data["delivery_rate"] = round(100.0 * (data.get("total_delivered") or 0) / sent, 1) if sent else 0
        data["open_rate"] = round(100.0 * (data.get("total_opened") or 0) / sent, 1) if sent else 0
        data["click_rate"] = round(100.0 * (data.get("total_clicked") or 0) / sent, 1) if sent else 0
        data["response_rate"] = round(100.0 * (data.get("total_responded") or 0) / sent, 1) if sent else 0
        responded = data.get("total_responded") or 0
        cost = float(data.get("actual_cost") or data.get("estimated_cost") or 0)
        data["cost_per_lead"] = round(cost / responded, 2) if responded and cost else 0
        return data
    finally:
        db.close()


@router.post("/campaigns", status_code=201, dependencies=[Depends(require_permission("crm.campaign_manage"))])
def create_campaign(data: CampaignCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        cid = db.execute(text("""
            INSERT INTO marketing_campaigns (
                name, campaign_type, status, start_date, end_date,
                budget, target_audience, description, created_by, branch_id,
                segment_id, subject, content, scheduled_date, estimated_cost
            ) VALUES (
                :name, :type, :status, :start, :end,
                :budget, :audience, :desc, :uid, :branch,
                :segment_id, :subject, :content,
                CASE WHEN :scheduled IS NOT NULL THEN :scheduled::timestamptz ELSE NULL END,
                :est_cost
            ) RETURNING id
        """), {
            "name": data.name, "type": data.campaign_type, "status": data.status,
            "start": data.start_date, "end": data.end_date,
            "budget": data.budget, "audience": data.target_audience,
            "desc": data.description, "uid": current_user.id, "branch": data.branch_id,
            "segment_id": data.segment_id, "subject": data.subject,
            "content": data.content, "scheduled": data.scheduled_date,
            "est_cost": data.estimated_cost,
        }).scalar()
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_create_campaign", resource_type="campaign", resource_id=str(cid), details={"name": data.name, "campaign_type": data.campaign_type}, request=request)
        return {"id": cid, "message": "تم إنشاء الحملة"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/campaigns/{campaign_id}", dependencies=[Depends(require_permission("crm.campaign_manage"))])
def update_campaign(campaign_id: int, data: CampaignUpdate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(**http_error(400, "no_data_to_update"))
        updates["id"] = campaign_id
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        db.execute(text(f"UPDATE marketing_campaigns SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_update_campaign", resource_type="campaign", resource_id=str(campaign_id), details={"fields_updated": list(updates.keys())}, request=request)
        return {"message": "تم تحديث الحملة"}
    finally:
        db.close()


@router.delete("/campaigns/{campaign_id}", dependencies=[Depends(require_permission("crm.campaign_manage"))])
def delete_campaign(campaign_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM marketing_campaigns WHERE id = :id"), {"id": campaign_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_delete_campaign", resource_type="campaign", resource_id=str(campaign_id), details={}, request=request)
        return {"message": "تم حذف الحملة"}
    finally:
        db.close()


# ---- Campaign Execution ----

@router.post("/campaigns/{campaign_id}/execute", dependencies=[Depends(require_permission("crm.campaign_execute"))])
async def execute_campaign(campaign_id: int, request: Request, current_user=Depends(get_current_user)):
    """Execute campaign: fetch segment contacts, create recipient records, dispatch notifications."""
    db = get_db_connection(current_user.company_id)
    try:
        campaign = db.execute(text("""
            SELECT id, segment_id, campaign_type, subject, content, status, created_by
            FROM marketing_campaigns WHERE id = :id
        """), {"id": campaign_id}).fetchone()

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        c = dict(campaign._mapping)
        if c["status"] not in ("draft", "scheduled"):
            raise HTTPException(status_code=400, detail="Campaign must be in draft or scheduled status to execute")

        if not c["segment_id"]:
            raise HTTPException(status_code=400, detail="Campaign must have a segment to execute")

        # Idempotency: prevent double-execution
        existing_recipients = db.execute(text(
            "SELECT COUNT(*) FROM campaign_recipients WHERE campaign_id = :id"
        ), {"id": campaign_id}).scalar()
        if existing_recipients > 0:
            raise HTTPException(status_code=400, detail="Campaign already has recipients — it may have been executed already")

        # Fetch segment contacts
        contacts = db.execute(text("""
            SELECT p.id, p.name, p.email, p.phone
            FROM crm_customer_segment_members csm
            JOIN parties p ON csm.customer_id = p.id
            WHERE csm.segment_id = :seg_id
        """), {"seg_id": c["segment_id"]}).fetchall()

        if not contacts:
            raise HTTPException(status_code=400, detail="No contacts found in the target segment")

        campaign_type = c["campaign_type"] or "email"
        total_created = 0

        for contact in contacts:
            ct = dict(contact._mapping)
            channels = []
            if campaign_type in ("email", "both") and ct.get("email"):
                channels.append("email")
            if campaign_type in ("sms", "both") and ct.get("phone"):
                channels.append("sms")

            for channel in channels:
                db.execute(text("""
                    INSERT INTO campaign_recipients (campaign_id, contact_id, channel, delivery_status)
                    VALUES (:cid, :contact_id, :channel, 'sent')
                """), {"cid": campaign_id, "contact_id": ct["id"], "channel": channel})
                total_created += 1

        # Update campaign status and metrics
        db.execute(text("""
            UPDATE marketing_campaigns
            SET status = 'executing', executed_at = NOW(),
                total_sent = :total, updated_at = NOW()
            WHERE id = :id
        """), {"total": total_created, "id": campaign_id})

        # Mark as completed (synchronous execution)
        db.execute(text("""
            UPDATE marketing_campaigns
            SET status = 'completed', total_delivered = :total,
                updated_at = NOW()
            WHERE id = :id
        """), {"total": total_created, "id": campaign_id})

        # Update recipient delivery status
        db.execute(text("""
            UPDATE campaign_recipients
            SET delivery_status = 'delivered', updated_at = NOW()
            WHERE campaign_id = :cid AND delivery_status = 'sent'
        """), {"cid": campaign_id})

        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_execute_campaign", resource_type="campaign", resource_id=str(campaign_id), details={"total_recipients": total_created}, request=request)

        # Notify campaign creator about execution completion
        campaign_creator = c.get("created_by")
        if campaign_creator:
            try:
                await notification_service.dispatch(
                    db=get_db_connection(current_user.company_id),
                    company_id=current_user.company_id,
                    recipient_id=campaign_creator,
                    event_type="crm.campaign_executed",
                    title="تم تنفيذ الحملة التسويقية",
                    body=f"تم إرسال الحملة #{campaign_id} إلى {total_created} مستلم",
                    feature_source="crm",
                    reference_type="campaign",
                    reference_id=campaign_id,
                    link=f"/campaigns/{campaign_id}/report",
                )
            except Exception as notif_err:
                logger.warning("Failed to dispatch campaign execution notification: %s", notif_err)

        return {
            "message": "Campaign executed successfully",
            "total_recipients": total_created,
            "campaign_id": campaign_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to execute campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute campaign")
    finally:
        db.close()


@router.get("/campaigns/{campaign_id}/recipients", dependencies=[Depends(require_permission("crm.campaign_view"))])
def list_campaign_recipients(
    campaign_id: int,
    delivery_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
):
    """List recipients for a campaign with their engagement status."""
    db = get_db_connection(current_user.company_id)
    try:
        conditions = ["cr.campaign_id = :cid"]
        params: dict = {"cid": campaign_id, "skip": skip, "limit": limit}

        if delivery_status:
            conditions.append("cr.delivery_status = :ds")
            params["ds"] = delivery_status

        where = " AND ".join(conditions)
        rows = db.execute(text(f"""
            SELECT cr.id, cr.contact_id, p.name as contact_name, p.email as contact_email,
                   cr.channel, cr.delivery_status, cr.opened_at, cr.clicked_at, cr.responded_at,
                   cr.created_at
            FROM campaign_recipients cr
            JOIN parties p ON cr.contact_id = p.id
            WHERE {where}
            ORDER BY cr.created_at DESC
            OFFSET :skip LIMIT :limit
        """), params).fetchall()

        count_row = db.execute(text(f"""
            SELECT COUNT(*) FROM campaign_recipients cr WHERE {where}
        """), params).fetchone()

        return {
            "recipients": [dict(r._mapping) for r in rows],
            "total": count_row[0] if count_row else 0,
        }
    finally:
        db.close()


@router.post("/campaigns/webhook/track")
def campaign_tracking_webhook(payload: TrackingWebhookPayload, company_id: str):
    """Public webhook for tracking campaign engagement (opens, clicks, responses).
    Requires company_id query param. Validates a signed payload to prevent tampering."""
    import hashlib
    import os
    import hmac as hmac_lib
    webhook_secret = os.environ.get("CAMPAIGN_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    expected_sig = hashlib.sha256(f"{payload.recipient_id}:{payload.event}:{webhook_secret}".encode()).hexdigest()

    if not hmac_lib.compare_digest(expected_sig, payload.signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    db = get_db_connection(company_id)
    try:
        if payload.event == "delivered":
            db.execute(text("""
                UPDATE campaign_recipients SET delivery_status = 'delivered', updated_at = NOW()
                WHERE id = :rid
            """), {"rid": payload.recipient_id})
            db.execute(text("""
                UPDATE marketing_campaigns SET total_delivered = total_delivered + 1
                WHERE id = (SELECT campaign_id FROM campaign_recipients WHERE id = :rid)
            """), {"rid": payload.recipient_id})

        elif payload.event == "opened":
            db.execute(text("""
                UPDATE campaign_recipients SET opened_at = COALESCE(opened_at, NOW()), updated_at = NOW()
                WHERE id = :rid
            """), {"rid": payload.recipient_id})
            db.execute(text("""
                UPDATE marketing_campaigns SET total_opened = total_opened + 1
                WHERE id = (SELECT campaign_id FROM campaign_recipients WHERE id = :rid)
            """), {"rid": payload.recipient_id})

        elif payload.event == "clicked":
            db.execute(text("""
                UPDATE campaign_recipients SET clicked_at = COALESCE(clicked_at, NOW()), updated_at = NOW()
                WHERE id = :rid
            """), {"rid": payload.recipient_id})
            db.execute(text("""
                UPDATE marketing_campaigns SET total_clicked = total_clicked + 1
                WHERE id = (SELECT campaign_id FROM campaign_recipients WHERE id = :rid)
            """), {"rid": payload.recipient_id})

        elif payload.event == "responded":
            db.execute(text("""
                UPDATE campaign_recipients SET responded_at = COALESCE(responded_at, NOW()), updated_at = NOW()
                WHERE id = :rid
            """), {"rid": payload.recipient_id})
            db.execute(text("""
                UPDATE marketing_campaigns SET total_responded = total_responded + 1
                WHERE id = (SELECT campaign_id FROM campaign_recipients WHERE id = :rid)
            """), {"rid": payload.recipient_id})

        elif payload.event in ("bounced", "failed"):
            db.execute(text("""
                UPDATE campaign_recipients SET delivery_status = :status, updated_at = NOW()
                WHERE id = :rid
            """), {"rid": payload.recipient_id, "status": payload.event})

        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        logger.error(f"Tracking webhook error: {e}")
        raise HTTPException(status_code=500, detail="Tracking webhook failed")
    finally:
        db.close()


# ---- Lead Attribution ----

@router.post("/campaigns/{campaign_id}/attribute-lead", dependencies=[Depends(require_permission("crm.campaign_manage"))])
def attribute_lead_to_campaign(campaign_id: int, lead_id: int, request: Request, current_user=Depends(get_current_user)):
    """Attribute a CRM lead/opportunity to a campaign."""
    db = get_db_connection(current_user.company_id)
    try:
        # Verify campaign exists
        campaign = db.execute(text("SELECT id FROM marketing_campaigns WHERE id = :id"), {"id": campaign_id}).fetchone()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Verify lead exists
        lead = db.execute(text("SELECT id FROM sales_opportunities WHERE id = :id"), {"id": lead_id}).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead/opportunity not found")

        # Check for duplicate
        existing = db.execute(text("""
            SELECT id FROM campaign_lead_attributions
            WHERE campaign_id = :cid AND lead_id = :lid
        """), {"cid": campaign_id, "lid": lead_id}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Lead already attributed to this campaign")

        db.execute(text("""
            INSERT INTO campaign_lead_attributions (campaign_id, lead_id, attributed_at)
            VALUES (:cid, :lid, NOW())
        """), {"cid": campaign_id, "lid": lead_id})

        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_attribute_lead_to_campaign", resource_type="campaign_lead_attribution", resource_id=str(campaign_id), details={"lead_id": lead_id}, request=request)
        return {"message": "Lead attributed to campaign", "campaign_id": campaign_id, "lead_id": lead_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Lead attribution error: {e}")
        raise HTTPException(status_code=500, detail="Failed to attribute lead")
    finally:
        db.close()


@router.get("/campaigns/{campaign_id}/metrics", dependencies=[Depends(require_permission("crm.campaign_view"))])
def get_campaign_metrics(campaign_id: int, current_user=Depends(get_current_user)):
    """Get detailed engagement metrics and lead attribution for a campaign."""
    db = get_db_connection(current_user.company_id)
    try:
        campaign = db.execute(text("""
            SELECT c.id, c.name, c.total_sent, c.total_delivered, c.total_opened,
                   c.total_clicked, c.total_responded, c.estimated_cost, c.actual_cost
            FROM marketing_campaigns c WHERE c.id = :id
        """), {"id": campaign_id}).fetchone()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        c = dict(campaign._mapping)
        sent = c["total_sent"] or 0
        c["delivery_rate"] = round(100.0 * (c["total_delivered"] or 0) / sent, 1) if sent else 0
        c["open_rate"] = round(100.0 * (c["total_opened"] or 0) / sent, 1) if sent else 0
        c["click_rate"] = round(100.0 * (c["total_clicked"] or 0) / sent, 1) if sent else 0
        c["response_rate"] = round(100.0 * (c["total_responded"] or 0) / sent, 1) if sent else 0

        # Attributed leads
        leads = db.execute(text("""
            SELECT cla.id, cla.lead_id, so.title as lead_title, so.stage,
                   so.expected_value, cla.attributed_at
            FROM campaign_lead_attributions cla
            JOIN sales_opportunities so ON cla.lead_id = so.id
            WHERE cla.campaign_id = :cid
            ORDER BY cla.attributed_at DESC
        """), {"cid": campaign_id}).fetchall()

        responded = c["total_responded"] or 0
        cost = float(c.get("actual_cost") or c.get("estimated_cost") or 0)
        c["cost_per_lead"] = round(cost / responded, 2) if responded and cost else 0
        c["attributed_leads"] = [dict(r._mapping) for r in leads]
        c["total_attributed_leads"] = len(leads)

        return c
    finally:
        db.close()


# ======================== CRM-005: Knowledge Base ========================

class ArticleCreate(BaseModel):
    title: str
    category: str = "general"  # faq, guide, policy, general
    content: str
    tags: Optional[str] = None
    is_published: bool = False

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_published: Optional[bool] = None


@router.get("/knowledge-base", dependencies=[Depends(require_permission("sales.view"))])
def list_articles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(get_current_user)
):
    db = get_db_connection(current_user.company_id)
    try:
        conditions = ["1=1"]
        params = {}
        if category:
            conditions.append("category = :cat")
            params["cat"] = category
        if search:
            conditions.append("(title ILIKE :q OR content ILIKE :q OR tags ILIKE :q)")
            params["q"] = f"%{search}%"

        rows = db.execute(text(f"""
            SELECT kb.*, u.full_name as author_name
            FROM crm_knowledge_base kb
            LEFT JOIN company_users u ON kb.created_by = u.id
            WHERE {' AND '.join(conditions)}
            ORDER BY kb.created_at DESC
        """), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/knowledge-base/{article_id}", dependencies=[Depends(require_permission("sales.view"))])
def get_article(article_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # increment view count
        db.execute(text("UPDATE crm_knowledge_base SET views = COALESCE(views, 0) + 1 WHERE id = :id"), {"id": article_id})
        db.commit()
        row = db.execute(text("""
            SELECT kb.*, u.full_name as author_name
            FROM crm_knowledge_base kb LEFT JOIN company_users u ON kb.created_by = u.id
            WHERE kb.id = :id
        """), {"id": article_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="المقالة غير موجودة")
        return dict(row._mapping)
    finally:
        db.close()


@router.post("/knowledge-base", status_code=201, dependencies=[Depends(require_permission("sales.create"))])
def create_article(data: ArticleCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        aid = db.execute(text("""
            INSERT INTO crm_knowledge_base (title, category, content, tags, is_published, created_by)
            VALUES (:title, :cat, :content, :tags, :pub, :uid) RETURNING id
        """), {
            "title": data.title, "cat": data.category, "content": data.content,
            "tags": data.tags, "pub": data.is_published, "uid": current_user.id
        }).scalar()
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_create_article", resource_type="knowledge_article", resource_id=str(aid), details={"title": data.title, "category": data.category}, request=request)
        return {"id": aid, "message": "تم إنشاء المقالة"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating article: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/knowledge-base/{article_id}", dependencies=[Depends(require_permission("sales.create"))])
def update_article(article_id: int, data: ArticleUpdate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(**http_error(400, "no_data_to_update"))
        updates["id"] = article_id
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        db.execute(text(f"UPDATE crm_knowledge_base SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_update_article", resource_type="knowledge_article", resource_id=str(article_id), details={"fields_updated": list(updates.keys())}, request=request)
        return {"message": "تم تحديث المقالة"}
    finally:
        db.close()


@router.delete("/knowledge-base/{article_id}", dependencies=[Depends(require_permission("sales.create"))])
def delete_article(article_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM crm_knowledge_base WHERE id = :id"), {"id": article_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_delete_article", resource_type="knowledge_article", resource_id=str(article_id), details={}, request=request)
        return {"message": "تم حذف المقالة"}
    finally:
        db.close()


# ======================== CRM-006: Lead Scoring ========================

class LeadScoringRuleCreate(BaseModel):
    rule_name: str
    field_name: str  # stage, source, expected_value, customer_id, etc.
    operator: str = "equals"  # equals, greater_than, less_than, contains, exists
    field_value: Optional[str] = None
    score: int = 0

class LeadScoringRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    field_name: Optional[str] = None
    operator: Optional[str] = None
    field_value: Optional[str] = None
    score: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/lead-scoring/rules", dependencies=[Depends(require_permission("sales.view"))])
def list_scoring_rules(current_user=Depends(get_current_user)):
    """قائمة قواعد تسجيل العملاء المحتملين"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT * FROM crm_lead_scoring_rules ORDER BY score DESC
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/lead-scoring/rules", status_code=201, dependencies=[Depends(require_permission("sales.create"))])
def create_scoring_rule(data: LeadScoringRuleCreate, request: Request, current_user=Depends(get_current_user)):
    """إنشاء قاعدة تسجيل نقاط"""
    db = get_db_connection(current_user.company_id)
    try:
        rid = db.execute(text("""
            INSERT INTO crm_lead_scoring_rules (rule_name, field_name, operator, field_value, score, created_by)
            VALUES (:name, :field, :op, :val, :score, :uid) RETURNING id
        """), {
            "name": data.rule_name, "field": data.field_name,
            "op": data.operator, "val": data.field_value,
            "score": data.score, "uid": current_user.id
        }).scalar()
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_create_scoring_rule", resource_type="lead_scoring_rule", resource_id=str(rid), details={"rule_name": data.rule_name, "score": data.score}, request=request)
        return {"id": rid, "message": "تم إنشاء قاعدة التسجيل"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating scoring rule: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/lead-scoring/rules/{rule_id}", dependencies=[Depends(require_permission("sales.create"))])
def update_scoring_rule(rule_id: int, data: LeadScoringRuleUpdate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(**http_error(400, "no_data_to_update"))
        updates["id"] = rule_id
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        db.execute(text(f"UPDATE crm_lead_scoring_rules SET {set_clause} WHERE id = :id"), updates)
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_update_scoring_rule", resource_type="lead_scoring_rule", resource_id=str(rule_id), details={"fields_updated": list(updates.keys())}, request=request)
        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.delete("/lead-scoring/rules/{rule_id}", dependencies=[Depends(require_permission("sales.delete"))])
def delete_scoring_rule(rule_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM crm_lead_scoring_rules WHERE id = :id"), {"id": rule_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_delete_scoring_rule", resource_type="lead_scoring_rule", resource_id=str(rule_id), details={}, request=request)
        return {"message": "تم الحذف"}
    finally:
        db.close()


@router.post("/lead-scoring/calculate", dependencies=[Depends(require_permission("sales.create"))])
def calculate_lead_scores(request: Request, current_user=Depends(get_current_user)):
    """حساب نقاط جميع الفرص تلقائياً بناءً على القواعد"""
    db = get_db_connection(current_user.company_id)
    try:
        rules = db.execute(text(
            "SELECT * FROM crm_lead_scoring_rules WHERE is_active = TRUE"
        )).fetchall()
        opps = db.execute(text(
            "SELECT * FROM sales_opportunities WHERE stage NOT IN ('won','lost')"
        )).fetchall()

        scored = 0
        for opp in opps:
            opp_d = dict(opp._mapping)
            total = 0
            details = []
            for r in rules:
                r_d = dict(r._mapping)
                val = str(opp_d.get(r_d["field_name"], "") or "")
                match = False
                if r_d["operator"] == "equals":
                    match = val.lower() == (r_d["field_value"] or "").lower()
                elif r_d["operator"] == "contains":
                    match = (r_d["field_value"] or "").lower() in val.lower()
                elif r_d["operator"] == "greater_than":
                    try:
                        match = float(val) > float(r_d["field_value"] or 0)
                    except (ValueError, TypeError):
                        pass
                elif r_d["operator"] == "less_than":
                    try:
                        match = float(val) < float(r_d["field_value"] or 0)
                    except (ValueError, TypeError):
                        pass
                elif r_d["operator"] == "exists":
                    match = bool(val and val.strip())

                if match:
                    total += r_d["score"]
                    details.append({"rule": r_d["rule_name"], "score": r_d["score"]})

            grade = "A" if total >= 80 else "B" if total >= 60 else "C" if total >= 40 else "D"

            import json
            db.execute(text("""
                INSERT INTO crm_lead_scores (opportunity_id, total_score, grade, scoring_details, last_scored_at)
                VALUES (:oid, :score, :grade, :details, NOW())
                ON CONFLICT (opportunity_id) DO UPDATE SET
                    total_score = EXCLUDED.total_score,
                    grade = EXCLUDED.grade,
                    scoring_details = EXCLUDED.scoring_details,
                    last_scored_at = NOW()
            """), {
                "oid": opp_d["id"], "score": total,
                "grade": grade, "details": json.dumps(details)
            })
            scored += 1

        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_calculate_lead_scores", resource_type="lead_scoring", details={"scored_count": scored}, request=request)
        return {"scored": scored, "message": f"تم تسجيل نقاط {scored} فرصة"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error calculating lead scores: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.get("/lead-scoring/scores", dependencies=[Depends(require_permission("sales.view"))])
def get_lead_scores(grade: Optional[str] = None, current_user=Depends(get_current_user)):
    """عرض نقاط الفرص مع التصنيف"""
    db = get_db_connection(current_user.company_id)
    try:
        conditions = ["1=1"]
        params = {}
        if grade:
            conditions.append("ls.grade = :grade")
            params["grade"] = grade.upper()

        rows = db.execute(text(f"""
            SELECT ls.*, o.title, o.stage, o.expected_value, o.contact_name,
                   p.name as customer_name
            FROM crm_lead_scores ls
            JOIN sales_opportunities o ON ls.opportunity_id = o.id
            LEFT JOIN parties p ON o.customer_id = p.id
            WHERE {' AND '.join(conditions)}
            ORDER BY ls.total_score DESC
        """), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


# ======================== CRM-007: Customer Segmentation ========================

class SegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    criteria: Optional[dict] = {}
    color: str = "#3B82F6"
    auto_assign: bool = False

class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[dict] = None
    color: Optional[str] = None
    auto_assign: Optional[bool] = None
    is_active: Optional[bool] = None


@router.get("/segments", dependencies=[Depends(require_permission("sales.view"))])
def list_segments(current_user=Depends(get_current_user)):
    """قائمة شرائح العملاء"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT s.*,
                   (SELECT COUNT(*) FROM crm_customer_segment_members m WHERE m.segment_id = s.id) as member_count
            FROM crm_customer_segments s
            WHERE s.is_active = TRUE
            ORDER BY s.name
        """)).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/segments", status_code=201, dependencies=[Depends(require_permission("sales.create"))])
def create_segment(data: SegmentCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        import json
        sid = db.execute(text("""
            INSERT INTO crm_customer_segments (name, description, criteria, color, auto_assign, created_by)
            VALUES (:name, :desc, :criteria, :color, :auto, :uid) RETURNING id
        """), {
            "name": data.name, "desc": data.description,
            "criteria": json.dumps(data.criteria or {}),
            "color": data.color, "auto": data.auto_assign, "uid": current_user.id
        }).scalar()
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_create_segment", resource_type="customer_segment", resource_id=str(sid), details={"name": data.name}, request=request)
        return {"id": sid, "message": "تم إنشاء شريحة العملاء"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating segment: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/segments/{seg_id}", dependencies=[Depends(require_permission("sales.create"))])
def update_segment(seg_id: int, data: SegmentUpdate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        import json
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if "criteria" in updates:
            updates["criteria"] = json.dumps(updates["criteria"])
        if not updates:
            raise HTTPException(**http_error(400, "no_data"))
        updates["id"] = seg_id
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        db.execute(text(f"UPDATE crm_customer_segments SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_update_segment", resource_type="customer_segment", resource_id=str(seg_id), details={"fields_updated": list(updates.keys())}, request=request)
        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.delete("/segments/{seg_id}", dependencies=[Depends(require_permission("sales.delete"))])
def delete_segment(seg_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM crm_customer_segment_members WHERE segment_id = :id"), {"id": seg_id})
        db.execute(text("DELETE FROM crm_customer_segments WHERE id = :id"), {"id": seg_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_delete_segment", resource_type="customer_segment", resource_id=str(seg_id), details={}, request=request)
        return {"message": "تم الحذف"}
    finally:
        db.close()


@router.post("/segments/{seg_id}/customers/{customer_id}",
             status_code=201, dependencies=[Depends(require_permission("sales.create"))])
def add_customer_to_segment(seg_id: int, customer_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("""
            INSERT INTO crm_customer_segment_members (segment_id, customer_id)
            VALUES (:sid, :cid) ON CONFLICT DO NOTHING
        """), {"sid": seg_id, "cid": customer_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_add_customer_to_segment", resource_type="customer_segment", resource_id=str(seg_id), details={"customer_id": customer_id}, request=request)
        return {"message": "تمت الإضافة"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding customer to segment: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.delete("/segments/{seg_id}/customers/{customer_id}",
               dependencies=[Depends(require_permission("sales.delete"))])
def remove_customer_from_segment(seg_id: int, customer_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("""
            DELETE FROM crm_customer_segment_members WHERE segment_id = :sid AND customer_id = :cid
        """), {"sid": seg_id, "cid": customer_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_remove_customer_from_segment", resource_type="customer_segment", resource_id=str(seg_id), details={"customer_id": customer_id}, request=request)
        return {"message": "تمت الإزالة"}
    finally:
        db.close()


@router.get("/segments/{seg_id}/customers", dependencies=[Depends(require_permission("sales.view"))])
def get_segment_customers(seg_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT p.id, p.name, p.email, p.phone, p.party_type, m.added_at
            FROM crm_customer_segment_members m
            JOIN parties p ON m.customer_id = p.id
            WHERE m.segment_id = :sid
            ORDER BY m.added_at DESC
        """), {"sid": seg_id}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


# ======================== CRM-008: CRM Contacts ========================

class ContactCreate(BaseModel):
    customer_id: int
    first_name: str
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    department: Optional[str] = None
    is_primary: bool = False
    is_decision_maker: bool = False
    notes: Optional[str] = None

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    department: Optional[str] = None
    is_primary: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    notes: Optional[str] = None


@router.get("/contacts", dependencies=[Depends(require_permission("sales.view"))])
def list_contacts(customer_id: Optional[int] = None, current_user=Depends(get_current_user)):
    """قائمة جهات الاتصال"""
    db = get_db_connection(current_user.company_id)
    try:
        conditions = ["1=1"]
        params = {}
        if customer_id:
            conditions.append("c.customer_id = :cid")
            params["cid"] = customer_id

        rows = db.execute(text(f"""
            SELECT c.*, p.name as customer_name
            FROM crm_contacts c
            LEFT JOIN parties p ON c.customer_id = p.id
            WHERE {' AND '.join(conditions)}
            ORDER BY c.is_primary DESC, c.first_name
        """), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.post("/contacts", status_code=201, dependencies=[Depends(require_permission("sales.create"))])
def create_contact(data: ContactCreate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        # If setting as primary, unset others
        if data.is_primary:
            db.execute(text("UPDATE crm_contacts SET is_primary = FALSE WHERE customer_id = :cid"),
                       {"cid": data.customer_id})

        cid = db.execute(text("""
            INSERT INTO crm_contacts (
                customer_id, first_name, last_name, job_title,
                email, phone, mobile, department,
                is_primary, is_decision_maker, notes, created_by
            ) VALUES (
                :cust, :fname, :lname, :title,
                :email, :phone, :mobile, :dept,
                :primary, :decision, :notes, :uid
            ) RETURNING id
        """), {
            "cust": data.customer_id, "fname": data.first_name,
            "lname": data.last_name, "title": data.job_title,
            "email": data.email, "phone": data.phone,
            "mobile": data.mobile, "dept": data.department,
            "primary": data.is_primary, "decision": data.is_decision_maker,
            "notes": data.notes, "uid": current_user.id
        }).scalar()
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_create_contact", resource_type="contact", resource_id=str(cid), details={"customer_id": data.customer_id, "first_name": data.first_name}, request=request)
        return {"id": cid, "message": "تم إنشاء جهة الاتصال"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(**http_error(500, "internal_error"))
    finally:
        db.close()


@router.put("/contacts/{contact_id}", dependencies=[Depends(require_permission("sales.create"))])
def update_contact(contact_id: int, data: ContactUpdate, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(**http_error(400, "no_data"))

        # If setting as primary, unset others for same customer  
        if updates.get("is_primary"):
            contact = db.execute(text("SELECT customer_id FROM crm_contacts WHERE id = :id"),
                                 {"id": contact_id}).fetchone()
            if contact:
                db.execute(text("UPDATE crm_contacts SET is_primary = FALSE WHERE customer_id = :cid"),
                           {"cid": contact.customer_id})

        updates["id"] = contact_id
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        db.execute(text(f"UPDATE crm_contacts SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_update_contact", resource_type="contact", resource_id=str(contact_id), details={"fields_updated": list(updates.keys())}, request=request)
        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.delete("/contacts/{contact_id}", dependencies=[Depends(require_permission("sales.delete"))])
def delete_contact(contact_id: int, request: Request, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM crm_contacts WHERE id = :id"), {"id": contact_id})
        db.commit()
        log_activity(db, user_id=current_user.id, username=getattr(current_user, "username", ""), action="crm_delete_contact", resource_type="contact", resource_id=str(contact_id), details={}, request=request)
        return {"message": "تم الحذف"}
    finally:
        db.close()


# ======================== CRM-009: Pipeline Analytics & Dashboard ========================

@router.get("/analytics/pipeline", dependencies=[Depends(require_permission("sales.view"))])
def pipeline_analytics(current_user=Depends(get_current_user)):
    """تحليلات خط أنابيب المبيعات — معدلات التحويل وسرعة المبيعات"""
    db = get_db_connection(current_user.company_id)
    try:
        # Stage conversion funnel
        funnel = db.execute(text("""
            SELECT stage,
                   COUNT(*) as count,
                   COALESCE(SUM(expected_value), 0) as total_value,
                   COALESCE(AVG(expected_value), 0) as avg_deal_size
            FROM sales_opportunities
            GROUP BY stage
            ORDER BY CASE stage
                WHEN 'lead' THEN 1 WHEN 'qualified' THEN 2
                WHEN 'proposal' THEN 3 WHEN 'negotiation' THEN 4
                WHEN 'won' THEN 5 WHEN 'lost' THEN 6
            END
        """)).fetchall()

        # Win rate
        win_rate = db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE stage = 'won') as won,
                COUNT(*) FILTER (WHERE stage = 'lost') as lost,
                COUNT(*) FILTER (WHERE stage IN ('won','lost')) as closed,
                CASE WHEN COUNT(*) FILTER (WHERE stage IN ('won','lost')) > 0
                     THEN ROUND(100.0 * COUNT(*) FILTER (WHERE stage = 'won') /
                          COUNT(*) FILTER (WHERE stage IN ('won','lost')), 1)
                     ELSE 0 END as win_rate_pct
            FROM sales_opportunities
        """)).fetchone()

        # Sales velocity: avg days to close won deals
        velocity = db.execute(text("""
            SELECT
                COALESCE(AVG(EXTRACT(DAY FROM (updated_at - created_at))), 0) as avg_days_to_close,
                COALESCE(AVG(expected_value), 0) as avg_deal_value,
                COUNT(*) as total_won
            FROM sales_opportunities WHERE stage = 'won'
        """)).fetchone()

        # Monthly trend (last 12 months)
        monthly = db.execute(text("""
            SELECT TO_CHAR(created_at, 'YYYY-MM') as month,
                   COUNT(*) as created,
                   COUNT(*) FILTER (WHERE stage = 'won') as won,
                   COUNT(*) FILTER (WHERE stage = 'lost') as lost,
                   COALESCE(SUM(expected_value) FILTER (WHERE stage = 'won'), 0) as won_value
            FROM sales_opportunities
            WHERE created_at >= NOW() - INTERVAL '12 months'
            GROUP BY TO_CHAR(created_at, 'YYYY-MM')
            ORDER BY month
        """)).fetchall()

        # Top performers
        top_reps = db.execute(text("""
            SELECT cu.username, cu.full_name,
                   COUNT(*) FILTER (WHERE o.stage = 'won') as wins,
                   COALESCE(SUM(o.expected_value) FILTER (WHERE o.stage = 'won'), 0) as total_value,
                   COUNT(*) as total_assigned
            FROM sales_opportunities o
            JOIN company_users cu ON o.assigned_to = cu.id
            GROUP BY cu.id, cu.username, cu.full_name
            ORDER BY total_value DESC
            LIMIT 10
        """)).fetchall()

        # Source analysis
        sources = db.execute(text("""
            SELECT COALESCE(source, 'غير محدد') as source,
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE stage = 'won') as won,
                   COALESCE(SUM(expected_value) FILTER (WHERE stage = 'won'), 0) as won_value
            FROM sales_opportunities
            GROUP BY source
            ORDER BY won_value DESC
        """)).fetchall()

        return {
            "funnel": [dict(r._mapping) for r in funnel],
            "win_rate": dict(win_rate._mapping) if win_rate else {},
            "velocity": dict(velocity._mapping) if velocity else {},
            "monthly_trend": [dict(r._mapping) for r in monthly],
            "top_performers": [dict(r._mapping) for r in top_reps],
            "source_analysis": [dict(r._mapping) for r in sources]
        }
    finally:
        db.close()


@router.get("/analytics/forecast", dependencies=[Depends(require_permission("sales.view"))])
def sales_forecast(current_user=Depends(get_current_user)):
    """توقعات المبيعات المبنية على خط الأنابيب"""
    db = get_db_connection(current_user.company_id)
    try:
        # Weighted pipeline value
        weighted = db.execute(text("""
            SELECT
                COALESCE(SUM(expected_value * probability / 100.0), 0) as weighted_value,
                COALESCE(SUM(expected_value), 0) as total_pipeline,
                COUNT(*) as active_deals
            FROM sales_opportunities
            WHERE stage NOT IN ('won', 'lost')
        """)).fetchone()

        # By expected close month
        by_month = db.execute(text("""
            SELECT TO_CHAR(expected_close_date, 'YYYY-MM') as month,
                   COUNT(*) as deals,
                   COALESCE(SUM(expected_value), 0) as total_value,
                   COALESCE(SUM(expected_value * probability / 100.0), 0) as weighted_value
            FROM sales_opportunities
            WHERE stage NOT IN ('won', 'lost') AND expected_close_date IS NOT NULL
            GROUP BY TO_CHAR(expected_close_date, 'YYYY-MM')
            ORDER BY month
        """)).fetchall()

        # Historical actuals for comparison
        actuals = db.execute(text("""
            SELECT TO_CHAR(updated_at, 'YYYY-MM') as month,
                   COALESCE(SUM(expected_value), 0) as actual_value,
                   COUNT(*) as deals_won
            FROM sales_opportunities
            WHERE stage = 'won' AND updated_at >= NOW() - INTERVAL '12 months'
            GROUP BY TO_CHAR(updated_at, 'YYYY-MM')
            ORDER BY month
        """)).fetchall()

        # Best/Worst/Most Likely scenarios
        scenarios = db.execute(text("""
            SELECT
                COALESCE(SUM(expected_value) FILTER (WHERE probability >= 75), 0) as commit_value,
                COALESCE(SUM(expected_value) FILTER (WHERE probability >= 50), 0) as best_case,
                COALESCE(SUM(expected_value * probability / 100.0), 0) as most_likely
            FROM sales_opportunities
            WHERE stage NOT IN ('won', 'lost')
        """)).fetchone()

        return {
            "weighted_pipeline": dict(weighted._mapping) if weighted else {},
            "by_month": [dict(r._mapping) for r in by_month],
            "historical_actuals": [dict(r._mapping) for r in actuals],
            "scenarios": dict(scenarios._mapping) if scenarios else {}
        }
    finally:
        db.close()


@router.get("/dashboard", dependencies=[Depends(require_permission("sales.view"))])
def crm_dashboard(current_user=Depends(get_current_user)):
    """لوحة معلومات CRM الشاملة"""
    db = get_db_connection(current_user.company_id)
    try:
        # Summary KPIs
        kpis = db.execute(text("""
            SELECT
                COUNT(*) as total_opportunities,
                COUNT(*) FILTER (WHERE stage NOT IN ('won','lost')) as active_opps,
                COUNT(*) FILTER (WHERE stage = 'won') as won_opps,
                COUNT(*) FILTER (WHERE stage = 'lost') as lost_opps,
                COALESCE(SUM(expected_value) FILTER (WHERE stage = 'won'), 0) as total_won_value,
                COALESCE(SUM(expected_value) FILTER (WHERE stage NOT IN ('won','lost')), 0) as pipeline_value,
                COALESCE(AVG(expected_value) FILTER (WHERE stage = 'won'), 0) as avg_deal_size
            FROM sales_opportunities
        """)).fetchone()

        # Tickets summary
        tickets = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'open') as open_tickets,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                COUNT(*) FILTER (WHERE priority IN ('critical','high') AND status NOT IN ('resolved','closed')) as urgent,
                COALESCE(AVG(EXTRACT(EPOCH FROM (COALESCE(resolved_at, NOW()) - created_at)) / 3600)
                    FILTER (WHERE resolved_at IS NOT NULL), 0) as avg_resolution_hrs
            FROM support_tickets
        """)).fetchone()

        # Campaigns summary
        campaigns = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COALESCE(SUM(budget), 0) as total_budget,
                COALESCE(SUM(total_responded), 0) as total_conversions
            FROM marketing_campaigns
        """)).fetchone()

        # Pipeline by stage
        pipeline_by_stage = db.execute(text("""
            SELECT stage,
                   COUNT(*) as count,
                   COALESCE(SUM(expected_value), 0) as total_value
            FROM sales_opportunities
            GROUP BY stage
            ORDER BY CASE stage
                WHEN 'lead' THEN 1 WHEN 'qualified' THEN 2
                WHEN 'proposal' THEN 3 WHEN 'negotiation' THEN 4
                WHEN 'won' THEN 5 WHEN 'lost' THEN 6 END
        """)).fetchall()

        # Win rate
        win_rate_row = db.execute(text("""
            SELECT CASE WHEN COUNT(*) FILTER (WHERE stage IN ('won','lost')) > 0
                        THEN ROUND(100.0 * COUNT(*) FILTER (WHERE stage = 'won') /
                             COUNT(*) FILTER (WHERE stage IN ('won','lost')), 1)
                        ELSE 0 END as win_rate
            FROM sales_opportunities
        """)).fetchone()

        # Recent activities
        recent = db.execute(text("""
            SELECT a.*, o.title as opportunity_title
            FROM opportunity_activities a
            JOIN sales_opportunities o ON a.opportunity_id = o.id
            ORDER BY a.created_at DESC LIMIT 10
        """)).fetchall()

        # Lead scores distribution
        scores_dist = db.execute(text("""
            SELECT grade, COUNT(*) as count
            FROM crm_lead_scores
            GROUP BY grade
            ORDER BY grade
        """)).fetchall()

        kpis_dict = dict(kpis._mapping) if kpis else {}
        kpis_dict['win_rate'] = float(win_rate_row.win_rate) if win_rate_row else 0

        return {
            "kpis": kpis_dict,
            "tickets": dict(tickets._mapping) if tickets else {},
            "campaigns": dict(campaigns._mapping) if campaigns else {},
            "pipeline_by_stage": [dict(r._mapping) for r in pipeline_by_stage],
            "recent_activities": [dict(r._mapping) for r in recent],
            "lead_score_distribution": [dict(r._mapping) for r in scores_dist]
        }
    finally:
        db.close()


@router.get("/analytics/conversion", dependencies=[Depends(require_permission("sales.view"))])
def conversion_analytics(current_user=Depends(get_current_user)):
    """تحليلات معدلات التحويل"""
    db = get_db_connection(current_user.company_id)
    try:
        # Win/Loss rate
        rates = db.execute(text("""
            SELECT
                COUNT(*) as total_closed,
                COUNT(*) FILTER (WHERE stage = 'won') as won,
                COUNT(*) FILTER (WHERE stage = 'lost') as lost,
                CASE WHEN COUNT(*) FILTER (WHERE stage IN ('won','lost')) > 0
                     THEN ROUND(100.0 * COUNT(*) FILTER (WHERE stage = 'won') /
                          COUNT(*) FILTER (WHERE stage IN ('won','lost')), 1) ELSE 0 END as win_rate,
                CASE WHEN COUNT(*) FILTER (WHERE stage IN ('won','lost')) > 0
                     THEN ROUND(100.0 * COUNT(*) FILTER (WHERE stage = 'lost') /
                          COUNT(*) FILTER (WHERE stage IN ('won','lost')), 1) ELSE 0 END as loss_rate,
                COALESCE(AVG(EXTRACT(DAY FROM (updated_at - created_at)))
                    FILTER (WHERE stage = 'won'), 0) as avg_days_to_close
            FROM sales_opportunities
        """)).fetchone()

        # Conversion by source
        by_source = db.execute(text("""
            SELECT COALESCE(source, 'غير محدد') as source,
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE stage = 'won') as won,
                   CASE WHEN COUNT(*) > 0
                        THEN ROUND(100.0 * COUNT(*) FILTER (WHERE stage = 'won') / COUNT(*), 1)
                        ELSE 0 END as conversion_rate
            FROM sales_opportunities
            WHERE stage IN ('won', 'lost')
            GROUP BY source
            ORDER BY conversion_rate DESC
        """)).fetchall()

        # Stage-to-stage conversion
        stage_conv = db.execute(text("""
            SELECT stage,
                   COUNT(*) as count,
                   COALESCE(SUM(expected_value), 0) as value
            FROM sales_opportunities
            GROUP BY stage
            ORDER BY CASE stage
                WHEN 'lead' THEN 1 WHEN 'qualified' THEN 2
                WHEN 'proposal' THEN 3 WHEN 'negotiation' THEN 4
                WHEN 'won' THEN 5 WHEN 'lost' THEN 6 END
        """)).fetchall()

        return {
            "win_rate": float(rates.win_rate) if rates else 0,
            "loss_rate": float(rates.loss_rate) if rates else 0,
            "avg_days_to_close": float(rates.avg_days_to_close) if rates else 0,
            "total_closed": rates.total_closed if rates else 0,
            "won": rates.won if rates else 0,
            "lost": rates.lost if rates else 0,
            "by_source": [dict(r._mapping) for r in by_source],
            "stage_distribution": [dict(r._mapping) for r in stage_conv]
        }
    finally:
        db.close()


@router.get("/analytics/campaign-roi", dependencies=[Depends(require_permission("sales.view"))])
def campaign_roi_analytics(current_user=Depends(get_current_user)):
    """تحليل العائد على الاستثمار في الحملات"""
    db = get_db_connection(current_user.company_id)
    try:
        rows = db.execute(text("""
            SELECT id, name, campaign_type, status, budget,
                   COALESCE(total_sent, 0) as sent,
                   COALESCE(total_opened, 0) as opens,
                   COALESCE(total_clicked, 0) as clicks,
                   COALESCE(total_responded, 0) as conversions,
                   CASE WHEN COALESCE(total_sent, 0) > 0
                        THEN ROUND(100.0 * COALESCE(total_opened, 0) / total_sent, 1) ELSE 0 END as open_rate,
                   CASE WHEN COALESCE(total_opened, 0) > 0
                        THEN ROUND(100.0 * COALESCE(total_clicked, 0) / total_opened, 1) ELSE 0 END as click_rate,
                   CASE WHEN COALESCE(total_sent, 0) > 0
                        THEN ROUND(100.0 * COALESCE(total_responded, 0) / total_sent, 1) ELSE 0 END as conversion_rate,
                   CASE WHEN budget > 0 AND COALESCE(total_responded, 0) > 0
                        THEN ROUND(budget / total_responded, 2) ELSE 0 END as cost_per_conversion,
                   start_date, end_date
            FROM marketing_campaigns
            ORDER BY COALESCE(total_responded, 0) DESC
        """)).fetchall()

        # Summary
        summary = db.execute(text("""
            SELECT
                COALESCE(SUM(budget), 0) as total_investment,
                COALESCE(SUM(total_responded), 0) as total_conversions,
                CASE WHEN SUM(COALESCE(total_responded, 0)) > 0
                     THEN ROUND(SUM(budget) / SUM(total_responded), 2) ELSE 0 END as avg_cpc,
                CASE WHEN SUM(COALESCE(total_sent, 0)) > 0
                     THEN ROUND(100.0 * SUM(COALESCE(total_responded, 0)) / SUM(total_sent), 2)
                     ELSE 0 END as overall_conversion_rate
            FROM marketing_campaigns
        """)).fetchone()

        return {
            "campaigns": [dict(r._mapping) for r in rows],
            "summary": dict(summary._mapping) if summary else {}
        }
    finally:
        db.close()
