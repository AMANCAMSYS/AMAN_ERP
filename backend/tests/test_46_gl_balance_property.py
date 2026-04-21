"""
TASK-032 — Property-based tests for journal-entry balance invariants.

Targets `services.gl_service.validate_je_lines` (the pure validation surface
extracted from `create_journal_entry` specifically for hypothesis testing).

Invariants under test:
  1. Any randomly generated BALANCED, NON-NEGATIVE, SINGLE-SIDED set of lines is
     accepted and the returned totals satisfy |Σdr − Σcr| ≤ 0.01.
  2. Any UNBALANCED set (difference > 0.01) is rejected with HTTP 400.
  3. Any line with both debit and credit > 0 is rejected.
  4. Any negative amount is rejected.
  5. An empty list and an all-zero set are rejected.
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal

import pytest
from fastapi import HTTPException
from hypothesis import given, settings, strategies as st

# Make the backend package importable when running pytest from repo root.
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from services.gl_service import validate_je_lines  # noqa: E402


_D2 = Decimal("0.01")

# Decimal amounts within a reasonable accounting range, quantized to 2 dp.
amount_strategy = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("1000000.00"),
    allow_nan=False,
    allow_infinity=False,
    places=2,
)


@st.composite
def balanced_entry(draw):
    """Generate a balanced pair of debit/credit line sets with equal totals."""
    n_debits = draw(st.integers(min_value=1, max_value=6))
    n_credits = draw(st.integers(min_value=1, max_value=6))
    debits = [draw(amount_strategy) for _ in range(n_debits)]
    total = sum(debits)
    # Split `total` into n_credits positive pieces, each >= 0.01.
    # Ensure total >= n_credits * 0.01 by inflating debits if too small.
    min_required = Decimal("0.01") * n_credits
    if total < min_required:
        bump = (min_required - total).quantize(_D2)
        debits[0] = (debits[0] + bump).quantize(_D2)
        total = sum(debits)

    remaining = total
    credits: list[Decimal] = []
    for i in range(n_credits - 1):
        slots_left = n_credits - 1 - i  # credits after this one (excluding last)
        max_share = (remaining - Decimal("0.01") * (slots_left + 1)).quantize(_D2)
        # slots_left+1 because we still need ≥0.01 for each remaining slot INCLUDING the final one.
        if max_share < Decimal("0.01"):
            share = Decimal("0.01")
        else:
            share = draw(
                st.decimals(
                    min_value=Decimal("0.01"),
                    max_value=max_share,
                    allow_nan=False,
                    allow_infinity=False,
                    places=2,
                )
            )
        credits.append(share)
        remaining -= share
    credits.append(remaining.quantize(_D2))
    assert all(c > 0 for c in credits), f"non-positive credit slice: {credits}"

    lines = [{"account_id": i + 1, "debit": d, "credit": 0} for i, d in enumerate(debits)]
    lines += [
        {"account_id": 100 + i, "debit": 0, "credit": c}
        for i, c in enumerate(credits)
    ]
    return lines, total


@given(balanced_entry())
@settings(max_examples=200, deadline=None)
def test_balanced_entries_are_accepted(entry):
    lines, expected_total = entry
    total_debit, total_credit = validate_je_lines(lines)
    assert abs(total_debit - total_credit) <= _D2, (
        f"validator returned unbalanced totals: dr={total_debit} cr={total_credit}"
    )
    # Totals should equal (within 0.01) the requested balanced amount.
    assert abs(total_debit - expected_total) <= _D2
    assert abs(total_credit - expected_total) <= _D2


@given(
    debit=amount_strategy,
    credit=amount_strategy,
    delta=st.decimals(
        min_value=Decimal("0.02"),
        max_value=Decimal("9999.99"),
        allow_nan=False,
        allow_infinity=False,
        places=2,
    ),
)
@settings(max_examples=100, deadline=None)
def test_unbalanced_entries_are_rejected(debit, credit, delta):
    # Force imbalance strictly greater than the 0.01 tolerance.
    lines = [
        {"account_id": 1, "debit": debit, "credit": 0},
        {"account_id": 2, "debit": 0, "credit": debit + delta},
    ]
    with pytest.raises(HTTPException) as exc:
        validate_je_lines(lines)
    assert exc.value.status_code == 400


@given(d=amount_strategy, c=amount_strategy)
@settings(max_examples=50, deadline=None)
def test_mixed_side_line_rejected(d, c):
    lines = [{"account_id": 1, "debit": d, "credit": c}]
    with pytest.raises(HTTPException) as exc:
        validate_je_lines(lines)
    assert exc.value.status_code == 400


@given(
    amount=st.decimals(
        min_value=Decimal("-1000000.00"),
        max_value=Decimal("-0.01"),
        allow_nan=False,
        allow_infinity=False,
        places=2,
    )
)
@settings(max_examples=30, deadline=None)
def test_negative_amount_rejected(amount):
    lines = [
        {"account_id": 1, "debit": amount, "credit": 0},
        {"account_id": 2, "debit": 0, "credit": abs(amount)},
    ]
    with pytest.raises(HTTPException) as exc:
        validate_je_lines(lines)
    assert exc.value.status_code == 400


def test_empty_lines_rejected():
    with pytest.raises(HTTPException) as exc:
        validate_je_lines([])
    assert exc.value.status_code == 400


def test_all_zero_rejected():
    lines = [
        {"account_id": 1, "debit": 0, "credit": 0},
        {"account_id": 2, "debit": 0, "credit": 0},
    ]
    with pytest.raises(HTTPException) as exc:
        validate_je_lines(lines)
    assert exc.value.status_code == 400


def test_within_tolerance_accepted():
    # |dr - cr| == 0.01 is accepted (boundary case per `> _D2`).
    lines = [
        {"account_id": 1, "debit": Decimal("100.00"), "credit": 0},
        {"account_id": 2, "debit": 0, "credit": Decimal("100.01")},
    ]
    total_debit, total_credit = validate_je_lines(lines)
    assert abs(total_debit - total_credit) == _D2
