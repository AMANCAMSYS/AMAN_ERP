import os
import re
import ast

def is_natural_language(text):
    # Very basic heuristic for natural language vs code/constants
    if len(text) < 3: return False
    # Skip if it looks like a path, URL, CSS class, SQL, enum, or UUID
    if '/' in text or '\\' in text or 'http' in text: return False
    if re.match(r'^[A-Z0-9_]+$', text): return False
    if re.match(r'^[a-z0-9_-]+$', text): return False # camelCase/kebab-case IDs
    if '_' in text and ' ' not in text: return False
    if text.endswith('.js') or text.endswith('.json') or text.endswith('.css'): return False
    
    # Needs to have at least some alphabet characters
    has_letters = bool(re.search(r'[a-zA-Z\u0600-\u06FF]', text))
    if not has_letters: return False
    
    return True

# --- PYTHON SCANNER ---
class StringVisitor(ast.NodeVisitor):
    def __init__(self):
        self.strings = []

    def visit_Call(self, node):
        func_name = ''
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        # Skip logger.info("...") or HTTPException(detail="...") if user excludes them,
        # but user specifically asked for ANY text "other than what's inside "" "
        # Wait, if text is in Python, it's ALWAYS in "" or ''. 
        # I'll just record all natural language strings not part of `t('...')`
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            if is_natural_language(node.value):
                # check if it's a docstring or just a print/raise
                self.strings.append((node.lineno, node.value))
        self.generic_visit(node)

def scan_python_file(filepath):
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        visitor = StringVisitor()
        visitor.visit(tree)
        for lineno, val in visitor.strings:
            # exclude docstrings loosely
            if '\n' in val and len(val) > 50:
                continue
            results.append((lineno, val))
    except Exception:
        pass
    return results

def scan_backend():
    print("--- Scanning Backend (Python) Hardcoded Strings ---")
    be_dir = "backend"
    found = 0
    for root, _, files in os.walk(be_dir):
        for file in files:
            if file.endswith('.py') and not root.startswith(os.path.join(be_dir, 'venv')):
                path = os.path.join(root, file)
                res = scan_python_file(path)
                if res:
                    # simplify output
                    for ln, text in res:
                        if text not in ["utf-8", "application/json", "Authorization"]:  # common falses
                            print(f"{path}:{ln} -> {repr(text)}")
                            found += 1
    print(f"Total backend hardcoded strings found: {found}\n")

# --- JSX SCANNER ---
def scan_frontend():
    print("--- Scanning Frontend (JSX) Hardcoded Strings ---")
    fe_dir = "frontend/src"
    
    # Match text outside of JSX tags: > text <
    text_pattern = re.compile(r'>\s*([A-Za-z\u0600-\u06FF][^\n<]{2,})\s*<')
    # Match strings inside quotes but NOT inside t("")
    # This is tricky because we want to ignore things like className="text-xl"
    # We will search for common attributes like label="Text", placeholder="Text", title="Text"
    attr_pattern = re.compile(r'\b(?:label|placeholder|title)=["\']([^"\']+)["\']')
    
    found = 0
    for root, _, files in os.walk(fe_dir):
        for file in files:
            if file.endswith('.jsx') or file.endswith('.js'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        # skip console.log
                        if 'console.log' in line: continue
                        
                        # 1. Text between tags
                        for m in text_pattern.finditer(line):
                            text = m.group(1).strip()
                            if is_natural_language(text):
                                # make sure it's not a t() fallback like || "Fallback"
                                if "|| '" in line or '|| "' in line: continue
                                print(f"{path}:{i+1} (Tag Text) -> {repr(text)}")
                                found += 1
                        
                        # 2. Text in attributes
                        for m in attr_pattern.finditer(line):
                            text = m.group(1).strip()
                            # check if it's dynamic like label={t('...')}
                            if '{' in text or '}' in text: continue
                            if getattr(text, 'startswith', lambda x:False)('t('): continue
                            
                            if is_natural_language(text):
                                print(f"{path}:{i+1} (Attribute) -> {repr(text)}")
                                found += 1
                except Exception:
                    pass
    print(f"Total frontend hardcoded strings found: {found}")

if __name__ == "__main__":
    scan_backend()
    scan_frontend()
