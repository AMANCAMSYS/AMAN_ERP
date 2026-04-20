# Implementation Plan: CRM Module Audit & Bug Fixes

**Branch**: `017-audit-crm` | **Date**: 2026-04-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/017-audit-crm/spec.md`

---

## Summary

Fix 12 confirmed bugs and issues across the CRM module discovered by a full audit. Changes are
purely corrective — wrong column names in INSERT queries, mismatched field names between frontend and
backend, a timezone crash in SLA calculation, and missing CRM notifications. One schema migration
drops four legacy columns from `marketing_campaigns`. No new tables, no new endpoints, no API
URL changes.

---

## Technical Context

**Language/Version**: Python 3.12 (backend) · React 18 / Vite (frontend)  
**Primary Dependencies**: FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Alembic · i18next  
**Storage**: PostgreSQL 15 — one DB per tenant  
**Testing**: pytest (backend) · Vitest + React Testing Library (frontend)  
**Target Platform**: Linux server (backend) · Browser (frontend)  
**Project Type**: Web application (ERP)  
**Performance Goals**: SLA endpoint < 200ms p95  
**Constraints**: No URL/method changes (backwards compat); Constitution XXVIII — schema change dual-update  
**Scale/Scope**: All existing company tenants affected by migration

---

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| I — No float for money | ✅ Pass | No monetary columns touched |
| II — Multi-tenant isolation | ✅ Pass | All DB calls via `get_db_connection(company_id)` |
| IV — No `detail=str(e)` | ✅ Pass | All new HTTPExceptions use `http_error()` helper |
| IV — SQL injection | ✅ Addressed | ISSUE-07: whitelist added to `update_opportunity` |
| VII — SQL-first | ✅ Pass | Fixes use `db.execute(text(...))` with parameterized queries |
| XIII — CRM pipeline | ✅ Pass | Stage machine unchanged |
| XVII — Notifications | ✅ Addressed | ISSUE-10: dispatch added for 3 CRM events |
| XXV — No N+1 | ✅ Pass | `author_name` already via JOIN (line 354); no new loops |
| XXVII — UI consistency | ✅ Addressed | Dropdowns replace raw numeric inputs |
| XXVIII — Schema sync ⛔ | ✅ Addressed | Migration + `database.py` updated together for FR-012 |

**Complexity violations**: None.

---

## Project Structure

### Documentation (this feature)

```text
specs/017-audit-crm/
├── plan.md              ← this file
├── spec.md
├── research.md
├── data-model.md
├── contracts/
│   └── api-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md             ← created by /speckit.tasks (next phase)
```

### Source Code (affected files only)

```text
backend/
├── routers/
│   └── crm.py                   ← BUG-01 BUG-07 BUG-05 ISSUE-07 ISSUE-10
├── database.py                  ← FR-012 (remove legacy columns from CREATE TABLE)
└── migrations/versions/
    └── <ts>_drop_legacy_campaign_columns.py  ← FR-012 migration

frontend/src/pages/
├── CRM/
│   ├── CRMHome.jsx              ← BUG-02 BUG-03 BUG-06
│   ├── CRMContacts.jsx          ← ISSUE-08
│   ├── MarketingCampaigns.jsx   ← BUG-04
│   └── SupportTickets.jsx       ← BUG-02 BUG-03
└── Campaign/
    └── CampaignReport.jsx       ← ISSUE-09
```

---

## Phase 0 — Research

**Status**: Complete. See [`research.md`](./research.md) and [`data-model.md`](./data-model.md).

Key findings:
- BUG-01: 4 wrong identifiers in `crm.py:475–504` + missing duplicate check
- BUG-07: `datetime.now()` naive vs TIMESTAMPTZ `crm.py:366`; also missing `sla_not_configured` branch
- BUG-05: ROI analytics (`crm.py:1837–1862`) queries dropped/stale columns
- BUG-02/03/04/06: Frontend field-name mismatches
- ISSUE-11: `database.py:4730–4733` — 4 legacy columns still in DDL

---

## Phase 1 — Implementation Tasks

Tasks are ordered by dependency. Items within the same group can be done in parallel.

### Group A — Critical Backend Fixes (no dependencies)

#### A1 — Fix `convert_to_quotation` column names + duplicate check (FR-001)

**File**: `backend/routers/crm.py`  
**Lines**: 460–519

Steps:
1. Before the customer check, query `won_quotation_id` from `sales_opportunities`.
   If non-null, raise `HTTPException(409, detail={"error": "quotation_already_exists", "quotation_id": existing_id})`.
2. Fix `generate_sequential_number` 4th arg: `"quotation_number"` → `"sq_number"`.
3. Fix INSERT columns: `quotation_number` → `sq_number`, `valid_until` → `expiry_date`.
4. Fix line INSERT column: `quotation_id` → `sq_id`.
5. After commit, `UPDATE sales_opportunities SET won_quotation_id = :qid WHERE id = :opp_id`.
6. Remove the bare `raise HTTPException(status_code=400, detail="...")` on line 472 and replace with `raise HTTPException(**http_error(400, "opportunity_no_customer"))` (Constitution IV).

#### A2 — Fix SLA timezone crash + sla_not_configured (FR-007)

**File**: `backend/routers/crm.py`  
**Lines**: 364–368

Steps:
1. Add `from datetime import timezone` at top of file (or in the function).
2. Replace lines 364–368 with:
   ```python
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

#### A3 — Fix campaign ROI analytics to use `total_*` columns (FR-005)

**File**: `backend/routers/crm.py`  
**Lines**: 1835–1865

Steps:
1. In the per-campaign SELECT (lines 1837–1851), replace:
   - `sent_count` → `total_sent`
   - `open_count` → `total_opened`
   - `click_count` → `total_clicked`
   - `conversion_count` → `total_responded`
2. In the summary SELECT (lines 1855–1864), apply same replacements.
3. Update `ORDER BY` (line 1851): `COALESCE(conversion_count, 0)` → `COALESCE(total_responded, 0)`.

#### A4 — Add whitelist to `update_opportunity` (FR-008)

**File**: `backend/routers/crm.py`  
**Lines**: 226–245

Steps:
1. Define constant above the function:
   ```python
   OPPORTUNITY_ALLOWED_FIELDS = {
       "title", "stage", "probability", "expected_value",
       "expected_close_date", "assigned_to", "notes", "lost_reason"
   }
   ```
2. Change line 229 filter to:
   ```python
   updates = {k: v for k, v in data.model_dump().items()
              if v is not None and k in OPPORTUNITY_ALLOWED_FIELDS}
   ```

---

### Group B — CRM Notifications (FR-011) — depends on nothing

#### B1 — Dispatch notification on ticket assignment

**File**: `backend/routers/crm.py`  
**Location**: `update_ticket` function (lines 412–433)

Steps:
1. Import `notification_service` at top of file.
2. Convert `update_ticket` to `async def`.
3. After `db.commit()`, check if `updates.get("assigned_to")` is set.
4. If yes, call:
   ```python
   await notification_service.dispatch(
       db=db,
       company_id=current_user.company_id,
       recipient_id=updates["assigned_to"],
       event_type="crm.ticket_assigned",
       title="تذكرة جديدة مُسندة إليك",
       body=f"تم إسناد التذكرة #{ticket_id} إليك",
       feature_source="crm",
       reference_type="ticket",
       reference_id=ticket_id,
       link=f"/crm/tickets/{ticket_id}"
   )
   ```

#### B2 — Dispatch notification on opportunity stage won/lost

**File**: `backend/routers/crm.py`  
**Location**: `update_opportunity` function (lines 226–245)

Steps:
1. Convert `update_opportunity` to `async def`.
2. After `db.commit()`, check if `updates.get("stage")` is in `{"won", "lost"}`.
3. Fetch `assigned_to` from `sales_opportunities` for this `opp_id`.
4. If `assigned_to` is non-null:
   ```python
   stage = updates["stage"]
   await notification_service.dispatch(
       db=db,
       company_id=current_user.company_id,
       recipient_id=assigned_to,
       event_type=f"crm.opportunity_{stage}",
       title="تحديث الفرصة البيعية",
       body=f"تم تحديث الفرصة إلى مرحلة {stage}",
       feature_source="crm",
       reference_type="opportunity",
       reference_id=opp_id,
       link=f"/crm/opportunities/{opp_id}"
   )
   ```

#### B3 — Dispatch notification on campaign execution complete

**File**: `backend/routers/crm.py`  
**Location**: campaign execute endpoint (find by searching `execute` in `/campaigns`)

Steps:
1. Convert campaign execute endpoint to `async def`.
2. After execution completes, dispatch to `campaign.created_by`:
   ```python
   await notification_service.dispatch(
       db=db,
       company_id=current_user.company_id,
       recipient_id=campaign_created_by,
       event_type="crm.campaign_executed",
       title="اكتملت الحملة التسويقية",
       body=f"تم إرسال الحملة '{campaign_name}' إلى {total_sent} مستلم",
       feature_source="crm",
       reference_type="campaign",
       reference_id=campaign_id,
       link=f"/campaigns/{campaign_id}/report"
   )
   ```

---

### Group C — Schema Migration (FR-012) — do after A3 is merged

#### C1 — Remove legacy columns from `database.py`

**File**: `backend/database.py`  
**Lines**: 4730–4733

Delete these four lines:
```python
sent_count INT DEFAULT 0,
open_count INT DEFAULT 0,
click_count INT DEFAULT 0,
conversion_count INT DEFAULT 0,
```

#### C2 — Create Alembic migration

**File**: `backend/migrations/versions/<timestamp>_drop_legacy_campaign_columns.py`

```python
"""drop legacy campaign metric columns

Revision ID: <auto>
Revises: <previous>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.drop_column('marketing_campaigns', 'sent_count')
    op.drop_column('marketing_campaigns', 'open_count')
    op.drop_column('marketing_campaigns', 'click_count')
    op.drop_column('marketing_campaigns', 'conversion_count')

def downgrade():
    op.add_column('marketing_campaigns',
        sa.Column('sent_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('marketing_campaigns',
        sa.Column('open_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('marketing_campaigns',
        sa.Column('click_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('marketing_campaigns',
        sa.Column('conversion_count', sa.Integer(), server_default='0', nullable=True))
```

---

### Group D — Frontend Fixes (no backend dependencies; parallel with Groups A/B)

#### D1 — Fix ticket comment field names (FR-002 + FR-003)

**Files**: `frontend/src/pages/CRM/SupportTickets.jsx`, `frontend/src/pages/CRM/CRMHome.jsx`

Steps per file:
1. Find comment submit handler — change `{ content: commentText }` → `{ comment: commentText }`.
2. Find comment render — change `comment.user_name` → `comment.author_name`.

#### D2 — Fix campaign metrics field names (FR-004)

**File**: `frontend/src/pages/CRM/MarketingCampaigns.jsx`

Steps:
1. Replace all reads: `sent_count` → `total_sent`, `open_count` → `total_opened`,
   `click_count` → `total_clicked`, `conversion_count` → `total_responded`.

#### D3 — Fix CRM Dashboard campaign widget (FR-006)

**File**: `frontend/src/pages/CRM/CRMHome.jsx`

Steps:
1. Find the campaign summary widget render.
2. Replace `campaign.conversion_count` → `campaign.total_responded`.

#### D4 — Replace customer_id text input with searchable dropdown (FR-009)

**File**: `frontend/src/pages/CRM/CRMContacts.jsx`

Steps:
1. On component mount (or modal open), fetch customers from `GET /api/sales/customers?limit=100`.
2. Store in local state `customers`.
3. Replace `<input type="number" ... />` for `customer_id` with a `<select>` filtered by typed name,
   or a `SearchableSelect` component if one exists in the codebase.
4. On selection, set `customer_id` to the selected customer's `id`.
5. Show "لا يوجد عملاء" empty state when list is empty.

#### D5 — Replace opportunity ID text input with searchable dropdown (FR-010)

**File**: `frontend/src/pages/Campaign/CampaignReport.jsx`

Steps:
1. On "Attribute Lead" modal open, fetch opportunities from `GET /api/crm/opportunities`.
2. Store in local state `opportunities`.
3. Replace raw `<input type="number" />` with a `<select>` filtered by opportunity title.
4. On selection, set opportunity ID to the selected value.

---

## Phase 2 — Verification

### Backend Verification

| Check | Command / Method |
|-------|-----------------|
| Import check | `python -c "from routers.crm import router"` |
| SLA timezone fix | Hit `GET /api/crm/tickets/{id}` for any ticket — no TypeError |
| Convert quotation | Create opportunity, call convert endpoint — verify `sq_number`, `expiry_date` in DB |
| Duplicate convert | Call convert twice — second must return 409 |
| ROI analytics | `GET /api/crm/analytics/campaign-roi` — non-zero rates for executed campaigns |
| Notifications | Assign ticket — check `notifications` table for new row |
| Migration | `alembic upgrade head` on test DB — columns dropped without error |
| Schema parity | Fresh `database.py` create vs. migrated DB — identical column list |

### Frontend Verification

| Check | Method |
|-------|--------|
| Comment submit | Submit comment on any ticket — verify 201 response (not 422) |
| Author name | Comments thread shows username, not blank |
| Campaign metrics | Campaign list shows non-zero Sent/Opened/Clicked/Responded for executed campaigns |
| Customer dropdown | Add Contact modal shows customer search dropdown |
| Opportunity dropdown | Attribute Lead modal shows opportunity search dropdown |

---

## Implementation Order (suggested)

```
Day 1:
  A1 (BUG-01 convert quotation)   ← highest business impact
  A2 (BUG-07 SLA timezone)        ← runtime crash fix
  D1 (BUG-02/03 comment fields)   ← parallel, frontend only

Day 2:
  A3 (BUG-05 ROI analytics)       ← unblocks C1/C2
  D2 (BUG-04 campaign metrics)    ← parallel, frontend only
  D3 (BUG-06 dashboard widget)    ← parallel, frontend only
  A4 (ISSUE-07 whitelist)         ← quick, no dependencies

Day 3:
  C1 + C2 (schema migration)      ← after A3 confirmed working
  B1 + B2 + B3 (notifications)    ← can be parallel

Day 4:
  D4 (ISSUE-08 contact dropdown)  ← UI polish
  D5 (ISSUE-09 lead modal)        ← UI polish
  Full verification pass
```

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Migration drops columns still referenced by un-merged code | Apply A3 (backend fix) before or together with C1/C2 |
| `async def` conversion on endpoints breaks existing sync callers | FastAPI handles both sync and async routes natively; no caller impact |
| `generate_sequential_number` with new column name finds no rows → returns wrong prefix | The function queries `MAX()` of the column — if 0 rows it starts from 1, which is correct |
| Customer dropdown in contacts fetches all customers (could be large list) | Add `?limit=100&search=` param; paginate or debounce search |
