"""E-invoice outbox relay smoke test.

Inserts a pending row into ``einvoice_outbox`` and triggers the relay
endpoint to confirm the worker picks the row up and either marks it
processed or moves it to the give-up bucket on a non-retriable failure.
"""
from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import text


def _outbox_table_exists(db_connection) -> bool:
    return bool(
        db_connection.execute(
            text("SELECT to_regclass('public.einvoice_outbox')")
        ).scalar()
    )


@pytest.fixture()
def pending_outbox_row(db_connection):
    if not _outbox_table_exists(db_connection):
        pytest.skip("einvoice_outbox table not present in this tenant")

    nonce = str(uuid.uuid4())
    payload = {
        "invoice_id": -1,
        "uuid": nonce,
        "smoke_test": True,
        "lines": [],
    }
    row = db_connection.execute(
        text(
            """
            INSERT INTO einvoice_outbox
                (event_type, payload, status, attempts, created_at)
            VALUES ('invoice.test', CAST(:p AS JSONB), 'pending', 0, NOW())
            RETURNING id
            """
        ),
        {"p": json.dumps(payload)},
    ).scalar()
    db_connection.commit()
    try:
        yield row
    finally:
        db_connection.execute(
            text("DELETE FROM einvoice_outbox WHERE id = :id"),
            {"id": row},
        )
        db_connection.commit()


def test_outbox_relay_processes_or_gives_up(client, admin_headers, db_connection, pending_outbox_row):
    """Triggering the relay must move the test row out of ``pending``.

    A real call to the e-invoice integration is not expected to succeed in
    the test environment (no live ZATCA/Aman gateway), so the row may end
    up as ``failed`` or ``giveup``; the only assertion is that it is no
    longer ``pending`` after the relay handler runs.
    """
    resp = client.post(
        "/api/finance/accounting-depth/einvoice/outbox/relay",
        headers=admin_headers,
        json={"limit": 5},
    )
    if resp.status_code == 404:
        pytest.skip("Outbox relay endpoint not exposed on this build")
    assert resp.status_code in (200, 202), resp.text

    status = db_connection.execute(
        text("SELECT status FROM einvoice_outbox WHERE id = :id"),
        {"id": pending_outbox_row},
    ).scalar()
    assert status is not None
    assert status != "pending", f"relay did not pick up the row; status={status}"
