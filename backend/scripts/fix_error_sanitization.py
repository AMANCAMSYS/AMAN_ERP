#!/usr/bin/env python3
"""
T004-T008: Fix all error sanitization violations.
- Replace detail=str(e) with generic Arabic message + logger.exception()
- Replace traceback.print_exc() with logger.exception()
- Replace print(f"...{e}...") with logger.exception()
"""
import re
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERIC_ERROR_500 = '"حدث خطأ داخلي"'
GENERIC_ERROR_400 = '"طلب غير صالح"'


def ensure_logger(content: str, filepath: str) -> str:
    """Add import logging + logger if not present."""
    has_logging_import = bool(re.search(r'^import logging', content, re.MULTILINE))
    has_getlogger = bool(re.search(r'logger\s*=\s*logging\.getLogger', content))

    if has_logging_import and has_getlogger:
        return content

    lines = content.split('\n')
    insert_idx = 0

    # Find last import line
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_idx = i + 1

    additions = []
    if not has_logging_import:
        additions.append('import logging')
    if not has_getlogger:
        additions.append('logger = logging.getLogger(__name__)')

    if additions:
        # Insert after last import, with a blank line
        for j, add_line in enumerate(additions):
            lines.insert(insert_idx + j, add_line)

    return '\n'.join(lines)


def fix_detail_str_e(content: str) -> tuple[str, int]:
    """Replace detail=str(e) and add logger.exception() before raise."""
    count = 0
    lines = content.split('\n')
    new_lines = []

    for i, line in enumerate(lines):
        # Match keyword form: raise HTTPException(...detail=str(e)...)
        match = re.search(r'(\s*)raise HTTPException\((.*)detail=str\(e\)(.*)\)', line)
        if match:
            indent = match.group(1)
            before_detail = match.group(2)
            after_detail = match.group(3)

            # Determine status code
            status_match = re.search(r'status_code=(\d+)', before_detail)
            status_code = int(status_match.group(1)) if status_match else 500

            if status_code >= 500:
                generic_msg = GENERIC_ERROR_500
            else:
                generic_msg = GENERIC_ERROR_400

            # Add logger.exception() before raise
            new_lines.append(f'{indent}logger.exception("Internal error")')
            new_lines.append(f'{indent}raise HTTPException({before_detail}detail={generic_msg}{after_detail})')
            count += 1
            continue

        # Match positional form: raise HTTPException(500, str(e))
        match2 = re.search(r'(\s*)raise HTTPException\((\d+),\s*str\(e\)\)', line)
        if match2:
            indent = match2.group(1)
            status_code = int(match2.group(2))
            generic_msg = GENERIC_ERROR_500 if status_code >= 500 else GENERIC_ERROR_400
            new_lines.append(f'{indent}logger.exception("Internal error")')
            new_lines.append(f'{indent}raise HTTPException({status_code}, {generic_msg})')
            count += 1
            continue

        new_lines.append(line)

    return '\n'.join(new_lines), count


def fix_traceback_print_exc(content: str) -> tuple[str, int]:
    """Replace traceback.print_exc() with logger.exception()."""
    count = 0
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        if re.search(r'\btraceback\.print_exc\(\)', line):
            indent = re.match(r'(\s*)', line).group(1)
            new_lines.append(f'{indent}logger.exception("Unexpected error")')
            count += 1
        elif re.search(r'\btraceback\.format_exc\(\)', line):
            # print(traceback.format_exc()) -> logger.exception(...)
            indent = re.match(r'(\s*)', line).group(1)
            new_lines.append(f'{indent}logger.exception("Unexpected error")')
            count += 1
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), count


def fix_print_statements(content: str) -> tuple[str, int]:
    """Replace print(f"Error...{e}...") with logger.exception()."""
    count = 0
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # Match print(f"...ERROR/Error...{e/str(e)}...")
        if re.search(r'^\s*print\(f?["\'].*(?:error|ERROR|Error).*\)', line, re.IGNORECASE):
            indent = re.match(r'(\s*)', line).group(1)
            new_lines.append(f'{indent}logger.exception("Operation failed")')
            count += 1
        # Match print(f"NOTIFICATION ERROR: {str(e)}")
        elif re.search(r'^\s*print\(f?["\'].*NOTIFICATION.*\)', line, re.IGNORECASE):
            indent = re.match(r'(\s*)', line).group(1)
            new_lines.append(f'{indent}logger.exception("Notification error")')
            count += 1
        # Match print(f"DASHBOARD ERROR: {str(e)}")
        elif re.search(r'^\s*print\(f?["\'].*DASHBOARD.*\)', line, re.IGNORECASE):
            indent = re.match(r'(\s*)', line).group(1)
            new_lines.append(f'{indent}logger.exception("Dashboard error")')
            count += 1
        # Match print(f"UNREAD COUNT ERROR: {str(e)}")
        elif re.search(r'^\s*print\(f?["\'].*UNREAD.*\)', line, re.IGNORECASE):
            indent = re.match(r'(\s*)', line).group(1)
            new_lines.append(f'{indent}logger.exception("Unread count error")')
            count += 1
        else:
            new_lines.append(line)

    return '\n'.join(new_lines), count


def remove_traceback_import(content: str) -> str:
    """Remove 'import traceback' if no longer used."""
    if 'traceback.' not in content.replace('import traceback', ''):
        content = re.sub(r'^import traceback\n', '', content, flags=re.MULTILINE)
    return content


def process_file(filepath: str) -> dict:
    """Process a single file, applying all fixes."""
    with open(filepath, 'r') as f:
        original = f.read()

    content = original
    stats = {'detail_str_e': 0, 'traceback': 0, 'print': 0}

    content, n = fix_detail_str_e(content)
    stats['detail_str_e'] = n

    content, n = fix_traceback_print_exc(content)
    stats['traceback'] = n

    content, n = fix_print_statements(content)
    stats['print'] = n

    total = sum(stats.values())
    if total > 0:
        content = ensure_logger(content, filepath)
        content = remove_traceback_import(content)
        with open(filepath, 'w') as f:
            f.write(content)

    return stats


def find_python_files(directories: list[str]) -> list[str]:
    """Find all .py files in the given directories."""
    files = []
    for d in directories:
        dirpath = os.path.join(BACKEND_DIR, d)
        if not os.path.isdir(dirpath):
            continue
        for root, _, filenames in os.walk(dirpath):
            for fn in filenames:
                if fn.endswith('.py'):
                    files.append(os.path.join(root, fn))
    return sorted(files)


def main():
    # Production code directories (exclude scripts/, tests/)
    dirs = ['routers', 'utils', 'services', 'middleware']
    files = find_python_files(dirs)

    total_fixes = 0
    for fp in files:
        stats = process_file(fp)
        n = sum(stats.values())
        if n > 0:
            rel = os.path.relpath(fp, BACKEND_DIR)
            print(f"  Fixed {rel}: detail_str_e={stats['detail_str_e']}, "
                  f"traceback={stats['traceback']}, print={stats['print']}")
            total_fixes += n

    print(f"\nTotal fixes applied: {total_fixes}")
    return 0 if total_fixes > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
