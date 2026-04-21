"""
SWIFT MT940 bank-statement parser.

MT940 is the SWIFT end-of-day bank statement format still used by most
non-SEPA retail and corporate banks. Each statement is a block of tagged
fields delimited by ``:<tag>:``. This module parses the subset we care
about for reconciliation:

  :20: — transaction reference
  :25: — account identification
  :28C: — statement / sequence number
  :60F: / :60M: — opening balance (final / intermediate)
  :61: — statement line (one per transaction)
  :86: — information to account owner (free-form)
  :62F: / :62M: — closing balance
  :64: — available balance

Reference: https://www.sepaforcorporates.com/swift-for-corporates/account-statement-mt940-file-format-overview/
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class MT940Transaction:
    value_date: date
    entry_date: Optional[date]
    amount: Decimal                   # signed: +credit, -debit
    currency: str
    transaction_type: str             # SWIFT code (e.g. NTRF, NMSC)
    reference: str
    bank_reference: Optional[str] = None
    description: str = ""


@dataclass
class MT940Statement:
    account: str
    statement_number: str
    currency: str
    opening_balance: Decimal
    closing_balance: Decimal
    transactions: List[MT940Transaction] = field(default_factory=list)


def _parse_date(yymmdd: str) -> date:
    """MT940 dates are YYMMDD — pivot on 70: <70 → 20xx, else 19xx."""
    if not yymmdd or len(yymmdd) != 6:
        raise ValueError(f"bad MT940 date {yymmdd!r}")
    year = int(yymmdd[:2])
    year += 2000 if year < 70 else 1900
    return date(year, int(yymmdd[2:4]), int(yymmdd[4:6]))


_TAG_RE = re.compile(r"^:(\d{1,3}[A-Z]?):", re.MULTILINE)

# :61: subfield regex — value date + opt entry date + D/C + amount + tx type
_LINE61_RE = re.compile(
    r"^(?P<vdate>\d{6})"            # value date YYMMDD
    r"(?P<edate>\d{4})?"            # optional entry date MMDD
    r"(?P<rc>R?[CD])"               # Credit/Debit (optional 'R' = reversal)
    r"(?P<amt>\d+(?:,\d+)?)"        # amount with comma decimal
    r"(?P<txt>N[A-Z0-9]{3})"        # transaction type 'N' + 3 chars
    r"(?P<rest>.*)$",
    re.DOTALL,
)


def _split_blocks(text: str) -> List[tuple[str, str]]:
    """Return a list of (tag, value) preserving order."""
    blocks: List[tuple[str, str]] = []
    matches = list(_TAG_RE.finditer(text))
    for i, m in enumerate(matches):
        tag = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        value = text[start:end].strip("\r\n -")
        blocks.append((tag, value))
    return blocks


def parse_mt940(raw: str) -> List[MT940Statement]:
    """Parse a raw MT940 file (may contain multiple statements)."""
    statements: List[MT940Statement] = []
    current: Optional[MT940Statement] = None
    pending_txn: Optional[MT940Transaction] = None

    for tag, value in _split_blocks(raw):
        if tag == "20":
            # start of a new statement — flush pending
            if current:
                if pending_txn:
                    current.transactions.append(pending_txn)
                    pending_txn = None
                statements.append(current)
            current = MT940Statement(
                account="", statement_number="", currency="",
                opening_balance=Decimal("0"), closing_balance=Decimal("0"),
            )
        elif current is None:
            continue
        elif tag == "25":
            current.account = value.strip()
        elif tag == "28C":
            current.statement_number = value.strip()
        elif tag in ("60F", "60M"):
            bal = _parse_balance(value)
            current.currency = bal["currency"]
            current.opening_balance = bal["amount"]
        elif tag == "61":
            if pending_txn:
                current.transactions.append(pending_txn)
            pending_txn = _parse_line61(value, currency=current.currency)
        elif tag == "86":
            if pending_txn is not None:
                pending_txn.description = (pending_txn.description + " " + value.strip()).strip()
        elif tag in ("62F", "62M"):
            bal = _parse_balance(value)
            current.closing_balance = bal["amount"]

    if current:
        if pending_txn:
            current.transactions.append(pending_txn)
        statements.append(current)
    return statements


def _parse_balance(value: str) -> dict:
    """Parse :60F:/:62F:  DC + YYMMDD + CCY + amount."""
    # e.g. "C240115EUR1500,00"
    value = value.strip()
    dc = value[0]
    ccy = value[7:10]
    amt_str = value[10:].replace(",", ".")
    amount = Decimal(amt_str)
    if dc == "D":
        amount = -amount
    return {"dc": dc, "currency": ccy, "amount": amount}


def _parse_line61(value: str, currency: str) -> MT940Transaction:
    m = _LINE61_RE.match(value.strip())
    if not m:
        raise ValueError(f"bad MT940 :61: line: {value!r}")
    vdate = _parse_date(m.group("vdate"))
    edate = None
    if m.group("edate"):
        try:
            edate = date(vdate.year, int(m.group("edate")[:2]), int(m.group("edate")[2:]))
        except Exception:
            edate = None
    rc = m.group("rc")
    amount = Decimal(m.group("amt").replace(",", "."))
    if rc.endswith("D"):
        amount = -amount
    tx_type = m.group("txt")
    rest = (m.group("rest") or "").strip()
    # The rest may contain customer reference //bank reference + description
    reference = rest
    bank_ref: Optional[str] = None
    if "//" in rest:
        reference, bank_ref_and_more = rest.split("//", 1)
        bank_ref = bank_ref_and_more.split("\n", 1)[0].strip() or None
    return MT940Transaction(
        value_date=vdate,
        entry_date=edate,
        amount=amount,
        currency=currency,
        transaction_type=tx_type,
        reference=reference.strip(),
        bank_reference=bank_ref,
    )
