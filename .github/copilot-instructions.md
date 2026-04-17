# aman Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-16

## Active Technologies
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0, APScheduler, Starlette middleware, openpyxl, i18next (004-audit-framework)
- PostgreSQL 15 (per-tenant `aman_{company_id}` DBs + system `aman_system` DB), Redis (004-audit-framework)
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first), Starlette BaseHTTPMiddleware, APScheduler, openpyxl, Pydantic, i18next (005-audit-framework)
- PostgreSQL 15 (multi-tenant `aman_{company_id}` + `aman_system`), Redis (rate limiting/cache) (005-audit-framework)
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0, python-jose (JWT), passlib (bcrypt), pyotp (TOTP), slowapi (rate limiting), Redis, Starlette middleware (004-audit-auth-security)
- PostgreSQL 15 (multi-tenant `aman_{company_id}` + `aman_system`), Redis (rate limiting, token blacklist cache) (004-audit-auth-security)
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), APScheduler, Pydantic, openpyxl, ReportLab, i18next, React Router (005-audit-core-admin)
- PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (rate limiting, cache — partially adopted) (005-audit-core-admin)
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, APScheduler, openpyxl, ReportLab, i18next, React Router (006-audit-accounting)
- PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (caching) (006-audit-accounting)
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, openpyxl, i18next, React Router (007-audit-treasury)
- PostgreSQL 15 (multi-tenant `aman_{company_id}` + system `aman_system`), Redis (rate limiting/cache) (007-audit-treasury)
- Python 3.12 (backend) · React 18 / Vite (frontend) + FastAPI · SQLAlchemy 2.0 (SQL-first via `text()`) · Pydantic · i18next · React Router · openpyxl · python-jose (008-audit-taxes)
- PostgreSQL 15 — per-tenant `aman_{company_id}` + system `aman_system`; Redis (rate limiting/cache) (008-audit-taxes)
- Python 3.12 (backend) · React 18 / Vite (frontend) + FastAPI · SQLAlchemy 2.0 (`text()` SQL-first) · Pydantic · `decimal.Decimal` · `gl_service.py` · `fiscal_lock.py` · `validate_branch_access` · `formatNumber()` · `useToast` hook (009-audit-inventory)
- PostgreSQL 15 — per-tenant `aman_{company_id}`; no schema changes required (009-audit-inventory)
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (`text()` SQL-first), Pydantic, i18next, React Router (009-audit-inventory)
- Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router (011-audit-purchases)

- Python 3.12.3 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0, Pydantic, Redis, i18next, React Router (003-constitution-remediation)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12.3 (backend), React 18 / Vite (frontend): Follow standard conventions

## Recent Changes
- 016-audit-manufacturing: Added Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router
- 015-audit-hr: Added Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router
- 013-audit-pos: Added Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, i18next, React Router


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
