#!/usr/bin/env python3
"""Fix quote mismatches in fetch calls"""
import re

with open('frontend/src/App.js', 'r') as f:
    content = f.read()

# Find all fetch calls with ${API_URL} that end with single quote instead of backtick
# Pattern: fetch(`${API_URL}/...'  should be fetch(`${API_URL}/...`
content = re.sub(
    r"fetch\(`(\$\{API_URL\}[^`']+)'",
    r'fetch(`\1`',
    content
)

with open('frontend/src/App.js', 'w') as f:
    f.write(content)

print('Fixed quote mismatches!')

