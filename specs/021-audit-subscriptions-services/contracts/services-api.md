# API Contract Changes: Services

**Module**: Services (`/api/services/*`)
**Date**: 2026-04-20

## Changed Endpoints

### POST /api/services/requests
**Change**: Now accepts Pydantic schema instead of raw dict
- Request body validated: `title` (required, max 255), `priority` (enum), `branch_id` (optional), etc.
- Returns `422` on validation failure (was `500`)
- Branch access validated: returns `403` if user lacks access to specified branch
- Audit logged via `log_activity()`

### PUT /api/services/requests/{id}
**Change**: Pydantic schema + status transition validation
- `status` field validated against state machine:
  - `pending` → `assigned`, `cancelled`
  - `assigned` → `in_progress`, `cancelled`
  - `in_progress` → `on_hold`, `completed`, `cancelled`
  - `on_hold` → `in_progress`, `cancelled`
  - `completed` → (no transitions)
  - `cancelled` → (no transitions)
- Invalid transitions return `400` with message describing valid transitions
- Branch access validated

### DELETE /api/services/requests/{id}
**Change**: Soft-delete instead of hard delete
- Record marked `is_deleted = true`
- Related costs also soft-deleted

### POST /api/services/requests/{id}/assign
**Change**: Pydantic schema (`assigned_to` as required int)
- Returns `422` if `assigned_to` missing
- Sets status to `assigned` if currently `pending`

### POST /api/services/requests/{id}/costs
**Change**: Pydantic schema (`description`, `amount` as Decimal, `cost_type`)
- Returns `422` on validation failure
- Soft-delete on DELETE (was hard delete)

### PUT /api/services/documents/{id}/meta
**Change**: Pydantic schema for metadata update
- `tags` accepted as JSON array (was TEXT)
- `access_level` validated as enum

### GET /api/services/documents/{id}/download (NEW)
**Change**: New endpoint for file download
- Validates access level against user role
- Returns file via `FileResponse`
- Returns `404` if file not found on disk

### GET /api/services/requests (list)
**Change**: Pagination added
- Accepts `page` (default 1), `per_page` (default 25, max 100)
- Response includes pagination metadata: `total`, `page`, `per_page`, `pages`

### GET /api/services/documents (list)
**Change**: Pagination added (same params as above)

## Response Shape Changes

### Service Request Record
```json
{
  "id": 1,
  "title": "AC Repair",
  "status": "in_progress",
  "branch_id": 1,
  "is_deleted": false
}
```
New fields: `branch_id`, `is_deleted`
Removed fields: `file_path` (from document responses — replaced by `download_url`)

### Document Record
```json
{
  "id": 1,
  "title": "Invoice Scan",
  "tags": ["invoice", "scan"],
  "download_url": "/api/services/documents/1/download",
  "is_deleted": false
}
```
Changed: `tags` from string to JSON array, `file_path` removed, `download_url` added, `is_deleted` added

### List Response (paginated)
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 25,
  "pages": 6
}
```
