# Research: CRM Module Audit & Bug Fixes

**Feature**: 017-audit-crm  
**Date**: 2026-04-20  
**Phase**: 0 — Code Discovery

---

## Files In Scope

| File | Role |
|------|------|
| `backend/routers/crm.py` | All CRM endpoints (1872 lines) |
| `backend/database.py` | Table DDL — `sales_quotations`, `sales_quotation_lines`, `marketing_campaigns`, `support_tickets`, `ticket_comments`, `sales_opportunities` |
| `backend/services/notification_service.py` | `dispatch()` async method |
| `backend/utils/accounting.py` | `generate_sequential_number()` helper |
| `frontend/src/pages/CRM/CRMHome.jsx` | Dashboard + ticket comment thread |
| `frontend/src/pages/CRM/CRMContacts.jsx` | Contact form (customer_id input) |
| `frontend/src/pages/CRM/MarketingCampaigns.jsx` | Campaign list with engagement metrics |
| `frontend/src/pages/CRM/SupportTickets.jsx` | Ticket detail + comment submit |
| `frontend/src/pages/Campaign/CampaignReport.jsx` | Attribute lead modal |

---

## BUG-01 — Wrong Column Names in `convert_to_quotation`

**Severity**: Critical  
**Location**: `backend/routers/crm.py`

### Root Cause

Three wrong identifiers are used in the INSERT queries:

| Line | Wrong identifier | Correct identifier | Source of truth |
|------|-----------------|-------------------|-----------------|
| 475 | `"quotation_number"` (4th arg to `generate_sequential_number`) | `"sq_number"` | `database.py:995` |
| 479 | column `quotation_number` in INSERT | `sq_number` | `database.py:995` |
| 480 | column `valid_until` in INSERT | `expiry_date` | `database.py:1000` |
| 498 | column `quotation_id` in line INSERT | `sq_id` | `database.py:1018` |

### Current Code (lines 474–504)

```python
# Line 475 — wrong column name for sequence generation
quot_num = generate_sequential_number(db, f"QT-{datetime.now().year}", "sales_quotations", "quotation_number")

# Lines 477–493 — wrong INSERT columns
quot_id = db.execute(text("""
    INSERT INTO sales_quotations (
        quotation_number, customer_id, quotation_date, valid_until,   -- ← wrong
        subtotal, tax_amount, discount, total, status, notes, created_by, branch_id
    ) VALUES (...)
    RETURNING id
"""), {...}).scalar()

# Lines 497–504 — wrong column name in line INSERT
db.execute(text("""
    INSERT INTO sales_quotation_lines (quotation_id, description, quantity, ...)  -- ← wrong
    VALUES (:qid, :desc, 1, :price, 0, 0, :price)
"""), {"qid": quot_id, ...})
```

### Missing Check: Duplicate Conversion

No check for `won_quotation_id` before inserting — a second click creates a duplicate quotation.  
The column `sales_opportunities.won_quotation_id INT` exists (`database.py:4653`).

### Fix

```python
# 1. Check for existing quotation first
existing = db.execute(
    text("SELECT won_quotation_id FROM sales_opportunities WHERE id = :id"),
    {"id": opp_id}
).scalar()
if existing:
    raise HTTPException(**http_error(409, "quotation_already_exists",
                                     extra={"quotation_id": existing}))

# 2. Fix sequence generation
quot_num = generate_sequential_number(db, f"QT-{datetime.now().year}",
                                       "sales_quotations", "sq_number")

# 3. Fix INSERT column names
INSERT INTO sales_quotations (
    sq_number, customer_id, quotation_date, expiry_date, ...
)

# 4. Fix line INSERT column name
INSERT INTO sales_quotation_lines (sq_id, description, ...)

# 5. Write won_quotation_id back to opportunity
UPDATE sales_opportunities SET won_quotation_id = :qid WHERE id = :opp_id
```

---

## BUG-02 — Frontend Sends Wrong Field Name for Ticket Comment

**Severity**: Critical  
**Location**: Frontend JSX files

### Root Cause

`CommentCreate` Pydantic model (`crm.py:79–82`) defines the field as `comment: str`.  
Backend INSERT (`crm.py:442`) uses `data.comment` → correct.  
Frontend sends `{ content: commentText }` → Pydantic rejects with 422 / comment is empty.

### Affected Frontend Files

- `frontend/src/pages/CRM/SupportTickets.jsx` — submit handler sends `{ content: commentText }`
- `frontend/src/pages/CRM/CRMHome.jsx` — ticket reply widget sends `{ content: commentText }`

### Fix

Change both send sites from:
```js
{ content: commentText }
```
to:
```js
{ comment: commentText }
```

---

## BUG-03 — Frontend Reads Wrong Field Name for Author Name

**Severity**: Critical  
**Location**: Frontend JSX files

### Root Cause

Backend query (`crm.py:354–358`) returns `cu.username as author_name`.  
Frontend renders `comment.user_name` → always `undefined` → shows blank.

### Affected Frontend Files

- `frontend/src/pages/CRM/SupportTickets.jsx` — renders `comment.user_name`
- `frontend/src/pages/CRM/CRMHome.jsx` — renders `comment.user_name`

### Fix

Change both render sites from `comment.user_name` to `comment.author_name`.

---

## BUG-04 — Campaign List Shows Zero Engagement Metrics

**Severity**: High  
**Location**: `frontend/src/pages/CRM/MarketingCampaigns.jsx`

### Root Cause

The API (`/crm/campaigns`) returns `total_sent`, `total_opened`, `total_clicked`, `total_responded`.  
`MarketingCampaigns.jsx` reads `sent_count`, `open_count`, `click_count`, `conversion_count` (old column names) → all zero.

### Fix

In `MarketingCampaigns.jsx`, update field reads:

| Old (wrong) | New (correct) |
|-------------|--------------|
| `c.sent_count` | `c.total_sent` |
| `c.open_count` | `c.total_opened` |
| `c.click_count` | `c.total_clicked` |
| `c.conversion_count` | `c.total_responded` |

---

## BUG-05 — Campaign ROI Analytics Queries Deleted Columns

**Severity**: High  
**Location**: `backend/routers/crm.py:1830–1872`

### Root Cause

`campaign_roi_analytics` (line 1831) queries `sent_count`, `open_count`, `click_count`, `conversion_count`.  
These columns still exist in the table (they have not been dropped yet) but are never written — always 0.  
The analytics summary (lines 1855–1865) also uses them.

### Fix

Replace all references with `total_sent`, `total_opened`, `total_clicked`, `total_responded`:

```sql
-- Before (lines 1837–1851)
COALESCE(sent_count, 0) as sent,
COALESCE(open_count, 0) as opens,
COALESCE(click_count, 0) as clicks,
COALESCE(conversion_count, 0) as conversions,
CASE WHEN COALESCE(sent_count, 0) > 0
     THEN ROUND(100.0 * COALESCE(open_count, 0) / sent_count, 1) ELSE 0 END as open_rate,
...

-- After
COALESCE(total_sent, 0) as sent,
COALESCE(total_opened, 0) as opens,
COALESCE(total_clicked, 0) as clicks,
COALESCE(total_responded, 0) as conversions,
CASE WHEN COALESCE(total_sent, 0) > 0
     THEN ROUND(100.0 * COALESCE(total_opened, 0) / total_sent, 1) ELSE 0 END as open_rate,
...
```

---

## BUG-06 — CRM Dashboard Uses `conversion_count`

**Severity**: High  
**Location**: `frontend/src/pages/CRM/CRMHome.jsx`

### Root Cause

CRM Dashboard campaign summary widget reads `campaign.conversion_count`.  
API returns `total_responded`. Change render to `campaign.total_responded`.

---

## BUG-07 — SLA Check Crashes with TypeError (Timezone Mismatch)

**Severity**: High  
**Location**: `backend/routers/crm.py:366`

### Root Cause

```python
# Line 366 — datetime.now() is naive (no tzinfo)
hours_open = (datetime.now() - ticket.created_at).total_seconds() / 3600
```

`ticket.created_at` is `TIMESTAMPTZ` in PostgreSQL → Python receives a timezone-aware `datetime`.  
Subtracting naive from aware raises `TypeError: can't subtract offset-naive and offset-aware datetimes`.

### Additional Issue (same lines 366–368)

When `sla_hours` is null or 0, current code falls back to `24` silently — should return `"sla_not_configured"`.

### Fix

```python
from datetime import timezone

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
```

---

## ISSUE-07 — SQL Injection via Dynamic SET Clause in `update_opportunity`

**Severity**: Medium  
**Location**: `backend/routers/crm.py:238`

### Root Cause

```python
# Line 229 — all non-None fields from Pydantic model
updates = {k: v for k, v in data.model_dump().items() if v is not None}
# Line 238 — key goes directly into SQL string (not parameterized name)
set_clause = ", ".join(f"{k} = :{k}" for k in updates)
```

`OpportunityUpdate` (lines 44–52) limits the Pydantic fields, so direct Pydantic-based injection is not possible.
However, the pattern is fragile: if the model is extended carelessly, a field like `id` or `created_by` could be overwritten.  
Best practice (Constitution IV): whitelist column names explicitly.

### Fix

```python
OPPORTUNITY_ALLOWED_FIELDS = {
    "title", "stage", "probability", "expected_value",
    "expected_close_date", "assigned_to", "notes", "lost_reason"
}

updates = {k: v for k, v in data.model_dump().items()
           if v is not None and k in OPPORTUNITY_ALLOWED_FIELDS}
if not updates:
    raise HTTPException(**http_error(400, "no_data_to_update"))
```

---

## ISSUE-08 — Contact Form: Customer ID as Raw Text Input

**Severity**: Medium  
**Location**: `frontend/src/pages/CRM/CRMContacts.jsx`

### Root Cause

The Add/Edit Contact modal contains a plain `<input type="number" />` for `customer_id`.  
Users must know the internal integer ID — unusable in practice.

### Fix

Replace with a searchable dropdown using the existing `GET /api/sales/customers` endpoint.  
Pattern to follow: reuse `SearchableDropdown` or implement a `<select>` with filter, matching the
style used in `SupportTickets.jsx` for customer selection.

---

## ISSUE-09 — Campaign Report: Attribute Lead Modal Uses Raw Opportunity ID

**Severity**: Medium  
**Location**: `frontend/src/pages/Campaign/CampaignReport.jsx`

### Root Cause

The "Attribute Lead" modal has a plain `<input type="number" />` for opportunity ID.  
Users must know the internal integer — unusable in practice.

### Fix

Replace with a searchable dropdown using `GET /api/crm/opportunities`.

---

## ISSUE-10 — No In-App Notifications for CRM Events

**Severity**: Medium  
**Location**: `backend/routers/crm.py` (various endpoints)

### Root Cause

`notification_service.dispatch()` is available but never called from the CRM router.

### Events to Instrument

| Event | Trigger location | Recipient | Skip condition |
|-------|-----------------|-----------|----------------|
| Ticket assigned | `update_ticket` when `assigned_to` changes | new assignee | none |
| Opportunity won | `update_opportunity` when `stage = "won"` | `assigned_to` user | `assigned_to` is null |
| Opportunity lost | `update_opportunity` when `stage = "lost"` | `assigned_to` user | `assigned_to` is null |
| Campaign executed | campaign execute endpoint (post-send) | `created_by` user | none |

### Dispatch Signature

```python
await notification_service.dispatch(
    db=db,
    company_id=current_user.company_id,
    recipient_id=<user_id>,
    event_type="crm.<event>",
    title="<AR title>",
    body="<AR body>",
    feature_source="crm",
    reference_type="<ticket|opportunity|campaign>",
    reference_id=<id>,
    link="/crm/<path>/<id>"
)
```

Note: `dispatch()` is async — the endpoints calling it must be converted to `async def` or the call
must be wrapped with `asyncio.run()` / `run_coroutine_threadsafe()`. Preferred: convert to `async def`.

---

## ISSUE-11 — Legacy Columns in `marketing_campaigns`

**Severity**: Medium (schema hygiene)  
**Location**: `backend/database.py:4730–4733`

### Root Cause

`marketing_campaigns` table contains both column families:

| Old (stale, always 0) | New (live, written by campaign execute) |
|-----------------------|-----------------------------------------|
| `sent_count INT` (line 4730) | `total_sent INTEGER` (line 4740) |
| `open_count INT` (line 4731) | `total_opened INTEGER` (line 4742) |
| `click_count INT` (line 4732) | `total_clicked INTEGER` (line 4743) |
| `conversion_count INT` (line 4733) | `total_responded INTEGER` (line 4744) |

### Fix (Constitution XXVIII ⛔ — dual-update required)

1. **Alembic migration**: `ALTER TABLE marketing_campaigns DROP COLUMN sent_count, open_count, click_count, conversion_count`
2. **`database.py`**: Remove lines 4730–4733 from the `CREATE TABLE` DDL
3. Ensure BUG-05 backend fix is applied first so the ROI endpoint no longer references old columns

---

## Summary Table

| ID | File | Line(s) | Type | Severity |
|----|------|---------|------|----------|
| BUG-01 | `backend/routers/crm.py` | 475, 479, 480, 498 | Wrong column names in INSERT + missing duplicate check | Critical |
| BUG-02 | `frontend/src/pages/CRM/SupportTickets.jsx`, `CRMHome.jsx` | — | Frontend sends `content` instead of `comment` | Critical |
| BUG-03 | `frontend/src/pages/CRM/SupportTickets.jsx`, `CRMHome.jsx` | — | Frontend reads `user_name` instead of `author_name` | Critical |
| BUG-04 | `frontend/src/pages/CRM/MarketingCampaigns.jsx` | — | Reads old column names (`sent_count` etc.) | High |
| BUG-05 | `backend/routers/crm.py` | 1837–1862 | ROI analytics queries old columns | High |
| BUG-06 | `frontend/src/pages/CRM/CRMHome.jsx` | — | Dashboard reads `conversion_count` | High |
| BUG-07 | `backend/routers/crm.py` | 366–368 | `datetime.now()` vs timezone-aware `created_at` | High |
| ISSUE-07 | `backend/routers/crm.py` | 229, 238 | No whitelist on dynamic SET clause | Medium |
| ISSUE-08 | `frontend/src/pages/CRM/CRMContacts.jsx` | — | Raw numeric input for customer ID | Medium |
| ISSUE-09 | `frontend/src/pages/Campaign/CampaignReport.jsx` | — | Raw numeric input for opportunity ID | Medium |
| ISSUE-10 | `backend/routers/crm.py` | various | No CRM notifications dispatched | Medium |
| ISSUE-11 | `backend/database.py`, migrations | 4730–4733 | Legacy columns not dropped | Medium |
