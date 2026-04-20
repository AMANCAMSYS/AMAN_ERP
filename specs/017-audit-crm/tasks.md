# Tasks: CRM Module Audit & Bug Fixes

**Input**: Design documents from `specs/017-audit-crm/`  
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/api-contracts.md ✅

**Organization**: Tasks grouped by user story to enable independent implementation and testing.  
**Tests**: Not requested — no test tasks generated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story this task belongs to (US1–US7 from spec.md)
- Every task includes an exact file path

---

## Phase 1: Setup

**Purpose**: One-time verification before making any changes.

- [x] T001 Confirm Alembic is connected and baseline migration is current by running `alembic current` from `backend/` — note the revision ID for use in T017

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Security fix that must be applied before any opportunity endpoint work begins.

**⚠️ CRITICAL**: T002 must be complete before any work on Phase 3 (US1) begins.

- [x] T002 Add `OPPORTUNITY_ALLOWED_FIELDS` constant and update the `updates` filter dict in `update_opportunity` to only include whitelisted keys in `backend/routers/crm.py:229–238` (FR-008)

**Checkpoint**: Whitelist in place — US1 work can now begin safely.

---

## Phase 3: User Story 1 — Convert Opportunity to Quotation (Priority: P1) 🎯 MVP

**Goal**: Sales rep can convert an opportunity to a quotation exactly once; duplicate conversion is blocked; quotation is created with the correct column names.

**Independent Test**: Create an opportunity with a linked customer → call `POST /api/crm/opportunities/{id}/convert-quotation` → verify a `sales_quotations` row exists with `sq_number` and `expiry_date` populated, and `sales_quotation_lines` row exists with `sq_id` set.  
Call the endpoint a second time → verify HTTP 409 is returned.

- [x] T003 [US1] Add duplicate-conversion guard: before the customer check, query `won_quotation_id` from `sales_opportunities`; if non-null raise `HTTPException(409, ...)` with the existing quotation ID in `backend/routers/crm.py:465–472`
- [x] T004 [US1] Fix `generate_sequential_number` 4th argument from `"quotation_number"` to `"sq_number"` in `backend/routers/crm.py:475`
- [x] T005 [US1] Fix INSERT column names in the `sales_quotations` INSERT: rename `quotation_number` → `sq_number` and `valid_until` → `expiry_date` in `backend/routers/crm.py:478–480`
- [x] T006 [US1] Fix INSERT column name in the `sales_quotation_lines` INSERT: rename `quotation_id` → `sq_id` in `backend/routers/crm.py:498`
- [x] T007 [US1] After `db.commit()`, write `won_quotation_id = quot_id` back to `sales_opportunities` for this `opp_id` in `backend/routers/crm.py:507–508`
- [x] T008 [US1] Replace bare `HTTPException(status_code=400, detail="يجب تحديد عميل...")` on line 472 with `raise HTTPException(**http_error(400, "opportunity_no_customer"))` in `backend/routers/crm.py:472` (Constitution IV)

**Checkpoint**: User Story 1 fully functional — quota conversion works end-to-end; duplicate is rejected.

---

## Phase 4: User Story 2 — Support Agent Adds Comment to a Ticket (Priority: P1)

**Goal**: Comment submit sends `{ comment }` (not `{ content }`); comment thread displays `author_name` (not blank).

**Independent Test**: Open any ticket → type a comment → submit → verify HTTP 201 (not 422); then reload the ticket detail → verify the comment thread shows the submitting user's name in the author field.

- [x] T009 [P] [US2] Change comment submit handler to send `{ comment: commentText }` instead of `{ content: commentText }` in `frontend/src/pages/CRM/SupportTickets.jsx` (FR-002)
- [x] T010 [P] [US2] Change comment submit handler to send `{ comment: commentText }` instead of `{ content: commentText }` in `frontend/src/pages/CRM/CRMHome.jsx` (FR-002)
- [x] T011 [US2] Change comment thread render from `comment.user_name` to `comment.author_name` in `frontend/src/pages/CRM/SupportTickets.jsx` (FR-003)
- [x] T012 [US2] Change comment thread render from `comment.user_name` to `comment.author_name` in `frontend/src/pages/CRM/CRMHome.jsx` (FR-003)

**Checkpoint**: User Story 2 fully functional — comments save with correct field and display correct author name.

---

## Phase 5: User Story 3 — Marketing Manager Views Campaign Engagement Metrics (Priority: P1)

**Goal**: Campaign list shows live Sent / Opened / Clicked / Responded values; CRM Dashboard campaign widget shows correct responded count.

**Independent Test**: Execute a campaign against any segment → open the Campaigns list → Sent, Opened, Clicked, Responded columns must show non-zero values matching what is in the database `total_*` columns.

- [x] T013 [P] [US3] Replace all four old field reads in the campaign list table with new names: `sent_count` → `total_sent`, `open_count` → `total_opened`, `click_count` → `total_clicked`, `conversion_count` → `total_responded` in `frontend/src/pages/CRM/MarketingCampaigns.jsx` (FR-004)
- [x] T014 [P] [US3] Replace `campaign.conversion_count` with `campaign.total_responded` in the campaign summary widget in `frontend/src/pages/CRM/CRMHome.jsx` (FR-006)

**Checkpoint**: User Story 3 fully functional — campaign metrics show live values everywhere.

---

## Phase 6: User Story 4 — Support Agent Tracks SLA Deadline on a Ticket (Priority: P2)

**Goal**: SLA check never throws `TypeError`; tickets with null/zero `sla_hours` return `"sla_not_configured"`.

**Independent Test**: Call `GET /api/crm/tickets/{id}` for any open ticket — response must include `sla_status` field with no server error. For a ticket where `sla_hours` is null, `sla_status` must be `"sla_not_configured"`.

- [x] T015 [US4] Add `from datetime import timezone` import (or extend existing `datetime` import) at the top of `backend/routers/crm.py`
- [x] T016 [US4] Replace lines 364–368 in `get_ticket` in `backend/routers/crm.py`: (a) if `sla_hours` is null/zero → set `result["sla_status"] = "sla_not_configured"` and skip breach logic; (b) otherwise use `datetime.now(timezone.utc)` for the subtraction and set `result["sla_status"]` to `"breached"` or `"within_sla"` (FR-007)

**Checkpoint**: User Story 4 fully functional — SLA check returns correct status without any server errors.

---

## Phase 7: User Story 5 — Sales Manager Views Campaign ROI Analytics (Priority: P2)

**Goal**: ROI analytics endpoint reads live `total_*` columns; legacy columns are then safe to drop.

**Independent Test**: Call `GET /api/crm/analytics/campaign-roi` after at least one executed campaign — `open_rate`, `click_rate`, `conversion_rate` must be non-zero; `total_conversions` in summary must be non-zero.

- [x] T017 [US5] In `campaign_roi_analytics` per-campaign SELECT (lines 1837–1851): replace `sent_count` → `total_sent`, `open_count` → `total_opened`, `click_count` → `total_clicked`, `conversion_count` → `total_responded`, update all CASE expressions and ORDER BY accordingly in `backend/routers/crm.py:1835–1851`
- [x] T018 [US5] In `campaign_roi_analytics` summary SELECT (lines 1855–1864): replace `conversion_count` → `total_responded`, `sent_count` → `total_sent` in all SUM/CASE expressions in `backend/routers/crm.py:1855–1864`
- [x] T019 [US5] Remove lines 4730–4733 from the `marketing_campaigns` `CREATE TABLE` DDL in `backend/database.py` — delete `sent_count`, `open_count`, `click_count`, `conversion_count` entries (FR-012, Constitution XXVIII — must be done together with T020)
- [x] T020 [US5] Create Alembic migration file `backend/migrations/versions/<timestamp>_drop_legacy_campaign_columns.py` with `upgrade()` dropping the four columns and `downgrade()` restoring them (FR-012, Constitution XXVIII — must be applied together with T019)

> ⚠️ T019 and T020 are a Constitution XXVIII pair — both must be committed together.

**Checkpoint**: User Story 5 fully functional — ROI analytics shows real data; legacy columns gone from schema.

---

## Phase 8: User Story 6 — CRM User Links a Contact to a Customer (Priority: P3)

**Goal**: Contact form shows searchable customer dropdown; Campaign Report "Attribute Lead" modal shows searchable opportunity dropdown.

**Independent Test**: Open the Add Contact modal — a customer search dropdown must appear. Open a Campaign Report → click "Attribute Lead" — an opportunity search dropdown must appear. Selecting from either dropdown and saving must persist the correct ID.

- [x] T021 [US6] On Add/Edit Contact modal open, fetch customers from `GET /api/sales/customers?limit=100` and store in component state in `frontend/src/pages/CRM/CRMContacts.jsx` (FR-009)
- [x] T022 [US6] Replace the raw `<input type="number" />` for `customer_id` with a filterable `<select>` rendered from customer state; add empty-state message when list is empty in `frontend/src/pages/CRM/CRMContacts.jsx` (FR-009)
- [x] T023 [US6] On "Attribute Lead" modal open, fetch opportunities from `GET /api/crm/opportunities` and store in component state in `frontend/src/pages/Campaign/CampaignReport.jsx` (FR-010)
- [x] T024 [US6] Replace the raw `<input type="number" />` for opportunity ID with a filterable `<select>` rendered from opportunity state in `frontend/src/pages/Campaign/CampaignReport.jsx` (FR-010)

**Checkpoint**: User Story 6 fully functional — both forms show searchable dropdowns; IDs saved correctly.

---

## Phase 9: User Story 7 — In-App Notifications for CRM Events (Priority: P3)

**Goal**: Ticket assignment, opportunity won/lost, and campaign execution each trigger an in-app notification to the relevant user.

**Independent Test**: Assign a ticket to a user → check the `notifications` table for a new row with `event_type = "crm.ticket_assigned"` and `recipient_id` = the assigned user's ID.

- [x] T025 [US7] Add `from services import notification_service` (or the correct import path) at the top of `backend/routers/crm.py` — verify the import resolves without error
- [x] T026 [US7] Convert `update_ticket` to `async def` in `backend/routers/crm.py:412`; after `db.commit()`, if `updates.get("assigned_to")` is set, call `await notification_service.dispatch(...)` with `event_type="crm.ticket_assigned"`, `recipient_id=updates["assigned_to"]`, `reference_type="ticket"`, `reference_id=ticket_id`, `link=f"/crm/tickets/{ticket_id}"` (FR-011)
- [x] T027 [US7] Convert `update_opportunity` to `async def` in `backend/routers/crm.py:226`; after `db.commit()`, if `updates.get("stage")` is in `{"won", "lost"}`, fetch `assigned_to` for this opportunity; if non-null, call `await notification_service.dispatch(...)` with `event_type=f"crm.opportunity_{stage}"`, `recipient_id=assigned_to`, `reference_type="opportunity"`, `reference_id=opp_id`, `link=f"/crm/opportunities/{opp_id}"` (FR-011)
- [x] T028 [US7] Locate the campaign execute endpoint in `backend/routers/crm.py` (search for `/campaigns/{campaign_id}/execute`); convert to `async def`; after execution completes, fetch `created_by` for the campaign; call `await notification_service.dispatch(...)` with `event_type="crm.campaign_executed"`, `recipient_id=campaign_created_by`, `reference_type="campaign"`, `reference_id=campaign_id`, `link=f"/campaigns/{campaign_id}/report"`, body includes total recipients count (FR-011)

**Checkpoint**: User Story 7 fully functional — in-app notifications dispatched for all three CRM events.

---

## Phase 10: Polish & Cross-Cutting Concerns

- [x] T029 [P] Remove the dead `branch_id` field from `CampaignForm.jsx` form and its associated state/handler in `frontend/src/pages/Campaign/CampaignForm.jsx` (per spec assumptions — no functional change)
- [x] T030 [P] Grep `backend/routers/crm.py` for any remaining references to `quotation_number`, `valid_until`, `quotation_id` (old column names) and confirm zero matches
- [x] T031 [P] Grep `backend/routers/crm.py` and all frontend CRM/Campaign pages for any remaining references to `sent_count`, `open_count`, `click_count`, `conversion_count` and confirm zero matches
- [x] T032 Run `alembic upgrade head` on a clean test tenant DB and confirm the four legacy columns are absent from `marketing_campaigns`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └── Phase 2 (Foundational — whitelist)
        └── Phase 3 (US1 — convert quotation)   ← MVP
              ├── Phase 4 (US2 — comments)        ← parallel with US1 if staffed
              ├── Phase 5 (US3 — campaign metrics) ← parallel with US1 if staffed
              ├── Phase 6 (US4 — SLA fix)          ← parallel with US1 if staffed
              ├── Phase 7 (US5 — ROI + migration)  ← migration requires T017/T018 first
              ├── Phase 8 (US6 — dropdowns)        ← parallel with others
              └── Phase 9 (US7 — notifications)    ← parallel with others
                    └── Phase 10 (Polish)
```

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (T002). No other story dependencies.
- **US2 (P1)**: Independent — can start any time after setup. No backend changes required.
- **US3 (P1)**: Independent — frontend-only. No backend changes required.
- **US4 (P2)**: Independent of US1–US3. Single backend function change.
- **US5 (P2)**: **T019/T020 must come after T017/T018** — cannot drop columns before fixing the query that reads them.
- **US6 (P3)**: Independent — frontend-only (uses existing endpoints).
- **US7 (P3)**: Independent — backend notification calls added to existing functions. Depends on T025 (import).

### Within Each User Story

- US1: T003 → T004 → T005 → T006 → T007 → T008 (sequential — same function)
- US2: T009 ∥ T010, then T011 (same file as T009), T012 (same file as T010)
- US3: T013 ∥ T014 (different files — parallel)
- US4: T015 → T016 (T015 must precede T016)
- US5: T017 → T018 → T019 + T020 (T019 and T020 must be committed together)
- US6: T021 → T022 (same file, sequential); T023 → T024 (same file, sequential); T021∥T023 (different files)
- US7: T025 → T026 ∥ T027 ∥ T028 (T025 import first; then three functions in parallel)

### Parallel Opportunities

- US2, US3, US4, US6 (all frontend or single-function backend) can be worked in parallel once setup is done
- US7 can proceed in parallel with US5, US6
- Within US2: T009 and T010 are parallel (different files)
- Within US3: T013 and T014 are parallel (different files)
- Within US6: T021–T022 (CRMContacts.jsx) and T023–T024 (CampaignReport.jsx) are parallel tracks
- Within US7: T026, T027, T028 are parallel (different functions in same file, non-overlapping lines)

---

## Parallel Example: User Story 2

```
# Parallel: fix submit field name in two files simultaneously
Task T009: SupportTickets.jsx — change content → comment in submit handler
Task T010: CRMHome.jsx       — change content → comment in submit handler

# Then: fix author name render (each in respective file from above)
Task T011: SupportTickets.jsx — change user_name → author_name
Task T012: CRMHome.jsx       — change user_name → author_name
```

## Parallel Example: User Story 6

```
# Parallel: two different files, independent changes
Task T021–T022: CRMContacts.jsx  — customer dropdown
Task T023–T024: CampaignReport.jsx — opportunity dropdown
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002)
3. Complete Phase 3: User Story 1 (T003–T008)
4. **STOP and VALIDATE**: Test convert-quotation end-to-end, confirm duplicate 409
5. Deliver / demo

### Incremental Delivery

| Step | Phases | Delivers |
|------|--------|---------|
| 1 | P1 + P2 | Foundation ready |
| 2 | P3 (US1) | Quotation conversion working ← MVP |
| 3 | P4 + P5 (US2, US3) | Ticket comments + campaign metrics fixed |
| 4 | P6 + P7 (US4, US5) | SLA crash fixed + ROI analytics live + migration applied |
| 5 | P8 (US6) | Customer and opportunity dropdowns |
| 6 | P9 (US7) | CRM notifications live |
| 7 | P10 | Polish + cleanup |

### Parallel Team Strategy (if 2 developers)

After T001–T002 (setup/foundational):

- **Dev A**: US1 (T003–T008) → US4 (T015–T016) → US5 (T017–T020)
- **Dev B**: US2 (T009–T012) ∥ US3 (T013–T014) → US6 (T021–T024) → US7 (T025–T028)

---

## Notes

- `[P]` tasks operate on different files or non-overlapping lines — safe to execute concurrently
- T019 and T020 are a Constitution XXVIII pair — commit them atomically in the same git commit
- T015 (import) and T026–T028 (async conversions) all touch `crm.py` but at non-overlapping lines
- Converting functions to `async def` (T026–T028) is safe in FastAPI — no caller changes needed
- If `notification_service.dispatch()` is not importable directly, check `backend/services/notification_service.py` for the correct module path before T025
- Commit after each Phase checkpoint to keep history clean
