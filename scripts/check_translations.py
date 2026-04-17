#!/usr/bin/env python3
"""
Comprehensive translation audit script for AMAN ERP.
Scans frontend and backend code for translation keys not present in ar.json / en.json.
"""

import json
import re
import os
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_SRC = PROJECT_ROOT / "frontend" / "src"
BACKEND_DIR = PROJECT_ROOT / "backend"
AR_FILE = FRONTEND_SRC / "locales" / "ar.json"
EN_FILE = FRONTEND_SRC / "locales" / "en.json"

# ── helpers ──────────────────────────────────────────────────────────────

def flatten_json(obj, prefix=""):
    """Flatten nested JSON into dot-notation keys."""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            items.update(flatten_json(v, new_key))
    else:
        items[prefix] = obj
    return items


def extract_frontend_keys(src_dir):
    """
    Extract all t('key') and t("key") calls from .jsx and .js files.
    Also handles t('key', {}) patterns.
    """
    pattern = re.compile(r"""(?:^|[^a-zA-Z_])t\(\s*['"]([\w.]+)['"]\s*[,)]""")
    keys = defaultdict(list)  # key -> list of files
    
    for ext in ("*.jsx", "*.js"):
        for fpath in src_dir.rglob(ext):
            # skip node_modules, locales, i18n config
            rel = str(fpath.relative_to(src_dir))
            if "node_modules" in rel or "locales/" in rel:
                continue
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in pattern.finditer(text):
                key = m.group(1)
                # Filter out obvious non-keys (single chars, urls, etc.)
                if len(key) < 3 or key.startswith("/") or key.startswith("http"):
                    continue
                keys[key].append(rel)
    return keys


def extract_backend_keys(backend_dir):
    """
    Extract translation-like strings from backend Python files.
    Look for patterns like:
      - "detail": "some.key"
      - message keys in HTTPException
      - _(...) or gettext(...)
    """
    # In backend, translations are typically sent as response messages
    # We look for string patterns that match translation key format
    pattern = re.compile(r"""['"]([\w]+(?:\.[\w]+)+)['"]""")
    keys = defaultdict(list)
    
    for fpath in backend_dir.rglob("*.py"):
        rel = str(fpath.relative_to(backend_dir))
        if "__pycache__" in rel or ".venv" in rel:
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in pattern.finditer(text):
            key = m.group(1)
            # Filter: must look like a translation key (module.subkey pattern)
            parts = key.split(".")
            if len(parts) >= 2 and all(p.isidentifier() for p in parts):
                # Exclude Python module paths and common non-translation patterns
                if any(p in key for p in ["os.path", "sys.", "app.", "router.", 
                                           "models.", "schemas.", "sqlalchemy.",
                                           "fastapi.", "datetime.", "logging.",
                                           "json.", "uuid.", "enum.", "typing.",
                                           "starlette.", "pydantic.", "email.",
                                           "http.", "urllib.", "base64.",
                                           "asyncio.", "io.", "re.", "math."]):
                    continue
                keys[key].append(rel)
    return keys


def check_key_exists(flat_dict, key):
    """Check if a key exists in the flattened dictionary."""
    return key in flat_dict


def main():
    print("=" * 80)
    print("  AMAN ERP — Comprehensive Translation Audit")
    print("=" * 80)
    
    # Load translation files
    print("\n📂 Loading translation files...")
    with open(AR_FILE, "r", encoding="utf-8") as f:
        ar_data = json.load(f)
    with open(EN_FILE, "r", encoding="utf-8") as f:
        en_data = json.load(f)
    
    ar_flat = flatten_json(ar_data)
    en_flat = flatten_json(en_data)
    
    print(f"   Arabic keys:  {len(ar_flat)}")
    print(f"   English keys: {len(en_flat)}")
    
    # ── 1. Frontend keys scan ──
    print("\n🔍 Scanning frontend source code for t() calls...")
    fe_keys = extract_frontend_keys(FRONTEND_SRC)
    print(f"   Found {len(fe_keys)} unique translation keys in frontend code")
    
    missing_ar = {}
    missing_en = {}
    
    for key, files in sorted(fe_keys.items()):
        if not check_key_exists(ar_flat, key):
            missing_ar[key] = files
        if not check_key_exists(en_flat, key):
            missing_en[key] = files
    
    # ── 2. Keys in AR but not EN, and vice versa ──
    ar_only = set(ar_flat.keys()) - set(en_flat.keys())
    en_only = set(en_flat.keys()) - set(ar_flat.keys())
    
    # ── Print results ──
    print("\n" + "=" * 80)
    print("  RESULTS")
    print("=" * 80)
    
    # Missing from Arabic
    print(f"\n❌ Keys used in frontend but MISSING from ar.json: {len(missing_ar)}")
    if missing_ar:
        for key, files in sorted(missing_ar.items()):
            print(f"   • {key}")
            for f in files[:2]:
                print(f"     └─ {f}")
    
    # Missing from English
    print(f"\n❌ Keys used in frontend but MISSING from en.json: {len(missing_en)}")
    if missing_en:
        for key, files in sorted(missing_en.items()):
            print(f"   • {key}")
            for f in files[:2]:
                print(f"     └─ {f}")
    
    # Asymmetric keys
    print(f"\n⚠️  Keys in ar.json but NOT in en.json: {len(ar_only)}")
    if ar_only:
        for key in sorted(ar_only)[:50]:
            print(f"   • {key}  →  \"{ar_flat[key]}\"")
        if len(ar_only) > 50:
            print(f"   ... and {len(ar_only) - 50} more")
    
    print(f"\n⚠️  Keys in en.json but NOT in ar.json: {len(en_only)}")
    if en_only:
        for key in sorted(en_only)[:50]:
            print(f"   • {key}  →  \"{en_flat[key]}\"")
        if len(en_only) > 50:
            print(f"   ... and {len(en_only) - 50} more")
    
    # Save full results to JSON for processing
    results = {
        "missing_from_ar": {k: v for k, v in missing_ar.items()},
        "missing_from_en": {k: v for k, v in missing_en.items()},
        "in_ar_not_en": list(ar_only),
        "in_en_not_ar": list(en_only),
    }
    
    output_path = PROJECT_ROOT / "scripts" / "translation_audit_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Full results saved to: {output_path}")
    
    return results


if __name__ == "__main__":
    main()
