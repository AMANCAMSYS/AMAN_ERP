# API Contracts: CRM Module Audit & Bug Fixes

**Feature**: 017-audit-crm  
**Date**: 2026-04-20

> This document records only the endpoints whose **request or response shape changes**.  
> URL paths and HTTP methods are unchanged (per spec assumption).

---

## 1. `POST /api/crm/tickets/{ticket_id}/comments`

### Change: Request body field rename (frontend fix)

**Before (broken)**
```json
{ "content": "Comment text", "is_internal": false }
```

**After (correct)**
```json
{ "comment": "Comment text", "is_internal": false }
```

**Backend**: No change — `CommentCreate.comment` is already correct (`crm.py:80`).  
**Frontend**: `SupportTickets.jsx` and `CRMHome.jsx` must send `comment` not `content`.

---

## 2. `GET /api/crm/tickets/{ticket_id}` — comments array

### Change: Response field rename (frontend fix)

**Before (broken — frontend was reading)**
```json
{
  "comments": [
    { "user_name": "Ahmed", "comment": "..." }
  ]
}
```

**After (correct — backend already returns)**
```json
{
  "comments": [
    { "author_name": "Ahmed", "comment": "..." }
  ]
}
```

**Backend**: No change — JOIN already aliases `cu.username as author_name` (`crm.py:355`).  
**Frontend**: `SupportTickets.jsx` and `CRMHome.jsx` must read `comment.author_name` not `comment.user_name`.

---

## 3. `GET /api/crm/tickets/{ticket_id}` — SLA fields

### Change: New/renamed response fields for SLA status

**Before (broken, crashes on timezone mismatch)**
```json
{
  "sla_breached": true,
  "hours_open": 25.3
}
```

**After (correct)**
```json
{
  "sla_status": "breached",        // "within_sla" | "breached" | "sla_not_configured"
  "sla_breached": true,            // kept for backwards compat (omitted when sla_not_configured)
  "hours_open": 25.3               // omitted when sla_not_configured
}
```

**Backend**: Fix `datetime.now()` → `datetime.now(timezone.utc)`, add `sla_not_configured` branch.  
**Frontend**: No breaking change — existing `sla_breached` boolean still present.

---

## 4. `POST /api/crm/opportunities/{opp_id}/convert-quotation`

### Change: New 409 error response for duplicate conversion

**Before**: No duplicate check — second call creates a second quotation silently.

**After (new error case)**
```json
HTTP 409 Conflict
{
  "detail": "quotation_already_exists",
  "quotation_id": 42
}
```

Success response unchanged:
```json
{ "quotation_id": 42, "quotation_number": "QT-2026-0001", "message": "تم تحويل الفرصة إلى عرض سعر" }
```

---

## 5. `GET /api/crm/analytics/campaign-roi`

### Change: Field renames in response (backend fix)

**Before (broken — always zeros)**
```json
{
  "campaigns": [
    {
      "sent": 0, "opens": 0, "clicks": 0, "conversions": 0,
      "open_rate": 0, "click_rate": 0, "conversion_rate": 0,
      "cost_per_conversion": 0
    }
  ],
  "summary": {
    "total_investment": 5000,
    "total_conversions": 0,
    "avg_cpc": 0,
    "overall_conversion_rate": 0
  }
}
```

**After (correct — reads live columns)**
```json
{
  "campaigns": [
    {
      "sent": 1200, "opens": 350, "clicks": 80, "conversions": 12,
      "open_rate": 29.2, "click_rate": 22.9, "conversion_rate": 1.0,
      "cost_per_conversion": 416.67
    }
  ],
  "summary": {
    "total_investment": 5000,
    "total_conversions": 12,
    "avg_cpc": 416.67,
    "overall_conversion_rate": 1.0
  }
}
```

Response field names (`sent`, `opens`, `clicks`, `conversions`) are SQL aliases — unchanged.  
Only the underlying SQL columns change from old to new.

---

## 6. Notification Events (new — no existing contract)

### `POST /api/crm/tickets/{ticket_id}` (PUT update) — side effect

When `assigned_to` changes, a notification is dispatched internally.  
No change to the HTTP response shape.

### `PUT /api/crm/opportunities/{opp_id}` — side effect

When `stage` becomes `won` or `lost` and `assigned_to` is non-null, a notification is dispatched.  
No change to the HTTP response shape.

---

## No-Change Endpoints

| Endpoint | Reason |
|----------|--------|
| `GET /api/crm/campaigns` | Backend returns `total_*` columns already; frontend fix only |
| `PUT /api/crm/opportunities/{opp_id}` | Whitelist fix is internal; same request/response shape |
| Add Contact (`POST /api/crm/contacts`) | Request body unchanged; only the form UI changes (dropdown vs. input) |
| Attribute Lead (`POST /api/.../attribute-lead`) | Request body unchanged; only the modal UI changes |
