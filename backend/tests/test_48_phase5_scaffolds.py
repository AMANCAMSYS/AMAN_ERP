"""Phase 5 smoke tests — scaffolds must import and behave for dry-run paths."""

from __future__ import annotations

from decimal import Decimal

import pytest


def test_einvoice_registry_resolves_known_jurisdictions():
    from integrations.einvoicing import get_adapter
    eg = get_adapter("EG")
    ae = get_adapter("AE")
    assert eg.jurisdiction == "EG"
    assert ae.jurisdiction == "AE"


def test_einvoice_registry_rejects_unknown():
    from integrations.einvoicing import get_adapter
    with pytest.raises(ValueError):
        get_adapter("XX")


def test_eta_adapter_dry_run_roundtrip():
    from integrations.einvoicing import EgyptETAAdapter
    adapter = EgyptETAAdapter(dry_run=True)
    result = adapter.submit({"id": 42})
    assert result.status == "submitted"
    assert result.document_uuid and result.document_uuid.startswith("dryrun-eta-")
    follow = adapter.fetch_status(result.document_uuid)
    assert follow.status == "accepted"


def test_uae_adapter_dry_run_roundtrip():
    from integrations.einvoicing import UAEFTAAdapter
    adapter = UAEFTAAdapter(dry_run=True)
    result = adapter.submit({"id": 1})
    assert result.status == "submitted"
    assert result.document_uuid.startswith("dryrun-ae-")


def test_impairment_service_pure_math(monkeypatch):
    """Impairment math: loss = carrying - max(viu, fvlcs) when positive."""
    from services import impairment_service

    class _Stub:
        def __init__(self):
            self.committed = False

        def execute(self, *a, **kw):
            class _R:
                def scalar(self_inner):
                    return 1
            return _R()

        def commit(self):
            self.committed = True

    db = _Stub()
    out = impairment_service.record_impairment_test(
        db,
        cgu_id=1,
        carrying_amount=Decimal("1000"),
        value_in_use=Decimal("700"),
        fair_value_less_costs=Decimal("750"),
    )
    assert out["recoverable_amount"] == "750"
    assert out["impairment_loss"] == "250.00"
    assert db.committed is True


def test_ecl_service_importable():
    """Module must import without hitting the DB."""
    from services import ecl_service
    assert hasattr(ecl_service, "compute_ecl_provision")


def test_nrv_service_importable():
    from services import nrv_service
    assert hasattr(nrv_service, "run_nrv_test")
