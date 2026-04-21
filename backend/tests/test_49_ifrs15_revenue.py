"""Unit tests for TASK-036 IFRS 15 revenue-recognition engine math.

Uses an in-memory SQLite-style stub so the engine's arithmetic is exercised
without needing a live database.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from services import ifrs15_revenue_service as rev


class _FakeResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def scalar(self):
        r = self.fetchone()
        return r.id if r and hasattr(r, "id") else None


class _Row:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _FakeDB:
    def __init__(self):
        self.contracts = {}
        self.pos = {}
        self._next_contract = 1
        self._next_po = 1

    def commit(self):
        pass

    def execute(self, stmt, params=None):
        sql = str(stmt).strip().lower()
        params = params or {}
        if sql.startswith("insert into revenue_contracts"):
            cid = self._next_contract
            self._next_contract += 1
            self.contracts[cid] = dict(params, id=cid,
                                       total_transaction_price=params["tp"])
            return _FakeResult([_Row(id=cid)])
        if sql.startswith("insert into performance_obligations"):
            pid = self._next_po
            self._next_po += 1
            self.pos[pid] = _Row(
                id=pid,
                contract_id=params["cid"],
                description=params["desc"],
                standalone_selling_price=params["ssp"],
                recognition_method=params["rm"],
                allocated_price=Decimal("0"),
                satisfied_pct=Decimal("0"),
                revenue_recognized=Decimal("0"),
            )
            return _FakeResult([_Row(id=pid)])
        if "select total_transaction_price from revenue_contracts" in sql:
            c = self.contracts[params["id"]]
            return _FakeResult([_Row(total_transaction_price=c["total_transaction_price"])])
        if "select id, standalone_selling_price from performance_obligations" in sql:
            rows = [p for p in self.pos.values() if p.contract_id == params["cid"]]
            return _FakeResult(sorted(rows, key=lambda r: r.id))
        if sql.startswith("update performance_obligations set allocated_price"):
            self.pos[params["id"]].allocated_price = Decimal(params["a"])
            return _FakeResult([])
        if ("select id, contract_id, description, allocated_price" in sql
                and "performance_obligations" in sql):
            p = self.pos[params["id"]]
            return _FakeResult([p])
        if sql.startswith("update performance_obligations"):
            p = self.pos[params["id"]]
            p.satisfied_pct = Decimal(params["pct"])
            p.revenue_recognized = Decimal(params["rev"])
            return _FakeResult([])
        return _FakeResult([])


def test_allocate_transaction_price_relative_ssp():
    db = _FakeDB()
    cid = rev.create_contract(
        db, "C-001", customer_id=1, total_transaction_price=Decimal("1000"),
        obligations=[
            {"description": "license", "standalone_selling_price": Decimal("800"),
             "recognition_method": "point_in_time"},
            {"description": "support", "standalone_selling_price": Decimal("400"),
             "recognition_method": "over_time"},
        ],
    )
    assert cid == 1
    pos = sorted(db.pos.values(), key=lambda p: p.id)
    # 1000 allocated on SSP 800:400 → 666.67 and 333.33; rounding absorbed in last.
    assert pos[0].allocated_price == Decimal("666.67")
    assert pos[1].allocated_price == Decimal("333.33")
    assert sum(p.allocated_price for p in pos) == Decimal("1000.00")


def test_recognise_point_in_time_flips_to_full():
    db = _FakeDB()
    rev.create_contract(
        db, "C-002", customer_id=1, total_transaction_price=Decimal("500"),
        obligations=[{"description": "device", "standalone_selling_price": Decimal("500"),
                      "recognition_method": "point_in_time"}],
    )
    po_id = list(db.pos.keys())[0]
    out = rev.recognise_revenue(db, po_id=po_id)
    assert out["satisfied_pct"] == "1"
    assert out["recognised_now"] == "500.00"
    # idempotent second call
    out2 = rev.recognise_revenue(db, po_id=po_id)
    assert out2["recognised_now"] == "0.00"


def test_recognise_over_time_delta():
    db = _FakeDB()
    rev.create_contract(
        db, "C-003", customer_id=1, total_transaction_price=Decimal("1200"),
        obligations=[{"description": "service", "standalone_selling_price": Decimal("1200"),
                      "recognition_method": "over_time"}],
    )
    po_id = list(db.pos.keys())[0]
    out1 = rev.recognise_revenue(db, po_id=po_id, new_satisfied_pct=Decimal("0.25"))
    assert out1["recognised_now"] == "300.00"
    out2 = rev.recognise_revenue(db, po_id=po_id, new_satisfied_pct=Decimal("0.75"))
    assert out2["recognised_now"] == "600.00"
    assert out2["total_recognised"] == "900.00"


def test_over_time_requires_satisfied_pct():
    db = _FakeDB()
    rev.create_contract(
        db, "C-004", customer_id=1, total_transaction_price=Decimal("100"),
        obligations=[{"description": "sv", "standalone_selling_price": Decimal("100"),
                      "recognition_method": "over_time"}],
    )
    po_id = list(db.pos.keys())[0]
    with pytest.raises(ValueError):
        rev.recognise_revenue(db, po_id=po_id)


def test_post_journal_requires_accounts():
    db = _FakeDB()
    rev.create_contract(
        db, "C-005", customer_id=1, total_transaction_price=Decimal("100"),
        obligations=[{"description": "x", "standalone_selling_price": Decimal("100"),
                      "recognition_method": "point_in_time"}],
    )
    po_id = list(db.pos.keys())[0]
    with pytest.raises(ValueError):
        rev.recognise_revenue(db, po_id=po_id, post_journal=True)
