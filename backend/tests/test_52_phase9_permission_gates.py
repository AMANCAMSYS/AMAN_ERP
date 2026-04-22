"""
Phase 10 · Regression tests for Phase 9 permission gates.

Verifies the 6 endpoints hardened in Phase 9 (commit 14783fd) now:
  (a) return 401 when called without Authorization header; and
  (b) respond successfully (not 500, not 403) for the admin/superuser token
      produced by conftest.admin_headers — i.e. the dependency chain
      `require_permission(...)` is correctly wired and does not break
      legitimate access.

Endpoints under test (all via prefix /api):
  GET  /api/dashboard/industry-widgets      dashboard.view
  GET  /api/dashboard/gl-rules              accounting.view
  GET  /api/dashboard/coa-summary           accounting.view
  GET  /api/data-import/entity-types        data_import.view
  GET  /api/data-import/template/customer   data_import.view
  GET  /api/external/webhooks/events        settings.view|admin
"""
import pytest


PHASE9_GATED_ENDPOINTS = [
    ("/api/dashboard/industry-widgets",        "dashboard.view"),
    ("/api/dashboard/gl-rules",                "accounting.view"),
    ("/api/dashboard/coa-summary",             "accounting.view"),
    ("/api/data-import/entity-types",          "data_import.view"),
    ("/api/data-import/template/customer",     "data_import.view"),
    ("/api/external/webhooks/events",          "settings.view|admin"),
]


@pytest.mark.parametrize("path,perm", PHASE9_GATED_ENDPOINTS)
def test_phase9_gate_requires_auth(client, path, perm):
    """Unauthenticated request must be rejected (401/403), never leak data."""
    resp = client.get(path)
    assert resp.status_code in (401, 403), (
        f"{path} expected 401/403 without auth, got {resp.status_code} "
        f"(perm={perm}) — gate may be missing."
    )


@pytest.mark.parametrize("path,perm", PHASE9_GATED_ENDPOINTS)
def test_phase9_gate_allows_admin(client, admin_headers, path, perm):
    """Admin/superuser must pass the gate (not 401/403/500)."""
    resp = client.get(path, headers=admin_headers)
    assert resp.status_code not in (401, 403, 500), (
        f"{path} failed for admin: status={resp.status_code} "
        f"(perm={perm}) — gate too strict or wiring broken. "
        f"Body: {resp.text[:200]}"
    )
