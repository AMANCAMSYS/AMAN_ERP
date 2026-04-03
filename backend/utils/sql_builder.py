"""
SEC-302: Safe SQL Clause Builder
Builds parameterized UPDATE/INSERT clauses from whitelisted field sets.
Prevents column-name injection by only accepting fields in an explicit allowlist.
"""
from typing import Dict, Any, Tuple, Set
from utils.sql_safety import validate_sql_identifier


def build_update_clause(
    allowed_fields: Set[str],
    data: Dict[str, Any],
    *,
    auto_updated_at: bool = True,
) -> Tuple[str, Dict[str, Any]]:
    """
    Build a safe SET clause for UPDATE statements.

    Only keys present in both *allowed_fields* and *data* are included.
    Each column name is validated as a safe SQL identifier.

    Args:
        allowed_fields: Explicit set of column names permitted in this context.
        data: Key-value pairs from the request (e.g. Pydantic model_dump).
        auto_updated_at: Append ``updated_at = CURRENT_TIMESTAMP`` automatically.

    Returns:
        (set_clause, safe_params) — e.g. ("name = :name, status = :status", {"name": "X", "status": "Y"})

    Raises:
        ValueError: If no valid fields remain after filtering, or a field name
                    fails identifier validation.
    """
    safe: Dict[str, Any] = {}
    for key in allowed_fields:
        if key in data:
            validate_sql_identifier(key, "column")
            safe[key] = data[key] if data[key] != "" else None

    if not safe and not auto_updated_at:
        raise ValueError("لا توجد بيانات صالحة للتحديث")

    parts = [f"{k} = :{k}" for k in safe]
    if auto_updated_at:
        parts.append("updated_at = CURRENT_TIMESTAMP")

    return ", ".join(parts), safe


def build_insert_clause(
    allowed_fields: Set[str],
    data: Dict[str, Any],
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build safe column-list and value-placeholder strings for INSERT statements.

    Args:
        allowed_fields: Explicit set of column names permitted.
        data: Key-value pairs to insert.

    Returns:
        (columns_str, placeholders_str, safe_params) — e.g.
        ("name, status", ":name, :status", {"name": "X", "status": "Y"})

    Raises:
        ValueError: If no valid fields remain after filtering.
    """
    safe: Dict[str, Any] = {}
    for key in allowed_fields:
        if key in data:
            validate_sql_identifier(key, "column")
            safe[key] = data[key]

    if not safe:
        raise ValueError("لا توجد بيانات صالحة للإضافة")

    cols = ", ".join(safe.keys())
    placeholders = ", ".join(f":{k}" for k in safe)
    return cols, placeholders, safe
