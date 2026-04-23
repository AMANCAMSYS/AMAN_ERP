"""Negative-path test for ``require_permission`` dependency.

Creates an ad-hoc user with a non-admin role that has no permissions at all
and verifies that a permission-protected governance endpoint returns 403.

Guards against accidental "open by default" regressions in the dependency
chain wired up via ``utils.permissions.require_permission``.
"""
from __future__ import annotations

import secrets

import pytest
from sqlalchemy import text


PROTECTED_ENDPOINT = "/api/governance/overtime-rates"


@pytest.fixture()
def bare_user(db_connection):
    """Create a temporary user whose role has zero permissions and yield credentials."""
    suffix = secrets.token_hex(4)
    username = f"perm_neg_{suffix}"
    password = "Perm-Neg-Test-2026!"

    role_row = db_connection.execute(
        text(
            """
            INSERT INTO roles (name, description, permissions, is_system)
            VALUES (:n, 'negative-path test role', CAST('[]' AS JSONB), FALSE)
            ON CONFLICT (name) DO UPDATE SET permissions = CAST('[]' AS JSONB)
            RETURNING id
            """
        ),
        {"n": f"role_neg_{suffix}"},
    ).fetchone()
    role_id = role_row[0]

    # Hash via the same path the API uses to keep the test honest.
    from utils.security import hash_password

    db_connection.execute(
        text(
            """
            INSERT INTO users (username, password_hash, role_id, role, is_active, is_superuser)
            VALUES (:u, :p, :rid, 'user', TRUE, FALSE)
            """
        ),
        {"u": username, "p": hash_password(password), "rid": role_id},
    )
    db_connection.commit()
    try:
        yield username, password
    finally:
        db_connection.execute(text("DELETE FROM users WHERE username = :u"), {"u": username})
        db_connection.execute(text("DELETE FROM roles WHERE id = :r"), {"r": role_id})
        db_connection.commit()


def test_bare_role_is_denied(client, bare_user, company_info):
    username, password = bare_user
    company_code = company_info.get("company_id") or company_info.get("company_code")
    resp = client.post(
        "/api/auth/login",
        data={
            "username": username,
            "password": password,
            "grant_type": "password",
            "company_code": company_code,
        },
    )
    if resp.status_code != 200:
        pytest.skip(f"could not log in as bare user: {resp.status_code} {resp.text}")
    token = resp.json()["access_token"]

    r = client.get(PROTECTED_ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403, (
        f"bare role unexpectedly allowed at {PROTECTED_ENDPOINT}: "
        f"status={r.status_code} body={r.text[:200]}"
    )


def test_no_token_is_denied(client):
    r = client.get(PROTECTED_ENDPOINT)
    assert r.status_code in (401, 403), f"unauthenticated request not denied: {r.status_code}"
