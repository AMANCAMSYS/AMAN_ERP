"""
Checks Management Router - TRS-001 & TRS-002
إدارة الشيكات تحت التحصيل والدفع
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from database import get_db_connection
from routers.auth import get_current_user
from utils.audit import log_activity
from utils.permissions import require_permission, validate_branch_access
from utils.accounting import update_account_balance, get_base_currency
from datetime import date, datetime
from typing import Optional

router = APIRouter(prefix="/checks", tags=["checks"])


def _ensure_checks_accounts(db):
    """Ensure accounts 1205 (Checks Receivable) and 2105 (Checks Payable) exist."""
    for code, nm, nm_en, acc_type, parent_prefix in [
        ('1205', 'شيكات تحت التحصيل', 'Checks Under Collection', 'asset', '12'),
        ('2105', 'شيكات تحت الدفع', 'Checks Payable', 'liability', '21'),
    ]:
        existing = db.execute(text(
            "SELECT id FROM accounts WHERE account_code = :code"
        ), {"code": code}).fetchone()
        if not existing:
            parent = db.execute(text(
                "SELECT id FROM accounts WHERE account_code = :code"
            ), {"code": parent_prefix + '00'}).fetchone()
            db.execute(text("""
                INSERT INTO accounts (account_number, account_code, name, name_en, account_type, parent_id, is_active, currency)
                VALUES (:code, :code, :name, :name_en, :type, :pid, TRUE, :currency)
                ON CONFLICT (account_number) DO NOTHING
            """), {"code": code, "name": nm, "name_en": nm_en, "type": acc_type,
                   "pid": parent.id if parent else None, "currency": get_base_currency(db)})
            db.commit()


# ============================================================
# TRS-001: شيكات تحت التحصيل - Checks Receivable
# ============================================================

@router.get("/receivable", dependencies=[Depends(require_permission("treasury.view"))])
def list_checks_receivable(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    """List all checks receivable with filters"""
    # Validate branch access
    branch_id = validate_branch_access(current_user, branch_id)
    
    db = get_db_connection(current_user.company_id)
    try:
        offset = (page - 1) * limit
        conditions = []
        params = {"limit": limit, "offset": offset}

        if status:
            conditions.append("cr.status = :status")
            params["status"] = status
        if search:
            conditions.append("(cr.check_number ILIKE :search OR cr.drawer_name ILIKE :search OR cr.bank_name ILIKE :search)")
            params["search"] = f"%{search}%"
        if branch_id:
            conditions.append("cr.branch_id = :branch_id")
            params["branch_id"] = branch_id

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total = db.execute(text(f"SELECT COUNT(*) FROM checks_receivable cr {where}"), params).scalar() or 0

        rows = db.execute(text(f"""
            SELECT cr.*, p.name as party_name, ta.name as treasury_name
            FROM checks_receivable cr
            LEFT JOIN parties p ON cr.party_id = p.id
            LEFT JOIN treasury_accounts ta ON cr.treasury_account_id = ta.id
            {where}
            ORDER BY cr.due_date ASC
            LIMIT :limit OFFSET :offset
        """), params).fetchall()

        items = []
        for r in rows:
            items.append({
                "id": r.id, "check_number": r.check_number,
                "drawer_name": r.drawer_name, "bank_name": r.bank_name,
                "branch_name": r.branch_name, "amount": float(r.amount),
                "currency": r.currency,
                "issue_date": str(r.issue_date) if r.issue_date else None,
                "due_date": str(r.due_date) if r.due_date else None,
                "collection_date": str(r.collection_date) if r.collection_date else None,
                "bounce_date": str(r.bounce_date) if r.bounce_date else None,
                "party_id": r.party_id, "party_name": r.party_name,
                "treasury_account_id": r.treasury_account_id,
                "treasury_name": r.treasury_name,
                "status": r.status, "bounce_reason": r.bounce_reason,
                "notes": r.notes, "created_at": str(r.created_at) if r.created_at else None,
            })

        return {"items": items, "total": total, "page": page}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/receivable/summary/stats", dependencies=[Depends(require_permission("treasury.view"))])
def checks_receivable_stats(branch_id: Optional[int] = None, current_user=Depends(get_current_user)):
    """Get summary stats for checks receivable"""
    # Validate branch access
    branch_id = validate_branch_access(current_user, branch_id)

    db = get_db_connection(current_user.company_id)
    try:
        cond = "AND branch_id = :branch_id" if branch_id else ""
        params = {"branch_id": branch_id} if branch_id else {}
        stats = db.execute(text(f"""
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'pending'), 0) as pending_amount,
                COUNT(*) FILTER (WHERE status = 'collected') as collected_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'collected'), 0) as collected_amount,
                COUNT(*) FILTER (WHERE status = 'bounced') as bounced_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'bounced'), 0) as bounced_amount,
                COUNT(*) FILTER (WHERE status = 'pending' AND due_date <= CURRENT_DATE) as overdue_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'pending' AND due_date <= CURRENT_DATE), 0) as overdue_amount
            FROM checks_receivable WHERE 1=1 {cond}
        """), params).fetchone()
        return {
            "pending": {"count": stats.pending_count, "amount": float(stats.pending_amount)},
            "collected": {"count": stats.collected_count, "amount": float(stats.collected_amount)},
            "bounced": {"count": stats.bounced_count, "amount": float(stats.bounced_amount)},
            "overdue": {"count": stats.overdue_count, "amount": float(stats.overdue_amount)},
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/receivable/{check_id}", dependencies=[Depends(require_permission("treasury.view"))])
def get_check_receivable(check_id: int, current_user=Depends(get_current_user)):
    """Get single check receivable details"""
    db = get_db_connection(current_user.company_id)
    try:
        r = db.execute(text("""
            SELECT cr.*, p.name as party_name, ta.name as treasury_name
            FROM checks_receivable cr
            LEFT JOIN parties p ON cr.party_id = p.id
            LEFT JOIN treasury_accounts ta ON cr.treasury_account_id = ta.id
            WHERE cr.id = :id
        """), {"id": check_id}).fetchone()
        if not r:
            raise HTTPException(404, "الشيك غير موجود")
        
        # Validate branch access
        validate_branch_access(current_user, r.branch_id)
        
        return {
            "id": r.id, "check_number": r.check_number,
            "drawer_name": r.drawer_name, "bank_name": r.bank_name,
            "branch_name": r.branch_name, "amount": float(r.amount),
            "currency": r.currency,
            "issue_date": str(r.issue_date) if r.issue_date else None,
            "due_date": str(r.due_date) if r.due_date else None,
            "collection_date": str(r.collection_date) if r.collection_date else None,
            "bounce_date": str(r.bounce_date) if r.bounce_date else None,
            "party_id": r.party_id, "party_name": r.party_name,
            "treasury_account_id": r.treasury_account_id,
            "treasury_name": r.treasury_name,
            "status": r.status, "bounce_reason": r.bounce_reason,
            "notes": r.notes,
            "journal_entry_id": r.journal_entry_id,
            "collection_journal_id": r.collection_journal_id,
            "bounce_journal_id": r.bounce_journal_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/receivable", dependencies=[Depends(require_permission("treasury.create"))])
def create_check_receivable(data: dict, current_user=Depends(get_current_user)):
    """
    Create a new check receivable.
    On creation: Dr. Checks Under Collection (1205) / Cr. Accounts Receivable
    """
    db = get_db_connection(current_user.company_id)
    try:
        # Validate branch access
        if data.get("branch_id"):
             validate_branch_access(current_user, data["branch_id"])

        required = ["check_number", "amount", "due_date"]
        for f in required:
            if not data.get(f):
                raise HTTPException(400, f"الحقل {f} مطلوب")

        _ensure_checks_accounts(db)

        amount = float(data["amount"])

        checks_account = db.execute(text(
            "SELECT id FROM accounts WHERE account_code = '1205' LIMIT 1"
        )).fetchone()

        ar_account = db.execute(text(
            "SELECT id FROM accounts WHERE account_code IN ('1201', '1200') AND is_active = TRUE ORDER BY account_code LIMIT 1"
        )).fetchone()

        if not checks_account or not ar_account:
            raise HTTPException(500, "حسابات الشيكات (1205) أو العملاء (1200/1201) غير موجودة. يرجى إعداد دليل الحسابات أولاً.")

        je = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
            VALUES (
                'CHK-R-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-R-%')::text, '1'), 6, '0'),
                :entry_date, :description, 'posted', 'check_receivable', :user_id, :branch_id
            ) RETURNING id
        """), {
            "entry_date": data.get("issue_date", str(date.today())),
            "description": f"استلام شيك رقم {data['check_number']} - {data.get('drawer_name', '')}",
            "user_id": current_user.id,
            "branch_id": data.get("branch_id"),
        }).fetchone()
        je_id = je.id if je else None

        if je_id:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, :amount, 0, :desc)
            """), {"je_id": je_id, "account_id": checks_account.id, "amount": amount,
                   "desc": f"شيك تحت التحصيل {data['check_number']}"})
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, 0, :amount, :desc)
            """), {"je_id": je_id, "account_id": ar_account.id, "amount": amount,
                   "desc": f"شيك تحت التحصيل {data['check_number']}"})

            # Update Account Balances
            update_account_balance(db, account_id=checks_account.id, debit_base=amount, credit_base=0)
            update_account_balance(db, account_id=ar_account.id, debit_base=0, credit_base=amount)

        result = db.execute(text("""
            INSERT INTO checks_receivable (
                check_number, drawer_name, bank_name, branch_name, amount, currency,
                issue_date, due_date, party_id, treasury_account_id, receipt_id,
                journal_entry_id, status, notes, branch_id, created_by
            ) VALUES (
                :check_number, :drawer_name, :bank_name, :branch_name, :amount, :currency,
                :issue_date, :due_date, :party_id, :treasury_id, :receipt_id,
                :je_id, 'pending', :notes, :branch_id, :user_id
            ) RETURNING id
        """), {
            "check_number": data["check_number"],
            "drawer_name": data.get("drawer_name", ""),
            "bank_name": data.get("bank_name", ""),
            "branch_name": data.get("branch_name", ""),
            "amount": amount,
            "currency": data.get("currency", get_base_currency(db)),
            "issue_date": data.get("issue_date"),
            "due_date": data["due_date"],
            "party_id": data.get("party_id"),
            "treasury_id": data.get("treasury_account_id"),
            "receipt_id": data.get("receipt_id"),
            "je_id": je_id,
            "notes": data.get("notes", ""),
            "branch_id": data.get("branch_id"),
            "user_id": current_user.id,
        }).fetchone()

        db.commit()
        try:
            log_activity(db, current_user.id, current_user.username, "create", "checks_receivable", str(result.id),
                         {"check_number": data["check_number"], "amount": amount})
        except Exception:
            pass
        return {"id": result.id, "message": "تم تسجيل الشيك بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/receivable/{check_id}/collect", dependencies=[Depends(require_permission("treasury.create"))])
def collect_check_receivable(check_id: int, data: dict, current_user=Depends(get_current_user)):
    """
    Mark check as collected.
    GL: Dr. Bank (treasury) / Cr. Checks Under Collection (1205)
    """
    db = get_db_connection(current_user.company_id)
    try:
        check = db.execute(text("SELECT * FROM checks_receivable WHERE id = :id"), {"id": check_id}).fetchone()
        if not check:
            raise HTTPException(404, "الشيك غير موجود")
            
        # Validate branch access
        validate_branch_access(current_user, check.branch_id)
        
        if check.status != 'pending':
            raise HTTPException(400, "الشيك ليس في حالة معلق")

        collection_date = data.get("collection_date", str(date.today()))
        treasury_id = data.get("treasury_account_id") or check.treasury_account_id

        if not treasury_id:
            raise HTTPException(400, "يجب تحديد حساب الخزينة/البنك")

        treasury = db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE id = :id"), {"id": treasury_id}).fetchone()
        if not treasury:
            raise HTTPException(404, "حساب الخزينة غير موجود")

        checks_account = db.execute(text("SELECT id FROM accounts WHERE account_code = '1205' LIMIT 1")).fetchone()
        if not checks_account:
            raise HTTPException(500, "حساب الشيكات تحت التحصيل (1205) غير موجود")

        amount = float(check.amount)

        je = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
            VALUES (
                'CHK-C-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-C-%')::text, '1'), 6, '0'),
                :entry_date, :description, 'posted', 'check_collection', :user_id, :branch_id
            ) RETURNING id
        """), {
            "entry_date": collection_date,
            "description": f"تحصيل شيك رقم {check.check_number}",
            "user_id": current_user.id,
            "branch_id": check.branch_id,
        }).fetchone()
        coll_je_id = je.id if je else None

        if coll_je_id:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, :amount, 0, :desc)
            """), {"je_id": coll_je_id, "account_id": treasury.gl_account_id, "amount": amount,
                   "desc": f"تحصيل شيك {check.check_number}"})
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, 0, :amount, :desc)
            """), {"je_id": coll_je_id, "account_id": checks_account.id, "amount": amount,
                   "desc": f"تحصيل شيك {check.check_number}"})

            # Update Account Balances
            update_account_balance(db, account_id=treasury.gl_account_id, debit_base=amount, credit_base=0)
            update_account_balance(db, account_id=checks_account.id, debit_base=0, credit_base=amount)

        # Update treasury balance
        db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance + :amt WHERE id = :tid"),
                   {"amt": amount, "tid": treasury_id})

        db.execute(text("""
            UPDATE checks_receivable SET status = 'collected', collection_date = :cdate,
                collection_journal_id = :je_id, treasury_account_id = COALESCE(:treasury_id, treasury_account_id),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": check_id, "cdate": collection_date, "je_id": coll_je_id, "treasury_id": treasury_id})
        db.commit()
        try:
            log_activity(db, current_user.id, current_user.username, "collect", "checks_receivable", str(check_id),
                         {"collection_date": collection_date})
        except Exception:
            pass
        return {"message": "تم تحصيل الشيك بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/receivable/{check_id}/bounce", dependencies=[Depends(require_permission("treasury.create"))])
def bounce_check_receivable(check_id: int, data: dict, current_user=Depends(get_current_user)):
    """
    Mark check as bounced.
    If pending: Dr. AR / Cr. Checks Under Collection (reverse original)
    If collected: Dr. AR / Cr. Bank (reverse collection + original)
    """
    db = get_db_connection(current_user.company_id)
    try:
        check = db.execute(text("SELECT * FROM checks_receivable WHERE id = :id"), {"id": check_id}).fetchone()
        if not check:
            raise HTTPException(404, "الشيك غير موجود")
            
        # Validate branch access
        validate_branch_access(current_user, check.branch_id)
        
        if check.status not in ('pending', 'collected'):
            raise HTTPException(400, "لا يمكن ارتجاع هذا الشيك")

        bounce_reason = data.get("bounce_reason", "")
        bounce_date = data.get("bounce_date", str(date.today()))
        amount = float(check.amount)

        ar_account = db.execute(text(
            "SELECT id FROM accounts WHERE account_code IN ('1201', '1200') AND is_active = TRUE ORDER BY account_code LIMIT 1"
        )).fetchone()
        checks_account = db.execute(text("SELECT id FROM accounts WHERE account_code = '1205' LIMIT 1")).fetchone()

        if not ar_account:
            raise HTTPException(500, "حساب العملاء (1200/1201) غير موجود")

        bounce_je_id = None

        if check.status == 'collected':
            treasury = db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE id = :id"),
                                  {"id": check.treasury_account_id}).fetchone() if check.treasury_account_id else None
            if not treasury:
                raise HTTPException(400, "حساب الخزينة غير مرتبط بالشيك المحصّل")

            je = db.execute(text("""
                INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
                VALUES (
                    'CHK-B-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-B-%')::text, '1'), 6, '0'),
                    :entry_date, :description, 'posted', 'check_bounce', :user_id, :branch_id
                ) RETURNING id
            """), {
                "entry_date": bounce_date,
                "description": f"ارتجاع شيك رقم {check.check_number} - {bounce_reason}",
                "user_id": current_user.id,
                "branch_id": check.branch_id,
            }).fetchone()
            bounce_je_id = je.id if je else None

            if bounce_je_id:
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, :amount, 0, :desc)
                """), {"je_id": bounce_je_id, "account_id": ar_account.id, "amount": amount,
                       "desc": f"ارتجاع شيك {check.check_number}"})
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, 0, :amount, :desc)
                """), {"je_id": bounce_je_id, "account_id": treasury.gl_account_id, "amount": amount,
                       "desc": f"ارتجاع شيك {check.check_number}"})

                # Update Account Balances
                update_account_balance(db, account_id=ar_account.id, debit_base=amount, credit_base=0)
                update_account_balance(db, account_id=treasury.gl_account_id, debit_base=0, credit_base=amount)

            db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance - :amt WHERE id = :tid"),
                       {"amt": amount, "tid": check.treasury_account_id})
        else:
            if not checks_account:
                raise HTTPException(500, "حساب الشيكات تحت التحصيل (1205) غير موجود")

            je = db.execute(text("""
                INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
                VALUES (
                    'CHK-B-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-B-%')::text, '1'), 6, '0'),
                    :entry_date, :description, 'posted', 'check_bounce', :user_id, :branch_id
                ) RETURNING id
            """), {
                "entry_date": bounce_date,
                "description": f"ارتجاع شيك رقم {check.check_number} - {bounce_reason}",
                "user_id": current_user.id,
                "branch_id": check.branch_id,
            }).fetchone()
            bounce_je_id = je.id if je else None

            if bounce_je_id:
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, :amount, 0, :desc)
                """), {"je_id": bounce_je_id, "account_id": ar_account.id, "amount": amount,
                       "desc": f"ارتجاع شيك {check.check_number}"})
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, 0, :amount, :desc)
                """), {"je_id": bounce_je_id, "account_id": checks_account.id, "amount": amount,
                       "desc": f"ارتجاع شيك {check.check_number}"})

                # Update Account Balances
                update_account_balance(db, account_id=ar_account.id, debit_base=amount, credit_base=0)
                update_account_balance(db, account_id=checks_account.id, debit_base=0, credit_base=amount)

        db.execute(text("""
            UPDATE checks_receivable SET status = 'bounced', bounce_date = :bdate,
                bounce_reason = :reason, bounce_journal_id = :je_id, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": check_id, "bdate": bounce_date, "reason": bounce_reason, "je_id": bounce_je_id})
        db.commit()
        try:
            log_activity(db, current_user.id, current_user.username, "bounce", "checks_receivable", str(check_id),
                         {"bounce_reason": bounce_reason})
        except Exception:
            pass
        return {"message": "تم تسجيل الشيك كمرتجع"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ============================================================
# TRS-002: شيكات تحت الدفع - Checks Payable
# ============================================================

@router.get("/payable", dependencies=[Depends(require_permission("treasury.view"))])
def list_checks_payable(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    search: Optional[str] = None,
    branch_id: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    """List all checks payable with filters"""
    # Validate branch access
    branch_id = validate_branch_access(current_user, branch_id)

    db = get_db_connection(current_user.company_id)
    try:
        offset = (page - 1) * limit
        conditions = []
        params = {"limit": limit, "offset": offset}

        if status:
            conditions.append("cp.status = :status")
            params["status"] = status
        if search:
            conditions.append("(cp.check_number ILIKE :search OR cp.beneficiary_name ILIKE :search OR cp.bank_name ILIKE :search)")
            params["search"] = f"%{search}%"
        if branch_id:
            conditions.append("cp.branch_id = :branch_id")
            params["branch_id"] = branch_id

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        total = db.execute(text(f"SELECT COUNT(*) FROM checks_payable cp {where}"), params).scalar() or 0

        rows = db.execute(text(f"""
            SELECT cp.*, p.name as party_name, ta.name as treasury_name
            FROM checks_payable cp
            LEFT JOIN parties p ON cp.party_id = p.id
            LEFT JOIN treasury_accounts ta ON cp.treasury_account_id = ta.id
            {where}
            ORDER BY cp.due_date ASC
            LIMIT :limit OFFSET :offset
        """), params).fetchall()

        items = []
        for r in rows:
            items.append({
                "id": r.id, "check_number": r.check_number,
                "beneficiary_name": r.beneficiary_name, "bank_name": r.bank_name,
                "branch_name": r.branch_name, "amount": float(r.amount),
                "currency": r.currency,
                "issue_date": str(r.issue_date) if r.issue_date else None,
                "due_date": str(r.due_date) if r.due_date else None,
                "clearance_date": str(r.clearance_date) if r.clearance_date else None,
                "bounce_date": str(r.bounce_date) if r.bounce_date else None,
                "party_id": r.party_id, "party_name": r.party_name,
                "treasury_account_id": r.treasury_account_id,
                "treasury_name": r.treasury_name,
                "status": r.status, "bounce_reason": r.bounce_reason,
                "notes": r.notes, "created_at": str(r.created_at) if r.created_at else None,
            })

        return {"items": items, "total": total, "page": page}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/payable/summary/stats", dependencies=[Depends(require_permission("treasury.view"))])
def checks_payable_stats(branch_id: Optional[int] = None, current_user=Depends(get_current_user)):
    """Get summary stats for checks payable"""
    # Validate branch access
    branch_id = validate_branch_access(current_user, branch_id)

    db = get_db_connection(current_user.company_id)
    try:
        cond = "AND branch_id = :branch_id" if branch_id else ""
        params = {"branch_id": branch_id} if branch_id else {}
        stats = db.execute(text(f"""
            SELECT
                COUNT(*) FILTER (WHERE status = 'issued') as issued_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'issued'), 0) as issued_amount,
                COUNT(*) FILTER (WHERE status = 'cleared') as cleared_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'cleared'), 0) as cleared_amount,
                COUNT(*) FILTER (WHERE status = 'bounced') as bounced_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'bounced'), 0) as bounced_amount,
                COUNT(*) FILTER (WHERE status = 'issued' AND due_date <= CURRENT_DATE) as overdue_count,
                COALESCE(SUM(amount) FILTER (WHERE status = 'issued' AND due_date <= CURRENT_DATE), 0) as overdue_amount
            FROM checks_payable WHERE 1=1 {cond}
        """), params).fetchone()
        return {
            "issued": {"count": stats.issued_count, "amount": float(stats.issued_amount)},
            "cleared": {"count": stats.cleared_count, "amount": float(stats.cleared_amount)},
            "bounced": {"count": stats.bounced_count, "amount": float(stats.bounced_amount)},
            "overdue": {"count": stats.overdue_count, "amount": float(stats.overdue_amount)},
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.get("/payable/{check_id}", dependencies=[Depends(require_permission("treasury.view"))])
def get_check_payable(check_id: int, current_user=Depends(get_current_user)):
    """Get single check payable details"""
    db = get_db_connection(current_user.company_id)
    try:
        r = db.execute(text("""
            SELECT cp.*, p.name as party_name, ta.name as treasury_name
            FROM checks_payable cp
            LEFT JOIN parties p ON cp.party_id = p.id
            LEFT JOIN treasury_accounts ta ON cp.treasury_account_id = ta.id
            WHERE cp.id = :id
        """), {"id": check_id}).fetchone()
        if not r:
            raise HTTPException(404, "الشيك غير موجود")
            
        # Validate branch access
        validate_branch_access(current_user, r.branch_id)
        
        return {
            "id": r.id, "check_number": r.check_number,
            "beneficiary_name": r.beneficiary_name, "bank_name": r.bank_name,
            "branch_name": r.branch_name, "amount": float(r.amount),
            "currency": r.currency,
            "issue_date": str(r.issue_date) if r.issue_date else None,
            "due_date": str(r.due_date) if r.due_date else None,
            "clearance_date": str(r.clearance_date) if r.clearance_date else None,
            "bounce_date": str(r.bounce_date) if r.bounce_date else None,
            "party_id": r.party_id, "party_name": r.party_name,
            "treasury_account_id": r.treasury_account_id,
            "treasury_name": r.treasury_name,
            "status": r.status, "bounce_reason": r.bounce_reason,
            "notes": r.notes,
            "journal_entry_id": r.journal_entry_id,
            "clearance_journal_id": r.clearance_journal_id,
            "bounce_journal_id": r.bounce_journal_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/payable", dependencies=[Depends(require_permission("treasury.create"))])
def create_check_payable(data: dict, current_user=Depends(get_current_user)):
    """
    Create a new check payable (issued check).
    GL: Dr. Accounts Payable / Cr. Checks Payable Account (2105)
    """
    db = get_db_connection(current_user.company_id)
    try:
        # Validate branch access
        if data.get("branch_id"):
             validate_branch_access(current_user, data["branch_id"])

        required = ["check_number", "amount", "due_date", "issue_date"]
        for f in required:
            if not data.get(f):
                raise HTTPException(400, f"الحقل {f} مطلوب")

        _ensure_checks_accounts(db)

        amount = float(data["amount"])

        checks_pay_account = db.execute(text(
            "SELECT id FROM accounts WHERE account_code = '2105' LIMIT 1"
        )).fetchone()

        ap_account = db.execute(text(
            "SELECT id FROM accounts WHERE account_code IN ('2101', '2100') AND is_active = TRUE ORDER BY account_code LIMIT 1"
        )).fetchone()

        if not checks_pay_account or not ap_account:
            raise HTTPException(500, "حسابات الشيكات (2105) أو الموردين (2100/2101) غير موجودة. يرجى إعداد دليل الحسابات أولاً.")

        je = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
            VALUES (
                'CHK-P-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-P-%')::text, '1'), 6, '0'),
                :entry_date, :description, 'posted', 'check_payable', :user_id, :branch_id
            ) RETURNING id
        """), {
            "entry_date": data["issue_date"],
            "description": f"إصدار شيك رقم {data['check_number']} - {data.get('beneficiary_name', '')}",
            "user_id": current_user.id,
            "branch_id": data.get("branch_id"),
        }).fetchone()
        je_id = je.id if je else None

        if je_id:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, :amount, 0, :desc)
            """), {"je_id": je_id, "account_id": ap_account.id, "amount": amount,
                   "desc": f"شيك صادر {data['check_number']}"})
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, 0, :amount, :desc)
            """), {"je_id": je_id, "account_id": checks_pay_account.id, "amount": amount,
                   "desc": f"شيك صادر {data['check_number']}"})

            # Update Account Balances
            update_account_balance(db, account_id=ap_account.id, debit_base=amount, credit_base=0)
            update_account_balance(db, account_id=checks_pay_account.id, debit_base=0, credit_base=amount)

        result = db.execute(text("""
            INSERT INTO checks_payable (
                check_number, beneficiary_name, bank_name, branch_name, amount, currency,
                issue_date, due_date, party_id, treasury_account_id, payment_voucher_id,
                journal_entry_id, status, notes, branch_id, created_by
            ) VALUES (
                :check_number, :beneficiary_name, :bank_name, :branch_name, :amount, :currency,
                :issue_date, :due_date, :party_id, :treasury_id, :payment_voucher_id,
                :je_id, 'issued', :notes, :branch_id, :user_id
            ) RETURNING id
        """), {
            "check_number": data["check_number"],
            "beneficiary_name": data.get("beneficiary_name", ""),
            "bank_name": data.get("bank_name", ""),
            "branch_name": data.get("branch_name", ""),
            "amount": amount,
            "currency": data.get("currency", get_base_currency(db)),
            "issue_date": data["issue_date"],
            "due_date": data["due_date"],
            "party_id": data.get("party_id"),
            "treasury_id": data.get("treasury_account_id"),
            "payment_voucher_id": data.get("payment_voucher_id"),
            "je_id": je_id,
            "notes": data.get("notes", ""),
            "branch_id": data.get("branch_id"),
            "user_id": current_user.id,
        }).fetchone()

        db.commit()
        try:
            log_activity(db, current_user.id, current_user.username, "create", "checks_payable", str(result.id),
                         {"check_number": data["check_number"], "amount": amount})
        except Exception:
            pass
        return {"id": result.id, "message": "تم تسجيل الشيك بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/payable/{check_id}/clear", dependencies=[Depends(require_permission("treasury.create"))])
def clear_check_payable(check_id: int, data: dict, current_user=Depends(get_current_user)):
    """
    Mark check as cleared (presented and paid by bank).
    GL: Dr. Checks Payable (2105) / Cr. Bank
    """
    db = get_db_connection(current_user.company_id)
    try:
        check = db.execute(text("SELECT * FROM checks_payable WHERE id = :id"), {"id": check_id}).fetchone()
        if not check:
            raise HTTPException(404, "الشيك غير موجود")
            
        # Validate branch access
        validate_branch_access(current_user, check.branch_id)
        
        if check.status != 'issued':
            raise HTTPException(400, "الشيك ليس في حالة صادر")

        clearance_date = data.get("clearance_date", str(date.today()))
        treasury_id = data.get("treasury_account_id") or check.treasury_account_id

        if not treasury_id:
            raise HTTPException(400, "يجب تحديد حساب الخزينة/البنك")

        treasury = db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE id = :id"), {"id": treasury_id}).fetchone()
        if not treasury:
            raise HTTPException(404, "حساب الخزينة غير موجود")

        checks_pay_account = db.execute(text("SELECT id FROM accounts WHERE account_code = '2105' LIMIT 1")).fetchone()
        if not checks_pay_account:
            raise HTTPException(500, "حساب الشيكات تحت الدفع (2105) غير موجود")

        amount = float(check.amount)

        je = db.execute(text("""
            INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
            VALUES (
                'CHK-CL-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-CL-%')::text, '1'), 6, '0'),
                :entry_date, :description, 'posted', 'check_clearance', :user_id, :branch_id
            ) RETURNING id
        """), {
            "entry_date": clearance_date,
            "description": f"صرف شيك رقم {check.check_number}",
            "user_id": current_user.id,
            "branch_id": check.branch_id,
        }).fetchone()
        clear_je_id = je.id if je else None

        if clear_je_id:
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, :amount, 0, :desc)
            """), {"je_id": clear_je_id, "account_id": checks_pay_account.id, "amount": amount,
                   "desc": f"صرف شيك {check.check_number}"})
            db.execute(text("""
                INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                VALUES (:je_id, :account_id, 0, :amount, :desc)
            """), {"je_id": clear_je_id, "account_id": treasury.gl_account_id, "amount": amount,
                   "desc": f"صرف شيك {check.check_number}"})

            # Update Account Balances
            update_account_balance(db, account_id=checks_pay_account.id, debit_base=amount, credit_base=0)
            update_account_balance(db, account_id=treasury.gl_account_id, debit_base=0, credit_base=amount)

        db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance - :amt WHERE id = :tid"),
                   {"amt": amount, "tid": treasury_id})

        db.execute(text("""
            UPDATE checks_payable SET status = 'cleared', clearance_date = :cdate,
                clearance_journal_id = :je_id, treasury_account_id = COALESCE(:treasury_id, treasury_account_id),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": check_id, "cdate": clearance_date, "je_id": clear_je_id, "treasury_id": treasury_id})
        db.commit()
        try:
            log_activity(db, current_user.id, current_user.username, "clear", "checks_payable", str(check_id),
                         {"clearance_date": clearance_date})
        except Exception:
            pass
        return {"message": "تم صرف الشيك بنجاح"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/payable/{check_id}/bounce", dependencies=[Depends(require_permission("treasury.create"))])
def bounce_check_payable(check_id: int, data: dict, current_user=Depends(get_current_user)):
    """
    Mark issued check as bounced.
    GL: Dr. Checks Payable (2105) / Cr. Accounts Payable
    """
    db = get_db_connection(current_user.company_id)
    try:
        check = db.execute(text("SELECT * FROM checks_payable WHERE id = :id"), {"id": check_id}).fetchone()
        if not check:
            raise HTTPException(404, "الشيك غير موجود")
            
        # Validate branch access
        validate_branch_access(current_user, check.branch_id)
        
        if check.status not in ('issued', 'cleared'):
            raise HTTPException(400, "لا يمكن ارتجاع هذا الشيك")

        bounce_reason = data.get("bounce_reason", "")
        bounce_date = data.get("bounce_date", str(date.today()))
        amount = float(check.amount)

        checks_pay_account = db.execute(text("SELECT id FROM accounts WHERE account_code = '2105' LIMIT 1")).fetchone()
        ap_account = db.execute(text(
            "SELECT id FROM accounts WHERE account_code IN ('2101', '2100') AND is_active = TRUE ORDER BY account_code LIMIT 1"
        )).fetchone()

        if not checks_pay_account or not ap_account:
            raise HTTPException(500, "حسابات الشيكات أو الموردين غير موجودة")

        bounce_je_id = None

        if check.status == 'cleared':
            # Cleared check bounced: reverse both issuance + clearance
            # Net reversal: Dr. Bank / Cr. AP
            treasury = db.execute(text("SELECT gl_account_id FROM treasury_accounts WHERE id = :id"),
                                  {"id": check.treasury_account_id}).fetchone() if check.treasury_account_id else None
            if not treasury:
                raise HTTPException(400, "حساب الخزينة غير مرتبط بالشيك")

            je = db.execute(text("""
                INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
                VALUES (
                    'CHK-BP-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-BP-%')::text, '1'), 6, '0'),
                    :entry_date, :description, 'posted', 'check_payable_bounce', :user_id, :branch_id
                ) RETURNING id
            """), {
                "entry_date": bounce_date,
                "description": f"ارتجاع شيك صادر رقم {check.check_number} (مصروف سابقاً) - {bounce_reason}",
                "user_id": current_user.id,
                "branch_id": check.branch_id,
            }).fetchone()
            bounce_je_id = je.id if je else None

            if bounce_je_id:
                # Dr. Bank (money returns to us)
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, :amount, 0, :desc)
                """), {"je_id": bounce_je_id, "account_id": treasury.gl_account_id, "amount": amount,
                       "desc": f"ارتجاع شيك مصروف {check.check_number}"})
                # Cr. AP (we still owe the supplier)
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, 0, :amount, :desc)
                """), {"je_id": bounce_je_id, "account_id": ap_account.id, "amount": amount,
                       "desc": f"ارتجاع شيك مصروف {check.check_number}"})

                # Update Account Balances
                update_account_balance(db, account_id=treasury.gl_account_id, debit_base=amount, credit_base=0)
                update_account_balance(db, account_id=ap_account.id, debit_base=0, credit_base=amount)

            # Treasury balance increases (money came back)
            db.execute(text("UPDATE treasury_accounts SET current_balance = current_balance + :amt WHERE id = :tid"),
                       {"amt": amount, "tid": check.treasury_account_id})
        else:
            # Issued (not cleared) check bounced: reverse issuance only
            # Dr. 2105 / Cr. AP
            je = db.execute(text("""
                INSERT INTO journal_entries (entry_number, entry_date, description, status, source, created_by, branch_id)
                VALUES (
                    'CHK-BP-' || LPAD(COALESCE((SELECT COUNT(*)+1 FROM journal_entries WHERE entry_number LIKE 'CHK-BP-%')::text, '1'), 6, '0'),
                    :entry_date, :description, 'posted', 'check_payable_bounce', :user_id, :branch_id
                ) RETURNING id
            """), {
                "entry_date": bounce_date,
                "description": f"ارتجاع شيك صادر رقم {check.check_number} - {bounce_reason}",
                "user_id": current_user.id,
                "branch_id": check.branch_id,
            }).fetchone()
            bounce_je_id = je.id if je else None

            if bounce_je_id:
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, :amount, 0, :desc)
                """), {"je_id": bounce_je_id, "account_id": checks_pay_account.id, "amount": amount,
                       "desc": f"ارتجاع شيك صادر {check.check_number}"})
                db.execute(text("""
                    INSERT INTO journal_lines (journal_entry_id, account_id, debit, credit, description)
                    VALUES (:je_id, :account_id, 0, :amount, :desc)
                """), {"je_id": bounce_je_id, "account_id": ap_account.id, "amount": amount,
                       "desc": f"ارتجاع شيك صادر {check.check_number}"})

                # Update Account Balances
                update_account_balance(db, account_id=checks_pay_account.id, debit_base=amount, credit_base=0)
                update_account_balance(db, account_id=ap_account.id, debit_base=0, credit_base=amount)

        db.execute(text("""
            UPDATE checks_payable SET status = 'bounced', bounce_date = :bdate,
                bounce_reason = :reason, bounce_journal_id = :je_id, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """), {"id": check_id, "bdate": bounce_date, "reason": bounce_reason, "je_id": bounce_je_id})
        db.commit()
        try:
            log_activity(db, current_user.id, current_user.username, "bounce", "checks_payable", str(check_id),
                         {"bounce_reason": bounce_reason})
        except Exception:
            pass
        return {"message": "تم تسجيل الشيك كمرتجع"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
    finally:
        db.close()


# ============================================================
# Due Checks Alerts (for both receivable and payable)
# ============================================================

@router.get("/due-alerts", dependencies=[Depends(require_permission("treasury.view"))])
def get_due_checks_alerts(days_ahead: int = Query(7, ge=1, le=90), branch_id: Optional[int] = None,
                          current_user=Depends(get_current_user)):
    """Get checks due within the next N days"""
    db = get_db_connection(current_user.company_id)
    try:
        cond = "AND branch_id = :branch_id" if branch_id else ""
        params = {"days": days_ahead}
        if branch_id:
            params["branch_id"] = branch_id

        receivable = db.execute(text(f"""
            SELECT id, check_number, drawer_name as party, amount, due_date, 'receivable' as type
            FROM checks_receivable
            WHERE status = 'pending' AND due_date <= CURRENT_DATE + :days {cond}
            ORDER BY due_date
        """), params).fetchall()

        payable = db.execute(text(f"""
            SELECT id, check_number, beneficiary_name as party, amount, due_date, 'payable' as type
            FROM checks_payable
            WHERE status = 'issued' AND due_date <= CURRENT_DATE + :days {cond}
            ORDER BY due_date
        """), params).fetchall()

        alerts = []
        for r in receivable:
            alerts.append({
                "id": r.id, "check_number": r.check_number, "party": r.party,
                "amount": float(r.amount), "due_date": str(r.due_date),
                "type": "receivable", "is_overdue": r.due_date <= date.today()
            })
        for r in payable:
            alerts.append({
                "id": r.id, "check_number": r.check_number, "party": r.party,
                "amount": float(r.amount), "due_date": str(r.due_date),
                "type": "payable", "is_overdue": r.due_date <= date.today()
            })

        alerts.sort(key=lambda x: x["due_date"])
        return {"alerts": alerts, "total": len(alerts)}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        db.close()
