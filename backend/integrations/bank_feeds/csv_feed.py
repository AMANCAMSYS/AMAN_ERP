"""
Generic CSV bank-statement parser.

Configure column mapping via :class:`CSVStatementConfig` — supports every
bank CSV format (name column → semantic meaning).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class CSVStatementConfig:
    date_column: str = "Date"
    value_date_column: Optional[str] = None
    amount_column: Optional[str] = "Amount"         # signed in one column
    debit_column: Optional[str] = None              # OR two columns
    credit_column: Optional[str] = None
    description_column: str = "Description"
    reference_column: Optional[str] = "Reference"
    balance_column: Optional[str] = "Balance"
    currency_column: Optional[str] = None
    default_currency: str = "SAR"
    date_format: str = "%Y-%m-%d"
    decimal_sep: str = "."
    thousand_sep: str = ","
    skip_rows: int = 0


def _parse_decimal(raw: str, cfg: CSVStatementConfig) -> Decimal:
    if raw is None or raw == "":
        return Decimal("0")
    s = str(raw).strip()
    s = s.replace(cfg.thousand_sep, "").replace(cfg.decimal_sep, ".")
    s = s.replace("(", "-").replace(")", "")
    return Decimal(s or "0")


def _parse_date(raw: str, cfg: CSVStatementConfig) -> Optional[date]:
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), cfg.date_format).date()
    except Exception:
        return None


def parse_csv_statement(raw: str | bytes, cfg: Optional[CSVStatementConfig] = None) -> List[Dict[str, Any]]:
    """Parse a CSV bank statement into a list of normalised transaction dicts."""
    cfg = cfg or CSVStatementConfig()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    for _ in range(cfg.skip_rows):
        next(reader, None)
    out: List[Dict[str, Any]] = []
    for row in reader:
        if cfg.debit_column and cfg.credit_column:
            debit = _parse_decimal(row.get(cfg.debit_column, ""), cfg)
            credit = _parse_decimal(row.get(cfg.credit_column, ""), cfg)
            amount = credit - debit
        else:
            amount = _parse_decimal(row.get(cfg.amount_column or "Amount", ""), cfg)
        out.append({
            "posting_date": _parse_date(row.get(cfg.date_column, ""), cfg),
            "value_date": _parse_date(row.get(cfg.value_date_column or "", ""), cfg),
            "amount": amount,
            "currency": row.get(cfg.currency_column or "", cfg.default_currency) or cfg.default_currency,
            "description": (row.get(cfg.description_column, "") or "").strip(),
            "reference": (row.get(cfg.reference_column or "", "") or "").strip(),
            "balance": _parse_decimal(row.get(cfg.balance_column or "", ""), cfg)
                       if cfg.balance_column else None,
            "raw": dict(row),
        })
    return out
