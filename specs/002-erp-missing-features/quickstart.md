# Quickstart: AMAN ERP — 18 Missing Features

**Branch**: `002-erp-missing-features` | **Date**: 2026-04-02

## Prerequisites

- Python 3.11+, Node.js 18+, PostgreSQL 15, Redis
- Docker + Docker Compose (for full stack)
- React Native CLI + Xcode/Android Studio (for mobile app)
- Existing AMAN ERP running locally (`docker compose up`)

## Implementation Order

Features must be implemented in this order due to dependencies:

```
Phase 1 (Tier 1 — Weeks 1-12):
  1. Unified Notification Service (cross-cutting, needed by 6+ features)
  2. SSO/LDAP Integration
  3. FIFO/LIFO Cost Layers
  4. 3-Way Matching
  5. Intercompany Accounting

Phase 2 (Tier 2 — Weeks 13-32):
  6. Employee Self-Service
  7. Subscription Billing
  8. Cash Flow Forecasting
  9. BI Dashboard Integration
  10. Mobile App (longest lead time — can start in parallel from Week 16)

Phase 3 (Tier 3 — Weeks 33-52):
  11. Blanket Purchase Orders
  12. Routing/Operations
  13. Shop Floor Control (depends on Routing)
  14. Time Tracking
  15. Resource Planning (depends on Time Tracking)
  16. Performance Reviews
  17. Demand Forecasting
  18. CPQ
  19. Campaign Management
```

## Adding a New Feature (Pattern)

Each feature follows this standard pattern:

### 1. Models (Alembic migration)

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "add_feature_name_tables"
# Apply to all tenants
alembic -x company=all upgrade head
```

Add models to the appropriate domain file in `backend/models/domains/`.

### 2. Schemas (Pydantic)

Create `backend/schemas/feature_name.py` with request/response models:
- All monetary fields: `Decimal` with `max_digits=18, decimal_places=4`
- All IDs: `int`
- All dates: `date` or `datetime`
- Enum fields: use `Literal[...]` or `Enum`

### 3. Service (Business Logic)

Create `backend/services/feature_service.py`:
- All journal entries through `gl_service.py`
- All monetary math with `Decimal` + `ROUND_HALF_UP`
- All notifications through `notification_service.py`
- All DB access through `get_db_connection(company_id)`

### 4. Router (API Endpoints)

Create `backend/routers/module/feature.py`:
- Every endpoint: `@require_permission("module.action")`
- Response format: `{"success": True, "data": ...}`
- Validation errors: 422 with structured details

### 5. Frontend Pages

Create `frontend/src/pages/FeatureName/`:
- List pages: use `DataTable` + `SearchFilter`
- Form pages: use `FormField`
- Both `en.json` and `ar.json` translations
- RTL layout support

### 6. Tests

Create `backend/tests/test_feature.py`:
- Test permission boundaries
- Test Decimal precision (no float drift)
- Test multi-tenant isolation
- Test GL service integration (if financial)
- Test edge cases from spec

## Key Files to Reference

| Purpose | File |
|---------|------|
| GL service (journal entries) | `backend/services/gl_service.py` |
| Costing service (WAC, extend for FIFO/LIFO) | `backend/services/costing_service.py` |
| Auth router (extend for SSO) | `backend/routers/auth.py` |
| Database connection | `backend/database.py` |
| Scheduler (recurring jobs) | `backend/services/scheduler.py` |
| Email service | `backend/services/email_service.py` |
| DataTable component | `frontend/src/components/DataTable.jsx` |
| FormField component | `frontend/src/components/FormField.jsx` |
| API client | `frontend/src/services/apiClient.js` |
| Constitution (rules) | `.specify/memory/constitution.md` |

## Environment Variables (New)

```env
# SSO/LDAP
SSO_SAML_ENTITY_ID=aman-erp
SSO_SAML_ACS_URL=https://erp.example.com/api/auth/sso/saml/acs

# Mobile Push Notifications
FCM_SERVER_KEY=<firebase-cloud-messaging-key>

# Campaign Email/SMS (external provider)
SMTP_CAMPAIGN_HOST=<smtp-host>
SMTP_CAMPAIGN_PORT=587
SMS_PROVIDER_API_KEY=<sms-api-key>
SMS_PROVIDER_URL=<sms-api-url>

# BI Dashboard
DASHBOARD_REFRESH_INTERVAL=15  # minutes
```

## Verification Checklist (per feature)

- [ ] Alembic migration created and applied
- [ ] Pydantic schemas with Decimal for money
- [ ] All endpoints have permission decorators
- [ ] GL entries route through gl_service.py
- [ ] Notifications route through notification_service.py
- [ ] Tests pass (permissions, Decimal, isolation, edge cases)
- [ ] AR + EN translations added
- [ ] RTL layout verified
- [ ] Multi-tenant tested (2+ companies)
