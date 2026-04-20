import json
import re

def update_file(filename, en_data, ar_data):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We will search for un-localized text and apply them
    # Because applying to all 170+ places automatically is risky (requires knowing the right key structure),
    # I will just write a script that adds a few critical ones the user pointed out.
    pass

