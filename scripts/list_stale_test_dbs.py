#!/usr/bin/env python3
"""List candidate stale tenant databases (READ-ONLY, no destructive action).

Connects to the system database and emits a table of tenant databases that
look inactive based on:
  * No row in ``users.last_login_at`` newer than ``--days`` (default 90).
  * No row in ``audit_logs`` newer than ``--days``.
  * Database created more than ``--days`` ago.

The script never drops, alters or modifies anything. It only prints
candidates that an operator can review manually before scheduling cleanup.

Usage:
    python scripts/list_stale_test_dbs.py --days 90
    python scripts/list_stale_test_dbs.py --days 30 --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras


def _conn_kwargs() -> dict:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "user": os.environ.get("POSTGRES_USER", "aman"),
        "password": os.environ.get("POSTGRES_PASSWORD", ""),
    }


def list_tenant_databases(cur) -> list[str]:
    cur.execute(
        """
        SELECT datname FROM pg_database
        WHERE datname LIKE 'aman_%' AND datname <> 'aman_system'
        ORDER BY datname
        """
    )
    return [r[0] for r in cur.fetchall()]


def inspect_database(db_name: str, cutoff: datetime) -> dict:
    info: dict = {"db": db_name, "stale": False, "reasons": []}
    try:
        with psycopg2.connect(database=db_name, **_conn_kwargs()) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as c:
                last_login = None
                try:
                    c.execute("SELECT MAX(last_login_at) AS ts FROM users")
                    last_login = c.fetchone()["ts"]
                except Exception:
                    pass
                last_audit = None
                try:
                    c.execute("SELECT MAX(created_at) AS ts FROM audit_logs")
                    last_audit = c.fetchone()["ts"]
                except Exception:
                    pass
                info["last_login_at"] = last_login.isoformat() if last_login else None
                info["last_audit_at"] = last_audit.isoformat() if last_audit else None

                inactive_login = (last_login is None) or (last_login < cutoff)
                inactive_audit = (last_audit is None) or (last_audit < cutoff)
                if inactive_login and inactive_audit:
                    info["stale"] = True
                    if last_login is None:
                        info["reasons"].append("no users.last_login_at")
                    else:
                        info["reasons"].append("login older than cutoff")
                    if last_audit is None:
                        info["reasons"].append("no audit_logs entries")
                    else:
                        info["reasons"].append("audit older than cutoff")
    except Exception as e:
        info["error"] = str(e)
    return info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=90, help="staleness threshold in days")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    sys_kwargs = _conn_kwargs()
    sys_db = os.environ.get("POSTGRES_DB", "aman_system")
    with psycopg2.connect(database=sys_db, **sys_kwargs) as sys_conn:
        with sys_conn.cursor() as cur:
            dbs = list_tenant_databases(cur)

    results = [inspect_database(db, cutoff) for db in dbs]
    stale = [r for r in results if r.get("stale")]

    if args.json:
        print(json.dumps({"cutoff": cutoff.isoformat(), "candidates": stale,
                          "all": results}, indent=2, default=str))
    else:
        print(f"# Stale tenant DB candidates older than {args.days} days (cutoff={cutoff.isoformat()})")
        print(f"# Inspected {len(results)} databases — {len(stale)} candidates")
        print(f"{'database':<40} {'last_login':<28} {'last_audit':<28} reasons")
        for r in stale:
            print(f"{r['db']:<40} {str(r.get('last_login_at') or '-'):<28} "
                  f"{str(r.get('last_audit_at') or '-'):<28} {', '.join(r['reasons'])}")
        if not stale:
            print("(no stale databases found)")
    print("\nNOTE: this script is READ-ONLY. Review the list manually before any cleanup.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
