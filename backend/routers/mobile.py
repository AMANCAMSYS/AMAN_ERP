"""
AMAN ERP — Mobile API Router
Endpoints for mobile sync, dashboard, and device registration.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from database import get_db_connection
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["Mobile"])


# ---------------------------------------------------------------------------
# Schemas (inline — small surface, keep co-located)
# ---------------------------------------------------------------------------

class SyncItem(BaseModel):
    entity_type: str = Field(..., max_length=50)
    entity_id: Optional[int] = None
    operation: str = Field(..., pattern=r"^(create|update)$")
    payload: dict = Field(default_factory=dict)
    device_timestamp: datetime


class SyncBatchRequest(BaseModel):
    device_id: str = Field(..., max_length=255)
    items: List[SyncItem]


class SyncResultItem(BaseModel):
    index: int
    status: str  # synced | conflict | error
    entity_id: Optional[int] = None
    message: Optional[str] = None
    server_version: Optional[dict] = None


class SyncBatchResponse(BaseModel):
    synced: int
    conflicts: int
    errors: int
    results: List[SyncResultItem]


class SyncStatusResponse(BaseModel):
    device_id: str
    pending: int
    conflicts: int
    last_sync: Optional[datetime] = None


class ConflictResolveRequest(BaseModel):
    sync_queue_id: int
    resolution: str = Field(..., pattern=r"^(keep_server|keep_device|merge)$")
    merged_payload: Optional[dict] = None


class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(..., max_length=255)
    platform: str = Field(..., pattern=r"^(ios|android)$")
    fcm_token: str = Field(..., max_length=500)


class DashboardResponse(BaseModel):
    inventory_summary: dict
    pending_orders: int
    pending_approvals: int
    recent_quotations: list
    currency_code: str
    currency_symbol: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_company_id(current_user) -> str:
    cid = getattr(current_user, "company_id", None)
    if not cid:
        raise HTTPException(status_code=400, detail="company_id not available")
    return cid


# ---------------------------------------------------------------------------
# POST /mobile/sync  — Batch sync offline changes
# ---------------------------------------------------------------------------

@router.post("/sync", response_model=SyncBatchResponse)
async def batch_sync(
    body: SyncBatchRequest,
    current_user=Depends(get_current_user),
):
    """Sync a batch of offline changes from mobile device."""
    company_id = _get_company_id(current_user)
    user_id = current_user.id
    now = datetime.now(timezone.utc)

    synced = 0
    conflicts = 0
    errors = 0
    results: list[SyncResultItem] = []

    conn = get_db_connection(company_id)
    try:
        with conn.begin():
            for idx, item in enumerate(body.items):
                try:
                    # Conflict detection: check if entity was modified after device_timestamp
                    conflict_detected = False
                    server_version = None

                    if item.operation == "update" and item.entity_id:
                        conflict_detected, server_version = _check_conflict(
                            conn, item.entity_type, item.entity_id, item.device_timestamp
                        )

                    if conflict_detected:
                        # Store in sync_queue as conflict
                        conn.execute(text("""
                            INSERT INTO sync_queue
                                (device_id, user_id, entity_type, entity_id, operation,
                                 payload, device_timestamp, server_timestamp, sync_status,
                                 conflict_resolution, created_at, updated_at)
                            VALUES
                                (:device_id, :user_id, :entity_type, :entity_id, :operation,
                                 :payload::jsonb, :device_ts, :now, 'conflict',
                                 :server_ver::jsonb, :now, :now)
                        """), {
                            "device_id": body.device_id, "user_id": user_id,
                            "entity_type": item.entity_type, "entity_id": item.entity_id,
                            "operation": item.operation,
                            "payload": _json_dumps(item.payload),
                            "device_ts": item.device_timestamp,
                            "now": now,
                            "server_ver": _json_dumps({"server": server_version, "device": item.payload}),
                        })
                        conflicts += 1
                        results.append(SyncResultItem(
                            index=idx, status="conflict",
                            entity_id=item.entity_id,
                            server_version=server_version,
                            message="Entity modified on server since device timestamp",
                        ))
                    else:
                        # Apply the change
                        applied_id = _apply_sync_item(conn, item, user_id)
                        # Record in sync_queue as synced
                        conn.execute(text("""
                            INSERT INTO sync_queue
                                (device_id, user_id, entity_type, entity_id, operation,
                                 payload, device_timestamp, server_timestamp, sync_status,
                                 created_at, updated_at)
                            VALUES
                                (:device_id, :user_id, :entity_type, :entity_id, :operation,
                                 :payload::jsonb, :device_ts, :now, 'synced', :now, :now)
                        """), {
                            "device_id": body.device_id, "user_id": user_id,
                            "entity_type": item.entity_type,
                            "entity_id": applied_id or item.entity_id,
                            "operation": item.operation,
                            "payload": _json_dumps(item.payload),
                            "device_ts": item.device_timestamp, "now": now,
                        })
                        synced += 1
                        results.append(SyncResultItem(
                            index=idx, status="synced", entity_id=applied_id or item.entity_id,
                        ))
                except Exception as exc:
                    logger.warning("Sync item %d failed: %s", idx, exc)
                    errors += 1
                    results.append(SyncResultItem(
                        index=idx, status="error", message=str(exc)[:200],
                    ))
    finally:
        conn.close()

    return SyncBatchResponse(synced=synced, conflicts=conflicts, errors=errors, results=results)


# ---------------------------------------------------------------------------
# GET /mobile/sync/status  — get sync status for device
# ---------------------------------------------------------------------------

@router.get("/sync/status", response_model=SyncStatusResponse)
async def sync_status(
    device_id: str,
    current_user=Depends(get_current_user),
):
    company_id = _get_company_id(current_user)
    conn = get_db_connection(company_id)
    try:
        row = conn.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE sync_status = 'pending')  AS pending,
                COUNT(*) FILTER (WHERE sync_status = 'conflict') AS conflicts,
                MAX(server_timestamp) AS last_sync
            FROM sync_queue
            WHERE device_id = :did AND user_id = :uid
        """), {"did": device_id, "uid": current_user.id}).mappings().first()
    finally:
        conn.close()

    return SyncStatusResponse(
        device_id=device_id,
        pending=row["pending"] if row else 0,
        conflicts=row["conflicts"] if row else 0,
        last_sync=row["last_sync"] if row else None,
    )


# ---------------------------------------------------------------------------
# POST /mobile/sync/resolve  — resolve a sync conflict
# ---------------------------------------------------------------------------

@router.post("/sync/resolve")
async def resolve_conflict(
    body: ConflictResolveRequest,
    current_user=Depends(get_current_user),
):
    company_id = _get_company_id(current_user)
    conn = get_db_connection(company_id)
    try:
        with conn.begin():
            row = conn.execute(text("""
                SELECT id, entity_type, entity_id, payload, conflict_resolution, sync_status
                FROM sync_queue WHERE id = :sid AND user_id = :uid
            """), {"sid": body.sync_queue_id, "uid": current_user.id}).mappings().first()

            if not row:
                raise HTTPException(404, "Sync queue item not found")
            if row["sync_status"] != "conflict":
                raise HTTPException(400, "Item is not in conflict status")

            if body.resolution == "keep_server":
                # Just mark as resolved — server version already in DB
                pass
            elif body.resolution == "keep_device":
                # Apply device payload
                import json
                payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
                _apply_sync_item_raw(conn, row["entity_type"], row["entity_id"], payload, current_user.id)
            elif body.resolution == "merge":
                if not body.merged_payload:
                    raise HTTPException(400, "merged_payload required for merge resolution")
                _apply_sync_item_raw(conn, row["entity_type"], row["entity_id"], body.merged_payload, current_user.id)

            conn.execute(text("""
                UPDATE sync_queue
                SET sync_status = 'resolved',
                    conflict_resolution = jsonb_set(
                        COALESCE(conflict_resolution, '{}'),
                        '{resolution}',
                        :res::jsonb
                    ),
                    updated_at = now()
                WHERE id = :sid
            """), {"sid": body.sync_queue_id, "res": f'"{body.resolution}"'})
    finally:
        conn.close()

    return {"status": "resolved", "resolution": body.resolution}


# ---------------------------------------------------------------------------
# GET /mobile/dashboard  — aggregated dashboard for mobile
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=DashboardResponse)
async def mobile_dashboard(current_user=Depends(get_current_user)):
    company_id = _get_company_id(current_user)
    conn = get_db_connection(company_id)
    try:
        # Company currency settings
        currency_row = conn.execute(text("""
            SELECT setting_value
            FROM company_settings
            WHERE setting_key = 'default_currency'
            ORDER BY id DESC
            LIMIT 1
        """)).mappings().first()
        currency_code = (
            (currency_row["setting_value"] if currency_row else None)
            or "SAR"
        )
        currency_code = str(currency_code).upper()
        currency_symbol = {
            "SAR": "ر.س",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "AED": "د.إ",
            "KWD": "د.ك",
            "QAR": "ر.ق",
            "BHD": "د.ب",
            "OMR": "ر.ع",
        }.get(currency_code, currency_code)

        # Inventory summary
        inv_row = conn.execute(text("""
            SELECT COUNT(*) AS total_products,
                   COALESCE(SUM(quantity_on_hand), 0) AS total_stock
            FROM products
        """)).mappings().first()
        inventory_summary = {
            "total_products": inv_row["total_products"] if inv_row else 0,
            "total_stock": float(inv_row["total_stock"]) if inv_row else 0,
        }

        # Pending orders
        pending_orders_row = conn.execute(text("""
            SELECT COUNT(*) AS cnt FROM sales_orders WHERE status IN ('draft', 'confirmed')
        """)).mappings().first()
        pending_orders = pending_orders_row["cnt"] if pending_orders_row else 0

        # Pending approvals for current user
        pending_approvals_row = conn.execute(text("""
            SELECT COUNT(*) AS cnt FROM approval_requests
            WHERE approver_id = :uid AND status = 'pending'
        """), {"uid": current_user.id}).mappings().first()
        pending_approvals = pending_approvals_row["cnt"] if pending_approvals_row else 0

        # Recent quotations
        quot_rows = conn.execute(text("""
            SELECT id, quotation_number, customer_name, total_amount, status, created_at
            FROM quotations
            ORDER BY created_at DESC LIMIT 10
        """)).mappings().all()
        recent_quotations = [dict(r) for r in quot_rows]
    finally:
        conn.close()

    return DashboardResponse(
        inventory_summary=inventory_summary,
        pending_orders=pending_orders,
        pending_approvals=pending_approvals,
        recent_quotations=recent_quotations,
        currency_code=currency_code,
        currency_symbol=currency_symbol,
    )


# ---------------------------------------------------------------------------
# POST /mobile/register-device  — register device for push notifications
# ---------------------------------------------------------------------------

@router.post("/register-device", status_code=201)
async def register_device(
    body: DeviceRegisterRequest,
    current_user=Depends(get_current_user),
):
    company_id = _get_company_id(current_user)
    conn = get_db_connection(company_id)
    try:
        with conn.begin():
            # Upsert device registration (store in sync_queue metadata or dedicated table)
            # For now, store as a special sync_queue entry with entity_type='device_registration'
            conn.execute(text("""
                INSERT INTO sync_queue
                    (device_id, user_id, entity_type, entity_id, operation,
                     payload, device_timestamp, server_timestamp, sync_status,
                     created_at, updated_at)
                VALUES
                    (:device_id, :user_id, 'device_registration', NULL, 'create',
                     :payload::jsonb, now(), now(), 'synced', now(), now())
                ON CONFLICT DO NOTHING
            """), {
                "device_id": body.device_id,
                "user_id": current_user.id,
                "payload": _json_dumps({
                    "platform": body.platform,
                    "fcm_token": body.fcm_token,
                }),
            })
    finally:
        conn.close()

    return {"status": "registered", "device_id": body.device_id}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

import json as _json


def _json_dumps(obj) -> str:
    return _json.dumps(obj, default=str)


# Entity table mapping for conflict detection & sync application
_ENTITY_TABLE_MAP = {
    "quotation": {"table": "quotations", "id_col": "id"},
    "sales_order": {"table": "sales_orders", "id_col": "id"},
    "approval": {"table": "approval_requests", "id_col": "id"},
    "inventory_adjustment": {"table": "stock_adjustments", "id_col": "id"},
}


def _check_conflict(conn, entity_type: str, entity_id: int, device_timestamp: datetime) -> tuple[bool, dict | None]:
    """Check if entity was modified on server after device_timestamp."""
    mapping = _ENTITY_TABLE_MAP.get(entity_type)
    if not mapping:
        return False, None

    table = mapping["table"]
    id_col = mapping["id_col"]

    row = conn.execute(text(f"""
        SELECT updated_at FROM {table} WHERE {id_col} = :eid
    """), {"eid": entity_id}).mappings().first()

    if not row:
        return False, None

    server_updated = row["updated_at"]
    if server_updated and server_updated > device_timestamp:
        # Fetch server version
        server_row = conn.execute(text(f"""
            SELECT * FROM {table} WHERE {id_col} = :eid
        """), {"eid": entity_id}).mappings().first()
        return True, {k: str(v) if v is not None else None for k, v in dict(server_row).items()} if server_row else None

    return False, None


def _apply_sync_item(conn, item: SyncItem, user_id: int) -> int | None:
    """Apply a single sync item (create or update) and return entity_id."""
    return _apply_sync_item_raw(conn, item.entity_type, item.entity_id, item.payload, user_id)


def _apply_sync_item_raw(conn, entity_type: str, entity_id: int | None, payload: dict, user_id: int) -> int | None:
    """Apply a sync change to the actual entity table."""
    mapping = _ENTITY_TABLE_MAP.get(entity_type)
    if not mapping:
        logger.warning("Unknown entity_type for sync: %s", entity_type)
        return entity_id

    table = mapping["table"]
    id_col = mapping["id_col"]

    # Filter payload to only include safe/known columns  
    # For now, store the payload in a generic way — the actual column mapping  
    # depends on the entity type and should be validated per-table
    if entity_id and entity_type != "create":
        # UPDATE — set updated_at and updated_by
        safe_cols = {k: v for k, v in payload.items() if k not in ("id", "created_at", "created_by")}
        if safe_cols:
            set_clause = ", ".join(f"{k} = :{k}" for k in safe_cols)
            safe_cols[id_col] = entity_id
            safe_cols["_user_id"] = user_id
            conn.execute(text(f"""
                UPDATE {table}
                SET {set_clause}, updated_at = now(), updated_by = :_user_id
                WHERE {id_col} = :{id_col}
            """), safe_cols)
        return entity_id
    else:
        # CREATE — use payload fields
        safe_cols = {k: v for k, v in payload.items() if k not in ("id", "created_at", "updated_at")}
        safe_cols["created_by"] = str(user_id)
        safe_cols["updated_by"] = str(user_id)
        if safe_cols:
            col_names = ", ".join(safe_cols.keys())
            col_params = ", ".join(f":{k}" for k in safe_cols.keys())
            result = conn.execute(text(f"""
                INSERT INTO {table} ({col_names}, created_at, updated_at)
                VALUES ({col_params}, now(), now())
                RETURNING {id_col}
            """), safe_cols)
            row = result.first()
            return row[0] if row else None
        return None
