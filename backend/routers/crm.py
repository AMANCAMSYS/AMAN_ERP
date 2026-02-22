"""
AMAN ERP - CRM Router
CRM-002: Sales Opportunities (Leads → Won/Lost pipeline)
CRM-004: Support Tickets with comments and SLA
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from typing import List, Dict, Any, Optional

from datetime import datetime
from pydantic import BaseModel
import logging

from database import get_db_connection
from routers.auth import get_current_user
from utils.permissions import require_permission
from utils.accounting import generate_sequential_number

router = APIRouter(prefix="/crm", tags=["إدارة العلاقات CRM"])
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
            raise HTTPException(404, "الفرصة غير موجودة")
        
        activities = db.execute(text("""
            SELECT * FROM opportunity_activities WHERE opportunity_id = :id ORDER BY created_at DESC
        """), {"id": opp_id}).fetchall()
        
        result = dict(opp._mapping)
        result["activities"] = [dict(a._mapping) for a in activities]
        return result
    finally:
        db.close()


@router.post("/opportunities", status_code=201, dependencies=[Depends(require_permission(["sales.create", "projects.create"]))])
def create_opportunity(data: OpportunityCreate, current_user=Depends(get_current_user)):
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
        return {"id": opp_id, "message": "تم إنشاء الفرصة البيعية"}
    finally:
        db.close()


@router.put("/opportunities/{opp_id}", dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
def update_opportunity(opp_id: int, data: OpportunityUpdate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(400, "لا توجد بيانات للتحديث")
        
        # Auto-set probability based on stage
        if "stage" in updates and updates["stage"] in OPPORTUNITY_STAGES:
            if "probability" not in updates:
                updates["probability"] = OPPORTUNITY_STAGES[updates["stage"]]
        
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = opp_id
        db.execute(text(f"UPDATE sales_opportunities SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.delete("/opportunities/{opp_id}", dependencies=[Depends(require_permission(["sales.delete", "projects.delete"]))])
def delete_opportunity(opp_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM sales_opportunities WHERE id = :id"), {"id": opp_id})
        db.commit()
        return {"message": "تم حذف الفرصة"}
    finally:
        db.close()


@router.post("/opportunities/{opp_id}/activities", status_code=201,
             dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
def add_activity(opp_id: int, data: ActivityCreate, current_user=Depends(get_current_user)):
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
        
        # SLA check
        if ticket.status not in ('resolved', 'closed'):
            hours_open = (datetime.now() - ticket.created_at).total_seconds() / 3600
            result["sla_breached"] = hours_open > (ticket.sla_hours or 24)
            result["hours_open"] = round(hours_open, 1)
        
        return result
    finally:
        db.close()


@router.post("/tickets", status_code=201,
             dependencies=[Depends(require_permission(["sales.create", "projects.create"]))])
def create_ticket(data: TicketCreate, current_user=Depends(get_current_user)):
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
        
        return {"id": tid, "ticket_number": ticket_num, "message": "تم إنشاء التذكرة"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.put("/tickets/{ticket_id}", dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
def update_ticket(ticket_id: int, data: TicketUpdate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(400, "لا توجد بيانات للتحديث")
        
        # Auto-set timestamps
        if updates.get("status") == "resolved":
            updates["resolved_at"] = datetime.now()
        elif updates.get("status") == "closed":
            updates["closed_at"] = datetime.now()
        
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = ticket_id
        db.execute(text(f"UPDATE support_tickets SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        return {"message": "تم التحديث"}
    finally:
        db.close()


@router.post("/tickets/{ticket_id}/comments", status_code=201,
             dependencies=[Depends(require_permission(["sales.create", "projects.edit"]))])
def add_comment(ticket_id: int, data: CommentCreate, current_user=Depends(get_current_user)):
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
        return {"id": cid}
    finally:
        db.close()


# ======================== CRM-001: Convert Opportunity to Quotation ========================

@router.post("/opportunities/{opp_id}/convert-quotation", status_code=201,
             dependencies=[Depends(require_permission("sales.create"))])
def convert_to_quotation(opp_id: int, current_user=Depends(get_current_user)):
    """تحويل فرصة بيعية إلى عرض سعر"""
    db = get_db_connection(current_user.company_id)
    try:
        opp = db.execute(text("SELECT * FROM sales_opportunities WHERE id = :id"), {"id": opp_id}).fetchone()
        if not opp:
            raise HTTPException(status_code=404, detail="الفرصة غير موجودة")
        opp = opp._mapping

        if not opp.get("customer_id"):
            raise HTTPException(status_code=400, detail="يجب تحديد عميل للفرصة قبل التحويل")

        # Generate quotation number
        quot_num = generate_sequential_number(db, f"QT-{datetime.now().year}", "sales_quotations", "quotation_number")

        quot_id = db.execute(text("""
            INSERT INTO sales_quotations (
                quotation_number, customer_id, quotation_date, valid_until,
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

        # Add a quotation line with opportunity value
        if opp.get("expected_value") and opp["expected_value"] > 0:
            db.execute(text("""
                INSERT INTO sales_quotation_lines (quotation_id, description, quantity, unit_price, tax_rate, discount, total)
                VALUES (:qid, :desc, 1, :price, 0, 0, :price)
            """), {
                "qid": quot_id,
                "desc": opp["title"],
                "price": opp["expected_value"]
            })

        # Update opportunity stage to 'proposal'
        db.execute(text("UPDATE sales_opportunities SET stage = 'proposal', updated_at = NOW() WHERE id = :id"), {"id": opp_id})
        db.commit()

        return {"quotation_id": quot_id, "quotation_number": quot_num, "message": "تم تحويل الفرصة إلى عرض سعر"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ======================== CRM-003: Marketing Campaigns ========================

class CampaignCreate(BaseModel):
    name: str
    campaign_type: str = "email"  # email, sms, social, event
    status: str = "draft"  # draft, active, paused, completed
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: float = 0
    target_audience: Optional[str] = None
    description: Optional[str] = None
    branch_id: Optional[int] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    campaign_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    target_audience: Optional[str] = None
    description: Optional[str] = None
    sent_count: Optional[int] = None
    open_count: Optional[int] = None
    click_count: Optional[int] = None
    conversion_count: Optional[int] = None


@router.get("/campaigns", dependencies=[Depends(require_permission("sales.view"))])
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
            LEFT JOIN users u ON c.created_by = u.id
            WHERE {' AND '.join(conditions)}
            ORDER BY c.created_at DESC
        """), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


@router.get("/campaigns/{campaign_id}", dependencies=[Depends(require_permission("sales.view"))])
def get_campaign(campaign_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        row = db.execute(text("SELECT * FROM marketing_campaigns WHERE id = :id"), {"id": campaign_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="الحملة غير موجودة")
        return dict(row._mapping)
    finally:
        db.close()


@router.post("/campaigns", status_code=201, dependencies=[Depends(require_permission("sales.create"))])
def create_campaign(data: CampaignCreate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        cid = db.execute(text("""
            INSERT INTO marketing_campaigns (
                name, campaign_type, status, start_date, end_date,
                budget, target_audience, description, created_by, branch_id
            ) VALUES (
                :name, :type, :status, :start, :end,
                :budget, :audience, :desc, :uid, :branch
            ) RETURNING id
        """), {
            "name": data.name, "type": data.campaign_type, "status": data.status,
            "start": data.start_date, "end": data.end_date,
            "budget": data.budget, "audience": data.target_audience,
            "desc": data.description, "uid": current_user.id, "branch": data.branch_id
        }).scalar()
        db.commit()
        return {"id": cid, "message": "تم إنشاء الحملة"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/campaigns/{campaign_id}", dependencies=[Depends(require_permission("sales.create"))])
def update_campaign(campaign_id: int, data: CampaignUpdate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")
        updates["id"] = campaign_id
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        db.execute(text(f"UPDATE marketing_campaigns SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        return {"message": "تم تحديث الحملة"}
    finally:
        db.close()


@router.delete("/campaigns/{campaign_id}", dependencies=[Depends(require_permission("sales.create"))])
def delete_campaign(campaign_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM marketing_campaigns WHERE id = :id"), {"id": campaign_id})
        db.commit()
        return {"message": "تم حذف الحملة"}
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
            FROM knowledge_base kb
            LEFT JOIN users u ON kb.created_by = u.id
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
        db.execute(text("UPDATE knowledge_base SET views = COALESCE(views, 0) + 1 WHERE id = :id"), {"id": article_id})
        db.commit()
        row = db.execute(text("""
            SELECT kb.*, u.full_name as author_name
            FROM knowledge_base kb LEFT JOIN users u ON kb.created_by = u.id
            WHERE kb.id = :id
        """), {"id": article_id}).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="المقالة غير موجودة")
        return dict(row._mapping)
    finally:
        db.close()


@router.post("/knowledge-base", status_code=201, dependencies=[Depends(require_permission("sales.create"))])
def create_article(data: ArticleCreate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        aid = db.execute(text("""
            INSERT INTO knowledge_base (title, category, content, tags, is_published, created_by)
            VALUES (:title, :cat, :content, :tags, :pub, :uid) RETURNING id
        """), {
            "title": data.title, "cat": data.category, "content": data.content,
            "tags": data.tags, "pub": data.is_published, "uid": current_user.id
        }).scalar()
        db.commit()
        return {"id": aid, "message": "تم إنشاء المقالة"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/knowledge-base/{article_id}", dependencies=[Depends(require_permission("sales.create"))])
def update_article(article_id: int, data: ArticleUpdate, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        updates = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="لا توجد بيانات للتحديث")
        updates["id"] = article_id
        set_clause = ", ".join(f"{k} = :{k}" for k in updates if k != "id")
        db.execute(text(f"UPDATE knowledge_base SET {set_clause}, updated_at = NOW() WHERE id = :id"), updates)
        db.commit()
        return {"message": "تم تحديث المقالة"}
    finally:
        db.close()


@router.delete("/knowledge-base/{article_id}", dependencies=[Depends(require_permission("sales.create"))])
def delete_article(article_id: int, current_user=Depends(get_current_user)):
    db = get_db_connection(current_user.company_id)
    try:
        db.execute(text("DELETE FROM knowledge_base WHERE id = :id"), {"id": article_id})
        db.commit()
        return {"message": "تم حذف المقالة"}
    finally:
        db.close()
