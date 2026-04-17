#!/usr/bin/env python3
"""
Deep scan for ALL hardcoded strings in frontend that should be translated.
Also finds all backend English messages that need Arabic translations.
"""
import json, re, os
from pathlib import Path
from collections import defaultdict

PROJECT = Path(__file__).resolve().parent.parent
FE_SRC  = PROJECT / "frontend" / "src"
BE_DIR  = PROJECT / "backend"
AR_F    = FE_SRC / "locales" / "ar.json"
EN_F    = FE_SRC / "locales" / "en.json"

def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    else:
        out[prefix] = obj
    return out

# ── 1  Pick out every t('key', 'fallback') where fallback is used ──
def find_t_with_fallback(src):
    """t('key', 'fallback') — means key might be fine but the fallback is a crutch."""
    pat = re.compile(r"""t\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]""")
    hits = []
    for ext in ("*.jsx", "*.js"):
        for f in src.rglob(ext):
            if "node_modules" in str(f) or "locales" in str(f): continue
            for m in pat.finditer(f.read_text("utf-8", errors="ignore")):
                hits.append((m.group(1), m.group(2), str(f.relative_to(src))))
    return hits

# ── 2  Hardcoded English strings after || 'xyz' ──
def find_or_fallback(src):
    pat = re.compile(r"""\|\|\s*['"]([A-Z][^'"]{3,})['"]""")
    hits = []
    for ext in ("*.jsx", "*.js"):
        for f in src.rglob(ext):
            if "node_modules" in str(f) or "locales" in str(f): continue
            for m in pat.finditer(f.read_text("utf-8", errors="ignore")):
                hits.append((m.group(1), str(f.relative_to(src))))
    return hits

# ── 3  Plain JSX text that's English ──
def find_plain_jsx_text(src):
    """Find >English Text< patterns in JSX that aren't wrapped in t()"""
    pat = re.compile(r""">\s*([A-Z][a-z]+(?:\s+[A-Za-z]+){1,8})\s*<""")
    hits = []
    for ext in ("*.jsx",):
        for f in src.rglob(ext):
            if "node_modules" in str(f) or "locales" in str(f): continue
            text = f.read_text("utf-8", errors="ignore")
            for m in pat.finditer(text):
                val = m.group(1).strip()
                if len(val) > 4 and not val.startswith("{"):
                    hits.append((val, str(f.relative_to(src))))
    return hits

# ── 4  Backend English detail= messages ──
def find_backend_english(be):
    pat = re.compile(r'detail="([A-Za-z][^"]{3,})"')
    hits = []
    for f in be.rglob("*.py"):
        if "__pycache__" in str(f): continue
        text = f.read_text("utf-8", errors="ignore")
        for m in pat.finditer(text):
            hits.append((m.group(1), str(f.relative_to(be))))
    return hits


with open(AR_F) as f: ar = json.load(f)
with open(EN_F) as f: en = json.load(f)
ar_flat = flatten(ar)
en_flat = flatten(en)

print("="*80)
print("  DEEP TRANSLATION SCAN")
print("="*80)

print("\n── 1. t('key','fallback') patterns ──")
t_fb = find_t_with_fallback(FE_SRC)
for key, fb, fl in t_fb[:30]:
    exists_ar = key in ar_flat
    exists_en = key in en_flat
    flag = "✅" if (exists_ar and exists_en) else "❌"
    print(f"  {flag} {key} -> fallback='{fb}'  [{fl}] ar={exists_ar} en={exists_en}")

print(f"\n── 2. || 'Fallback' patterns ({len(find_or_fallback(FE_SRC))}) ──")
for val, fl in find_or_fallback(FE_SRC):
    print(f"  ⚠️  '{val}' in {fl}")

print(f"\n── 3. Hardcoded JSX English text (sample) ──")
jsx_text = find_plain_jsx_text(FE_SRC)
# Filter to unique SecuritySettings
sec_hits = [h for h in jsx_text if "SecuritySettings" in h[1]]
for val, fl in sec_hits:
    print(f"  ⚠️  '{val}' in {fl}")

print(f"\n── 4. Backend English detail= messages ({len(find_backend_english(BE_DIR))}) ──")
be_en = find_backend_english(BE_DIR)
for msg, fl in sorted(be_en)[:20]:
    print(f"  ⚠️  '{msg}' in {fl}")
if len(be_en) > 20:
    print(f"  ... and {len(be_en)-20} more")

print("\n" + "="*80)
print(f"TOTAL: {len(t_fb)} t() with fallbacks, {len(find_or_fallback(FE_SRC))} || fallbacks, {len(sec_hits)} hardcoded JSX in Security, {len(be_en)} backend English messages")
