#!/usr/bin/env python3
"""
Add @limiter.limit() decorators and request: Request params to finance router endpoints.
GET endpoints -> 200/minute, mutation endpoints (POST/PUT/PATCH/DELETE) -> 100/minute
"""
import re
import sys

FILES = [
    "backend/routers/finance/accounting.py",
    "backend/routers/finance/budgets.py",
    "backend/routers/finance/cost_centers.py",
    "backend/routers/finance/currencies.py",
    "backend/routers/finance/intercompany_v2.py",
    "backend/routers/finance/advanced_workflow.py",
    "backend/routers/finance/costing_policies.py",
]

LIMITER_IMPORT = "from utils.limiter import limiter"
REQUEST_IMPORT = "from fastapi import Request"


def ensure_imports(content: str, filepath: str) -> str:
    """Add missing imports to file."""
    # Add limiter import if missing
    if "from utils.limiter import limiter" not in content:
        # Insert after the last 'from utils.' or 'from routers.' import
        lines = content.split("\n")
        insert_after = -1
        for idx, line in enumerate(lines):
            if line.startswith("from utils.") or line.startswith("from routers.") or line.startswith("from database"):
                insert_after = idx
        if insert_after == -1:
            # Fallback: insert after first import block
            for idx, line in enumerate(lines):
                if line.startswith("from ") or line.startswith("import "):
                    insert_after = idx
        lines.insert(insert_after + 1, LIMITER_IMPORT)
        content = "\n".join(lines)

    # Add Request to fastapi import if missing
    if "Request" not in content and "from fastapi import" in content:
        content = re.sub(
            r"(from fastapi import )([^\n]+)",
            lambda m: m.group(1) + m.group(2).rstrip() + ", Request",
            content,
            count=1,
        )
    elif "Request" not in content:
        lines = content.split("\n")
        lines.insert(0, "from fastapi import Request")
        content = "\n".join(lines)

    return content


def transform_content(content: str) -> str:
    """Add rate limiting decorators and request: Request params."""
    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect @router.METHOD( start
        router_match = re.match(r"(\s*)@router\.(get|post|put|delete|patch)\s*\(", line)
        if router_match:
            indent = router_match.group(1)
            method = router_match.group(2).lower()
            rate = "200/minute" if method == "get" else "100/minute"

            # Collect full decorator (may span multiple lines) until balanced parens
            decorator_lines = [line]
            depth = line.count("(") - line.count(")")
            while depth > 0 and i + 1 < len(lines):
                i += 1
                decorator_lines.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")

            result.extend(decorator_lines)

            # Insert @limiter.limit(...) after the full router decorator
            result.append(f"{indent}@limiter.limit(\"{rate}\")")

            # Now process the `def` line (may also be multi-line)
            i += 1
            def_line = lines[i]

            # Check if `request: Request` already present in the def line
            already_has_request = "request: Request" in def_line or "request:Request" in def_line

            if not already_has_request:
                # Peek ahead to check multi-line signature
                # Check if paren closes on same line
                def_depth = def_line.count("(") - def_line.count(")")
                if def_depth == 0:
                    # Check if the whole signature block has request: Request
                    already_has_request = False  # single line, checked above
                else:
                    # Multi-line: check remaining sig lines
                    lookahead = i + 1
                    while lookahead < len(lines) and def_depth > 0:
                        lk = lines[lookahead]
                        if "request: Request" in lk or "request:Request" in lk:
                            already_has_request = True
                            break
                        def_depth += lk.count("(") - lk.count(")")
                        lookahead += 1

            if not already_has_request:
                # Add `request: Request` as first non-self param
                paren_pos = def_line.find("(")
                if paren_pos >= 0:
                    after_paren = def_line[paren_pos + 1:]
                    # If the def line just has `(` at end (multi-line signature coming)
                    if after_paren.strip() == "" or after_paren.strip() == "\n":
                        result.append(def_line)
                        # Insert request: Request as next line with proper indent
                        i += 1
                        # Add request param before the next content line
                        result.append(f"{indent}    request: Request,")
                    else:
                        # Single-line or params start on same line
                        new_def = def_line[: paren_pos + 1] + "request: Request, " + after_paren
                        result.append(new_def)
                else:
                    result.append(def_line)
            else:
                result.append(def_line)

            i += 1
            continue

        result.append(line)
        i += 1

    return "\n".join(result)


def process_file(filepath: str, dry_run: bool = False):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    content = ensure_imports(original, filepath)
    content = transform_content(content)

    if dry_run:
        # Show diff summary
        orig_lines = original.split("\n")
        new_lines = content.split("\n")
        added = len(new_lines) - len(orig_lines)
        print(f"  {filepath}: +{added} lines")
        return

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Verify
    with open(filepath, "r", encoding="utf-8") as f:
        verify = f.read()
    limiter_uses = len(re.findall(r"@limiter\.limit\(", verify))
    router_defs = len(re.findall(r"@router\.(get|post|put|delete|patch)\(", verify))
    print(f"  {filepath}: {router_defs} endpoints, {limiter_uses} limiter decorators applied")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    print(f"{'DRY RUN - ' if dry_run else ''}Adding rate limiting to finance routers...\n")
    for f in FILES:
        process_file(f, dry_run)
    print("\nDone.")
