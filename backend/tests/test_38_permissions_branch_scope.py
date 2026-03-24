import pytest
from fastapi import HTTPException

from utils.permissions import validate_branch_access


def test_superuser_can_access_any_branch_or_all():
    user = {
        "role": "superuser",
        "permissions": ["*"],
        "allowed_branches": [1],
    }
    assert validate_branch_access(user, None) is None
    assert validate_branch_access(user, "999") == 999


def test_restricted_user_must_provide_branch_if_multiple_allowed():
    user = {
        "role": "user",
        "permissions": ["sales.view"],
        "allowed_branches": [1, 2],
    }
    with pytest.raises(HTTPException) as exc:
        validate_branch_access(user, None)
    assert exc.value.status_code == 403


def test_restricted_user_auto_selects_single_branch():
    user = {
        "role": "user",
        "permissions": ["sales.view"],
        "allowed_branches": [7],
    }
    assert validate_branch_access(user, None) == 7


def test_restricted_user_blocked_from_other_branch():
    user = {
        "role": "user",
        "permissions": ["sales.view"],
        "allowed_branches": [1, 2],
    }
    with pytest.raises(HTTPException) as exc:
        validate_branch_access(user, 3)
    assert exc.value.status_code == 403


def test_invalid_branch_id_returns_400():
    user = {
        "role": "user",
        "permissions": ["sales.view"],
        "allowed_branches": [1],
    }
    with pytest.raises(HTTPException) as exc:
        validate_branch_access(user, "abc")
    assert exc.value.status_code == 400
