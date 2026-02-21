"""
Approval Workflow Utility
=========================
Helper to automatically submit documents for approval if a matching workflow exists.
Used by purchases, expenses, and HR modules.
"""
from sqlalchemy import text
import logging

logger = logging.getLogger("aman.approvals")


def try_submit_for_approval(
    db,
    document_type: str,
    document_id: int,
    document_number: str,
    amount: float,
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
        amount: Total amount for threshold matching
        submitted_by: User ID who submitted the document
        description: Human-readable description
        link: Optional link to the document in the frontend
    
    Returns:
        dict with approval_request_id if submitted, or None if no workflow matches
    """
    try:
        # 1. Find matching workflow
        workflow = db.execute(text("""
            SELECT w.id, w.name 
            FROM approval_workflows w
            WHERE w.document_type = :dtype 
              AND w.is_active = TRUE
              AND (w.min_amount IS NULL OR w.min_amount <= :amount)
              AND (w.max_amount IS NULL OR w.max_amount >= :amount)
            ORDER BY w.min_amount DESC NULLS LAST
            LIMIT 1
        """), {"dtype": document_type, "amount": amount}).fetchone()
        
        if not workflow:
            return None  # No workflow = no approval required
        
        # 2. Get first step
        first_step = db.execute(text("""
            SELECT id, step, approver_role, approver_user_id, label
            FROM approval_workflow_steps
            WHERE workflow_id = :wid
            ORDER BY step ASC
            LIMIT 1
        """), {"wid": workflow.id}).fetchone()
        
        if not first_step:
            logger.warning(f"Workflow {workflow.id} has no steps, skipping approval")
            return None
        
        # 3. Create approval request
        request_id = db.execute(text("""
            INSERT INTO approval_requests (
                workflow_id, document_type, document_id, document_number,
                amount, description, submitted_by, current_step, status
            ) VALUES (
                :wid, :dtype, :did, :dnum,
                :amount, :desc, :uid, 1, 'pending'
            ) RETURNING id
        """), {
            "wid": workflow.id,
            "dtype": document_type,
            "did": document_id,
            "dnum": document_number,
            "amount": amount,
            "desc": description or f"{document_type} #{document_number}",
            "uid": submitted_by
        }).scalar()
        
        # 4. Notify the approver(s) at step 1
        if first_step.approver_user_id:
            # Notify specific user
            _create_notification(
                db,
                user_id=first_step.approver_user_id,
                title=f"طلب اعتماد جديد: {document_number}",
                message=description or f"طلب اعتماد {document_type} بمبلغ {amount:,.2f}",
                link=link or f"/approvals"
            )
        elif first_step.approver_role:
            # Notify all users with this role
            approvers = db.execute(text("""
                SELECT id FROM company_users 
                WHERE role = :role AND is_active = TRUE
            """), {"role": first_step.approver_role}).fetchall()
            
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
