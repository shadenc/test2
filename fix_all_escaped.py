#!/usr/bin/env python3
"""Fix all escaped API_URL template literals"""
import re

with open('frontend/src/App.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_count = 0
for i, line in enumerate(lines):
    # Find lines with `$\{API_URL}...' pattern
    if '$\{API_URL}' in line and line.count("`") >= 1:
        # Replace escaped ${ with normal ${ and fix quote
        original = line
        line = line.replace('$\{API_URL}', '${API_URL}')
        # Fix ending quote from ' to `
        if line.rstrip().endswith("'):") or line.rstrip().endswith("',"):
            line = line.rstrip()
            line = line[:-1] + '`' + line[-1:].replace("'", "")
        if original != line:
            lines[i] = line
            fixed_count += 1

with open('frontend/src/App.js', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'Fixed {fixed_count} lines')

