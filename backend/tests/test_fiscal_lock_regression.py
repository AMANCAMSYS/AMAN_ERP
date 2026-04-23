"""Fiscal period lock regression tests.

Ensures ``utils.fiscal_lock.check_fiscal_period_open`` actually blocks writes
when a period is locked and allows them when it is not. Guards against the
previous silent-pass bug and protects every GL-posting path that relies on
this gate (payroll, EOS, loans, projects, tax, zakat, governance endpoints).
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from utils.fiscal_lock import check_fiscal_period_open


@pytest.fixture()
def _fiscal_lock_row(db_connection):
    """Create a locked period covering a known date range, then remove it."""
    start = date(1990, 1, 1)
    end = date(1990, 12, 31)

    db_connection.execute(
        text(
            """
            INSERT INTO fiscal_period_locks
                (period_name, period_start, period_end, is_locked, locked_at, locked_by)
            VALUES (:n, :s, :e, TRUE, CURRENT_TIMESTAMP, 1)
            RETURNING id
            """
        ),
        {"n": "REGRESSION-LOCK", "s": start, "e": end},
    )
    db_connection.commit()
    try:
        yield (start, end)
    finally:
        db_connection.execute(
            text("DELETE FROM fiscal_period_locks WHERE period_name = :n"),
            {"n": "REGRESSION-LOCK"},
        )
        db_connection.commit()


class TestFiscalLockRegression:
    def test_locked_period_raises(self, db_connection, _fiscal_lock_row):
        start, _ = _fiscal_lock_row
        with pytest.raises(HTTPException) as exc:
            check_fiscal_period_open(db_connection, start)
        assert exc.value.status_code == 400

    def test_locked_period_soft_returns_false(self, db_connection, _fiscal_lock_row):
        start, _ = _fiscal_lock_row
        assert check_fiscal_period_open(db_connection, start, raise_error=False) is False

    def test_open_period_returns_true(self, db_connection, _fiscal_lock_row):
        _, end = _fiscal_lock_row
        # A date outside the locked window must be allowed.
        future = end + timedelta(days=365)
        assert check_fiscal_period_open(db_connection, future) is True

    def test_string_date_accepted(self, db_connection, _fiscal_lock_row):
        start, _ = _fiscal_lock_row
        with pytest.raises(HTTPException):
            check_fiscal_period_open(db_connection, start.isoformat())
