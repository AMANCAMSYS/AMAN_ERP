import os
import re
import ast

def scan_python(directory):
    print(f"\n--- Scanning Backend (Python) in {directory} ---")
    
    # Matches strings that might be natural language.
    # Excludes strings that look like IDs, paths, SQL, or very short.
    # We mainly look for strings that are not part of detail="...", as the user said "غير التي بين ال detail="
    # Actually the user said "غير التي بين ال"" (other than what's in "") ? 
    # Wait, in python, strings are either in '' or "".
    # If the user means "strings that are NOT inside translation keys or detail=""?
    pass

# We will implement a proper AST script to find strings.
