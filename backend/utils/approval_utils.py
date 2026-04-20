"""
Approval Workflow Utility
=========================
Helper to automatically submit documents for approval if a matching workflow exists.
Used by purchases, expenses, and HR modules.
"""
from decimal import Decimal
from sqlalchemy import text
import json
import logging

logger = logging.getLogger("aman.approvals")


def try_submit_for_approval(
    db,
    document_type: str,
    document_id: int,
    document_number: str,
    amount: Decimal,
    submitted_by: int,
    description: str = "",
    link: str = None
) -> dict:
    """
    Check if an approval workflow exists for this document type/amount.
    If yes, create an approval request. If no workflow, return None.
    
    Args:
        db: Database connection
        document_type: One of 'purchase_order', 'expense', 'leave_request', etc.
        document_id: ID of the document
        document_number: Document number for display
        amount: Total amount for threshold matching (Decimal)
        submitted_by: User ID who submitted the document
        description: Human-readable description
        link: Optional link to the document in the frontend
    
    Returns:
        dict with approval_request_id if submitted, or None if no workflow matches
    """
    try:
        # 1. Find matching workflow — read thresholds from conditions JSONB
        workflow = db.execute(text("""
            SELECT w.id, w.name, w.steps
            FROM approval_workflows w
            WHERE w.document_type = :dtype 
              AND w.is_active = TRUE
              AND (w.conditions->>'min_amount' IS NULL OR (w.conditions->>'min_amount')::numeric <= :amount)
              AND (w.conditions->>'max_amount' IS NULL OR (w.conditions->>'max_amount')::numeric >= :amount)
            ORDER BY (w.conditions->>'min_amount')::numeric DESC NULLS LAST
            LIMIT 1
        """), {"dtype": document_type, "amount": amount}).fetchone()
        
        if not workflow:
            return None  # No workflow = no approval required
        
        # 2. Get first step from steps JSONB column (no separate table)
        steps_raw = workflow.steps
        if isinstance(steps_raw, str):
            steps_raw = json.loads(steps_raw)
        steps = steps_raw if isinstance(steps_raw, list) else []
        
        if not steps:
            logger.warning(f"Workflow {workflow.id} has no steps, skipping approval")
            return None
        
        # Sort by order/step field and take the first
        first_step = sorted(steps, key=lambda s: s.get('order', s.get('step', 1)))[0]
        
        # 3. Create approval request
        request_id = db.execute(text("""
            INSERT INTO approval_requests (
                workflow_id, document_type, document_id, document_number,
                amount, description, submitted_by, current_step, total_steps, status
            ) VALUES (
                :wid, :dtype, :did, :dnum,
                :amount, :desc, :uid, 1, :total_steps, 'pending'
            ) RETURNING id
        """), {
            "wid": workflow.id,
            "dtype": document_type,
            "did": document_id,
            "dnum": document_number,
            "amount": amount,
            "desc": description or f"{document_type} #{document_number}",
            "uid": submitted_by,
            "total_steps": len(steps)
        }).scalar()
        
        # 4. Notify the approver(s) at step 1
        approver_user_id = first_step.get('approver_user_id') or first_step.get('approver_id')
        approver_role = first_step.get('approver_role')
        
        if approver_user_id:
            # Notify specific user
            _create_notification(
                db,
                user_id=approver_user_id,
                title=f"طلب اعتماد جديد: {document_number}",
                message=description or f"طلب اعتماد {document_type} بمبلغ {amount:,.2f}",
                link=link or f"/approvals"
            )
        elif approver_role:
            # Notify all users with this role
            approvers = db.execute(text("""
                SELECT id FROM company_users 
                WHERE role = :role AND is_active = TRUE
            """), {"role": approver_role}).fetchall()
            
            for approver in approvers:
                _create_notification(
                    db,
                    user_id=approver.id,
                    title=f"طلب اعتماد جديد: {document_number}",
                    message=description or f"طلب اعتماد {document_type} بمبلغ {amount:,.2f}",
                    link=link or f"/approvals"
                )
        
        logger.info(f"Created approval request #{request_id} for {document_type} #{document_number}")
        return {
            "approval_request_id": request_id,
            "workflow_name": workflow.name,
            "status": "pending_approval"
        }
        
    except Exception as e:
        logger.warning(f"Could not create approval request: {e}")
        # Don't fail the document creation if approval fails
        return None


def _create_notification(db, user_id: int, title: str, message: str, link: str = None):
    """Helper to create a notification."""
    try:
        db.execute(text("""
            INSERT INTO notifications (user_id, title, message, link, type, is_read)
            VALUES (:uid, :title, :msg, :link, 'approval', FALSE)
        """), {"uid": user_id, "title": title, "msg": message, "link": link})
    except Exception as e:
        logger.warning(f"Could not create notification: {e}")
