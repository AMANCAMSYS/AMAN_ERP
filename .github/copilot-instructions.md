# aman Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-14

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
- 006-audit-accounting: Added Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), Pydantic, APScheduler, openpyxl, ReportLab, i18next, React Router
- 005-audit-core-admin: Added Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0 (SQL-first via `text()`), APScheduler, Pydantic, openpyxl, ReportLab, i18next, React Router
- 004-audit-auth-security: Added Python 3.12 (backend), React 18 / Vite (frontend) + FastAPI, SQLAlchemy 2.0, python-jose (JWT), passlib (bcrypt), pyotp (TOTP), slowapi (rate limiting), Redis, Starlette middleware


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
