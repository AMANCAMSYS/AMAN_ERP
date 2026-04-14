# Quickstart: Authentication & Security Audit

**Feature**: `004-audit-auth-security`  
**Date**: 2026-04-14

## Prerequisites

- Python 3.12 with venv activated (`source .venv/bin/activate`)
- PostgreSQL 15 running with `aman_system` database
- Redis running (for rate limiting and token cache)
- Backend dependencies installed (`pip install -r backend/requirements.txt`)

## Running the Audit

### 1. Verify the scope

The audit covers these files:

```bash
# Backend routers
ls -la backend/routers/auth.py backend/routers/security.py backend/routers/sso.py backend/routers/roles.py backend/routers/mobile.py

# Utilities
ls -la backend/utils/permissions.py backend/utils/security_middleware.py backend/utils/limiter.py backend/utils/sql_safety.py

# Core
ls -la backend/config.py backend/database.py
```

### 2. Run existing tests

```bash
cd backend
pytest tests/ -k "auth or security or login or permission" -v
```

### 3. Grep for known violations

```bash
# Exception detail leaks (Constitution §IV violation)
grep -rn "detail=str(e)" backend/routers/ --include="*.py"

# print() in production code
grep -rn "^[^#]*print(" backend/routers/ backend/utils/ backend/services/ --include="*.py" | grep -v "traceback.print"

# traceback.print_exc() usage
grep -rn "traceback.print_exc" backend/ --include="*.py"

# Unprotected endpoints (missing require_permission or get_current_user)
grep -rn "@router\.\(get\|post\|put\|delete\)" backend/routers/ --include="*.py" | grep -v "Depends"
```

### 4. Verify rate limiting

```bash
# Test login rate limiting (should block after 5 attempts)
for i in $(seq 1 6); do
  curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test&password=wrong"
  echo " attempt $i"
done
```

### 5. Verify tenant isolation

```bash
# Check that get_db_connection routes correctly
grep -rn "get_db_connection\|get_tenant_db" backend/routers/ --include="*.py" | head -20

# Check validate_aman_identifier usage
grep -rn "validate_aman_identifier" backend/ --include="*.py"
```

## Key Files to Modify

| Priority | File | Fix |
|----------|------|-----|
| 🔴 P1 | `backend/routers/purchases.py` | Replace 20+ `detail=str(e)` with generic messages |
| 🔴 P1 | `backend/routers/services.py` | Replace 10+ `detail=str(e)` with generic messages |
| 🔴 P1 | `backend/routers/sso.py` | Fix SAML RelayState to use server-side state |
| 🟡 P2 | `backend/routers/security.py` | Remove try-except around audit logging; fix token invalidation |
| 🟡 P2 | `backend/routers/auth.py` | Replace `traceback.print_exc()` with `logger.exception()` |
| 🟡 P2 | `backend/utils/permissions.py` | Complete field-level restriction matrix |
| 🟢 P3 | `backend/routers/mobile.py` | Add rate limiting to sync endpoint |
| 🟢 P3 | `backend/utils/security_middleware.py` | Document CSP `unsafe-inline` limitation |

## Verifying Fixes

After applying fixes, re-run the grep checks from step 3 — all should return zero results.

```bash
# Should return 0 results after fix
grep -rn "detail=str(e)" backend/routers/ --include="*.py" | wc -l

# Should return 0 results
grep -rn "traceback.print_exc" backend/routers/ --include="*.py" | wc -l
```
