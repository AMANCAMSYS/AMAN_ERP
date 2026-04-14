# Quickstart: Audit Core Admin Module

**Branch**: `005-audit-core-admin` | **Date**: 2026-04-14

---

## Prerequisites

- Python 3.12+, Node.js 18+
- PostgreSQL 15 running with `aman_system` + at least one `aman_{company_id}` database
- Redis (optional — in-memory fallback available)
- Virtual environment activated: `source .venv/bin/activate`

## Setup

```bash
cd /home/omar/Desktop/aman
git checkout 005-audit-core-admin
source .venv/bin/activate
cd backend
pip install -r requirements.txt
```

## Running the Backend

```bash
cd backend
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Linting

```bash
cd backend
ruff check .
```

## Key Files to Modify (Audit Scope)

### Backend Routers (10 files)
- `backend/routers/companies.py` — Company CRUD
- `backend/routers/branches.py` — Branch CRUD
- `backend/routers/settings.py` — Settings management
- `backend/routers/notifications.py` — Notifications + WebSocket
- `backend/routers/audit.py` — Audit log queries
- `backend/routers/data_import.py` — Bulk data import
- `backend/routers/system_completion.py` — Onboarding wizard
- `backend/routers/external.py` — Webhooks, API keys
- `backend/routers/parties.py` — Customer/supplier listing
- `backend/routers/dashboard.py` — Dashboard metrics

### Backend Services (3 files)
- `backend/services/notification_service.py` — Multi-channel dispatch
- `backend/services/email_service.py` — SMTP email
- `backend/services/scheduler.py` — APScheduler jobs

### Backend Utils (9 files)
- `backend/utils/audit.py` — `log_activity()` function
- `backend/utils/cache.py` — Hybrid cache
- `backend/utils/email.py` — Email helpers
- `backend/utils/exports.py` — PDF/Excel generation
- `backend/utils/logging_config.py` — Structured logging
- `backend/utils/webhooks.py` — HMAC-signed dispatch
- `backend/utils/ws_manager.py` — WebSocket manager
- `backend/utils/sql_builder.py` — Safe query builder
- `backend/utils/sql_safety.py` — SQL identifier validation

### Backend Config (2 files)
- `backend/config.py` — App configuration
- `backend/database.py` — Multi-tenant DB routing

## Verification Checklist

After each phase, verify:

1. **No error leaks**: `grep -rn 'detail=str(e)\|detail=f"' backend/routers/ | grep -v '#'`
2. **Syntax check**: `python -m py_compile <file>`
3. **Audit logging**: `grep -rn 'log_activity' backend/routers/{companies,branches,settings,external}.py`
4. **Tests pass**: `pytest tests/ -v`

## Design Documents

- [spec.md](spec.md) — Feature specification (8 stories, 21 FRs)
- [research.md](research.md) — Research decisions (14 items)
- [data-model.md](data-model.md) — Entity documentation + schema additions
- [contracts/api-conformance.md](contracts/api-conformance.md) — Post-audit API contracts
