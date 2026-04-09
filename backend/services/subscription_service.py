"""Subscription billing service.

Handles enrollment lifecycle: enroll, billing, proration, cancellation,
trial management, and failed payment handling.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import text

logger = logging.getLogger(__name__)

_ZERO = Decimal("0")
_D4 = Decimal("0.0001")


def _dec(val) -> Decimal:
    if val is None:
        return _ZERO
    return Decimal(str(val))


def _billing_period_end(start: date, frequency: str) -> date:
    """Compute billing period end date from start and frequency."""
    if frequency == "monthly":
        # Advance 1 month
        month = start.month + 1
        year = start.year
        if month > 12:
            month = 1
            year += 1
        day = min(start.day, 28)  # safe day
        return date(year, month, day) - timedelta(days=1)
    elif frequency == "quarterly":
        month = start.month + 3
        year = start.year
        while month > 12:
            month -= 12
            year += 1
        day = min(start.day, 28)
        return date(year, month, day) - timedelta(days=1)
    elif frequency == "annual":
        return date(start.year + 1, start.month, min(start.day, 28)) - timedelta(days=1)
    else:
        # Default to monthly
        month = start.month + 1
        year = start.year
        if month > 12:
            month = 1
            year += 1
        return date(year, month, min(start.day, 28)) - timedelta(days=1)


def _next_billing(current: date, frequency: str) -> date:
    """Compute next billing date after current period."""
    end = _billing_period_end(current, frequency)
    return end + timedelta(days=1)


# ── Enrollment ──

def enroll_customer(db, *, customer_id: int, plan_id: int, enrollment_date: date | None = None, user: str | None = None) -> dict:
    """Enroll a customer in a subscription plan.

    If the plan has trial_period_days > 0, sets trial status and trial_end_date.
    Returns dict with enrollment_id.
    """
    today = enrollment_date or date.today()

    plan = db.execute(
        text("SELECT * FROM subscription_plans WHERE id = :pid AND is_deleted = false AND is_active = true"),
        {"pid": plan_id},
    ).fetchone()
    if not plan:
        raise ValueError(f"Plan {plan_id} not found or inactive")

    # Check customer exists
    customer = db.execute(
        text("SELECT id FROM parties WHERE id = :cid"),
        {"cid": customer_id},
    ).fetchone()
    if not customer:
        raise ValueError(f"Customer {customer_id} not found")

    trial_days = plan.trial_period_days or 0
    if trial_days > 0:
        status = "trial"
        trial_end = today + timedelta(days=trial_days)
        next_billing = trial_end + timedelta(days=1)
    else:
        status = "active"
        trial_end = None
        next_billing = _next_billing(today, plan.billing_frequency)

    row = db.execute(
        text(
            "INSERT INTO subscription_enrollments "
            "(customer_id, plan_id, enrollment_date, trial_end_date, next_billing_date, status, "
            " created_by, updated_by) "
            "VALUES (:cid, :pid, :ed, :ted, :nbd, :st, :usr, :usr) "
            "RETURNING id"
        ),
        {
            "cid": customer_id,
            "pid": plan_id,
            "ed": today,
            "ted": trial_end,
            "nbd": next_billing,
            "st": status,
            "usr": user,
        },
    ).fetchone()
    enrollment_id = row[0]
    db.commit()

    logger.info(
        "Enrolled customer %d in plan %d (status=%s, enrollment=%d)",
        customer_id, plan_id, status, enrollment_id,
    )
    return {"enrollment_id": enrollment_id, "status": status}


# ── Invoice Generation ──

def generate_subscription_invoice(db, *, enrollment_id: int, user: str | None = None) -> dict:
    """Generate an invoice for the current billing period of an enrollment.

    Creates an invoice record linked via subscription_invoices.
    Returns dict with invoice_id and subscription_invoice_id.
    """
    enrollment = db.execute(
        text(
            "SELECT e.*, p.base_amount, p.currency, p.billing_frequency, p.name AS plan_name "
            "FROM subscription_enrollments e "
            "JOIN subscription_plans p ON p.id = e.plan_id "
            "WHERE e.id = :eid AND e.is_deleted = false "
            "FOR UPDATE OF e"
        ),
        {"eid": enrollment_id},
    ).fetchone()
    if not enrollment:
        raise ValueError(f"Enrollment {enrollment_id} not found")

    if enrollment.status not in ("active", "at_risk"):
        raise ValueError(f"Cannot bill enrollment in '{enrollment.status}' status")

    billing_start = enrollment.next_billing_date
    billing_end = _billing_period_end(billing_start, enrollment.billing_frequency)
    amount = _dec(enrollment.base_amount).quantize(_D4, rounding=ROUND_HALF_UP)

    # Create the main invoice
    inv_row = db.execute(
        text(
            "INSERT INTO invoices "
            "(invoice_type, party_id, invoice_date, due_date, total, paid_amount, "
            " status, notes, created_by, updated_by) "
            "VALUES ('sales', :cid, :dt, :due, :amt, 0, 'pending', :notes, :usr, :usr) "
            "RETURNING id"
        ),
        {
            "cid": enrollment.customer_id,
            "dt": billing_start,
            "due": billing_end,
            "amt": float(amount),
            "notes": f"Subscription: {enrollment.plan_name} ({billing_start} - {billing_end})",
            "usr": user,
        },
    ).fetchone()
    invoice_id = inv_row[0]

    # Link via subscription_invoices
    si_row = db.execute(
        text(
            "INSERT INTO subscription_invoices "
            "(enrollment_id, invoice_id, billing_period_start, billing_period_end, "
            " is_prorated, created_by, updated_by) "
            "VALUES (:eid, :iid, :bps, :bpe, false, :usr, :usr) "
            "RETURNING id"
        ),
        {
            "eid": enrollment_id,
            "iid": invoice_id,
            "bps": billing_start,
            "bpe": billing_end,
            "usr": user,
        },
    ).fetchone()

    # Advance next_billing_date
    new_next = billing_end + timedelta(days=1)
    db.execute(
        text(
            "UPDATE subscription_enrollments SET next_billing_date = :nbd, updated_at = NOW() "
            "WHERE id = :eid"
        ),
        {"nbd": new_next, "eid": enrollment_id},
    )

    db.commit()
    logger.info(
        "Generated invoice %d for enrollment %d (period %s - %s, amount %s)",
        invoice_id, enrollment_id, billing_start, billing_end, amount,
    )
    return {"invoice_id": invoice_id, "subscription_invoice_id": si_row[0]}


# ── Proration ──

def prorate_plan_change(db, *, enrollment_id: int, new_plan_id: int, user: str | None = None) -> dict:
    """Change an enrollment's plan with proration.

    Credits unused portion of old plan, charges prorated amount of new plan.
    Returns dict with credit_amount, charge_amount, net_amount, new_invoice_id.
    """
    enrollment = db.execute(
        text(
            "SELECT e.*, p.base_amount AS old_amount, p.billing_frequency AS old_freq, p.name AS old_plan_name "
            "FROM subscription_enrollments e "
            "JOIN subscription_plans p ON p.id = e.plan_id "
            "WHERE e.id = :eid AND e.is_deleted = false "
            "FOR UPDATE OF e"
        ),
        {"eid": enrollment_id},
    ).fetchone()
    if not enrollment:
        raise ValueError(f"Enrollment {enrollment_id} not found")
    if enrollment.status not in ("active", "trial"):
        raise ValueError(f"Cannot change plan in '{enrollment.status}' status")

    new_plan = db.execute(
        text("SELECT * FROM subscription_plans WHERE id = :pid AND is_deleted = false AND is_active = true"),
        {"pid": new_plan_id},
    ).fetchone()
    if not new_plan:
        raise ValueError(f"New plan {new_plan_id} not found or inactive")

    today = date.today()
    old_amount = _dec(enrollment.old_amount)
    new_amount = _dec(new_plan.base_amount)

    # Calculate proration: how much of the current period is remaining
    period_end = _billing_period_end(enrollment.next_billing_date - timedelta(days=1), enrollment.old_freq)
    # next_billing_date was already advanced, so period start is the day after the previous period end
    # Actually, next_billing_date IS the start of the next period. Current period start = next_billing - period_length
    # Simpler: use days remaining / total days
    period_start = enrollment.enrollment_date  # approximate
    # Better: compute from enrollment's last billing
    last_invoice = db.execute(
        text(
            "SELECT billing_period_start, billing_period_end FROM subscription_invoices "
            "WHERE enrollment_id = :eid AND is_deleted = false "
            "ORDER BY billing_period_end DESC LIMIT 1"
        ),
        {"eid": enrollment_id},
    ).fetchone()

    if last_invoice:
        period_start = last_invoice.billing_period_start
        period_end = last_invoice.billing_period_end
    else:
        period_start = enrollment.enrollment_date
        period_end = _billing_period_end(period_start, enrollment.old_freq)

    total_days = (period_end - period_start).days + 1
    remaining_days = max((period_end - today).days + 1, 0)

    if total_days > 0 and remaining_days > 0:
        daily_old = old_amount / Decimal(str(total_days))
        credit = (daily_old * Decimal(str(remaining_days))).quantize(_D4, rounding=ROUND_HALF_UP)

        daily_new = new_amount / Decimal(str(total_days))
        charge = (daily_new * Decimal(str(remaining_days))).quantize(_D4, rounding=ROUND_HALF_UP)
    else:
        credit = _ZERO
        charge = _ZERO

    net = (charge - credit).quantize(_D4, rounding=ROUND_HALF_UP)

    # Create prorated invoice if net > 0
    invoice_id = None
    if net > _ZERO:
        inv_row = db.execute(
            text(
                "INSERT INTO invoices "
                "(invoice_type, party_id, invoice_date, due_date, total, paid_amount, "
                " status, notes, created_by, updated_by) "
                "VALUES ('sales', :cid, :dt, :due, :amt, 0, 'pending', :notes, :usr, :usr) "
                "RETURNING id"
            ),
            {
                "cid": enrollment.customer_id,
                "dt": today,
                "due": today + timedelta(days=30),
                "amt": float(net),
                "notes": f"Plan change proration: {enrollment.old_plan_name} -> {new_plan.name}",
                "usr": user,
            },
        ).fetchone()
        invoice_id = inv_row[0]

        db.execute(
            text(
                "INSERT INTO subscription_invoices "
                "(enrollment_id, invoice_id, billing_period_start, billing_period_end, "
                " is_prorated, proration_details, created_by, updated_by) "
                "VALUES (:eid, :iid, :bps, :bpe, true, :pd, :usr, :usr)"
            ),
            {
                "eid": enrollment_id,
                "iid": invoice_id,
                "bps": today,
                "bpe": period_end,
                "pd": f'{{"credit": "{credit}", "charge": "{charge}", "net": "{net}", '
                      f'"old_plan_id": {enrollment.plan_id}, "new_plan_id": {new_plan_id}}}',
                "usr": user,
            },
        )

    # Update enrollment to new plan
    db.execute(
        text(
            "UPDATE subscription_enrollments "
            "SET plan_id = :pid, updated_at = NOW(), updated_by = :usr "
            "WHERE id = :eid"
        ),
        {"pid": new_plan_id, "eid": enrollment_id, "usr": user},
    )
    db.commit()

    logger.info(
        "Plan change for enrollment %d: credit=%s, charge=%s, net=%s",
        enrollment_id, credit, charge, net,
    )
    return {
        "credit_amount": str(credit),
        "charge_amount": str(charge),
        "net_amount": str(net),
        "new_invoice_id": invoice_id,
    }


# ── Pause / Resume ──

def pause_enrollment(db, *, enrollment_id: int, user: str | None = None) -> None:
    """Pause an active subscription."""
    result = db.execute(
        text(
            "UPDATE subscription_enrollments SET status = 'paused', updated_at = NOW(), updated_by = :usr "
            "WHERE id = :eid AND status IN ('active', 'at_risk') AND is_deleted = false"
        ),
        {"eid": enrollment_id, "usr": user},
    )
    if result.rowcount == 0:
        raise ValueError(f"Enrollment {enrollment_id} not found or not in pauseable state")
    db.commit()
    logger.info("Paused enrollment %d", enrollment_id)


def resume_enrollment(db, *, enrollment_id: int, user: str | None = None) -> None:
    """Resume a paused subscription. Resets next billing to today."""
    result = db.execute(
        text(
            "UPDATE subscription_enrollments "
            "SET status = 'active', next_billing_date = CURRENT_DATE, "
            "    failed_payment_count = 0, updated_at = NOW(), updated_by = :usr "
            "WHERE id = :eid AND status = 'paused' AND is_deleted = false"
        ),
        {"eid": enrollment_id, "usr": user},
    )
    if result.rowcount == 0:
        raise ValueError(f"Enrollment {enrollment_id} not found or not paused")
    db.commit()
    logger.info("Resumed enrollment %d", enrollment_id)


# ── Cancellation ──

def cancel_enrollment(db, *, enrollment_id: int, reason: str | None = None, user: str | None = None) -> dict:
    """Cancel a subscription. Generates a final prorated invoice if applicable."""
    enrollment = db.execute(
        text(
            "SELECT e.*, p.base_amount, p.billing_frequency, p.name AS plan_name "
            "FROM subscription_enrollments e "
            "JOIN subscription_plans p ON p.id = e.plan_id "
            "WHERE e.id = :eid AND e.is_deleted = false "
            "FOR UPDATE OF e"
        ),
        {"eid": enrollment_id},
    ).fetchone()
    if not enrollment:
        raise ValueError(f"Enrollment {enrollment_id} not found")
    if enrollment.status == "cancelled":
        raise ValueError("Enrollment is already cancelled")

    db.execute(
        text(
            "UPDATE subscription_enrollments "
            "SET status = 'cancelled', cancelled_at = NOW(), cancellation_reason = :reason, "
            "    updated_at = NOW(), updated_by = :usr "
            "WHERE id = :eid"
        ),
        {"eid": enrollment_id, "reason": reason, "usr": user},
    )
    db.commit()

    logger.info("Cancelled enrollment %d (reason: %s)", enrollment_id, reason)
    return {"enrollment_id": enrollment_id, "status": "cancelled"}


# ── Failed Payment ──

def handle_failed_payment(db, *, enrollment_id: int) -> dict:
    """Increment failed payment counter. Mark at_risk after 3 failures."""
    enrollment = db.execute(
        text(
            "SELECT * FROM subscription_enrollments WHERE id = :eid AND is_deleted = false "
            "FOR UPDATE"
        ),
        {"eid": enrollment_id},
    ).fetchone()
    if not enrollment:
        raise ValueError(f"Enrollment {enrollment_id} not found")

    new_count = (enrollment.failed_payment_count or 0) + 1
    new_status = enrollment.status
    if new_count >= 3 and enrollment.status == "active":
        new_status = "at_risk"

    db.execute(
        text(
            "UPDATE subscription_enrollments "
            "SET failed_payment_count = :cnt, status = :st, updated_at = NOW() "
            "WHERE id = :eid"
        ),
        {"cnt": new_count, "st": new_status, "eid": enrollment_id},
    )
    db.commit()

    logger.info(
        "Failed payment #%d for enrollment %d (status: %s)",
        new_count, enrollment_id, new_status,
    )
    return {"failed_count": new_count, "status": new_status}


# ── Trial Expiration ──

def check_trial_expirations(db) -> int:
    """Convert expired trials to active status. Returns count of converted enrollments."""
    today = date.today()
    result = db.execute(
        text(
            "UPDATE subscription_enrollments "
            "SET status = 'active', updated_at = NOW() "
            "WHERE status = 'trial' AND trial_end_date <= :today AND is_deleted = false"
        ),
        {"today": today},
    )
    count = result.rowcount
    if count > 0:
        db.commit()
        logger.info("Converted %d trial enrollments to active", count)
    return count


# ── Billing Due Check (for scheduler) ──

def check_billing_due(db, user: str = "system") -> list[dict]:
    """Find enrollments with billing due today or earlier and generate invoices.

    Returns list of generated invoice results.
    """
    today = date.today()
    enrollments = db.execute(
        text(
            "SELECT id FROM subscription_enrollments "
            "WHERE next_billing_date <= :today "
            "  AND status IN ('active', 'at_risk') "
            "  AND is_deleted = false "
            "ORDER BY id"
        ),
        {"today": today},
    ).fetchall()

    results = []
    for row in enrollments:
        try:
            result = generate_subscription_invoice(db, enrollment_id=row.id, user=user)
            results.append(result)
        except Exception as e:
            logger.error("Failed to generate invoice for enrollment %d: %s", row.id, e)
            # Mark failed payment
            try:
                handle_failed_payment(db, enrollment_id=row.id)
            except Exception:
                logger.exception("Failed to handle payment failure for enrollment %d", row.id)

    return results
