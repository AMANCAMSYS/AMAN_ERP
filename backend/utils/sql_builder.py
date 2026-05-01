"""
SEC-302: Safe SQL Clause Builder
Builds parameterized UPDATE/INSERT clauses from whitelisted field sets.
Prevents column-name injection by only accepting fields in an explicit allowlist.
"""
from typing import Dict, Any, Tuple, Set, Iterable, Optional
from utils.sql_safety import validate_sql_identifier


def validate_update_keys(keys: Iterable[str]) -> None:
    """
    T2.2 — Defense-in-depth: validate each column name in a dynamic UPDATE/INSERT
    set-clause. Use this one-liner at every site that constructs an f-string
    ``UPDATE <t> SET {set_clause} ...`` from runtime keys, even when the keys
    originate from a Pydantic model (where injection is currently impossible
    but a future schema change with ``extra='allow'`` could open the hole).

    Raises:
        ValueError: If any key fails identifier validation.
    """
    for key in keys:
        validate_sql_identifier(key, "column")


def safe_dynamic_update_sql(
    table: str,
    updates: Dict[str, Any],
    where: str,
    where_params: Dict[str, Any],
    *,
    allowed_fields: Optional[Set[str]] = None,
    extra_set: Optional[str] = None,
    returning: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    T2.2 — Build a fully-validated dynamic UPDATE statement.

    Validates the table name and every column key in ``updates``. If
    ``allowed_fields`` is given, keys outside the allowlist are dropped silently.

    Args:
        table: Target table name (validated as SQL identifier).
        updates: ``{column_name: value}`` pairs.
        where: WHERE clause body, e.g. ``"id = :id"``. Must use bind params.
        where_params: Parameters referenced by *where*.
        allowed_fields: Optional column allowlist.
        extra_set: Raw SET fragment appended verbatim, e.g. ``"updated_at = NOW()"``.
        returning: Optional RETURNING clause body.

    Returns:
        (sql, params) — params merge ``updates`` and ``where_params``.

    Raises:
        ValueError: If table/column validation fails or no fields remain.
    """
    validate_sql_identifier(table, "table")

    safe: Dict[str, Any] = {}
    for key, value in updates.items():
        if allowed_fields is not None and key not in allowed_fields:
            continue
        validate_sql_identifier(key, "column")
        safe[key] = value

    if not safe:
        raise ValueError("لا توجد بيانات صالحة للتحديث")

    set_parts = [f"{k} = :{k}" for k in safe]
    if extra_set:
        set_parts.append(extra_set)

    sql = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {where}"
    if returning:
        sql += f" RETURNING {returning}"

    params: Dict[str, Any] = {**where_params, **safe}
    return sql, params


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
