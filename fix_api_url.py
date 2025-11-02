#!/usr/bin/env python3
"""
Fix API_URL template literals in App.js
"""
import re

with open('frontend/src/App.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix fetch calls that have '${API_URL}/ (should be backticks)
content = re.sub(r"fetch\('\$\{API_URL\}/", r'fetch(`$\{API_URL}/', content)

# Fix template literals: 'API_URL/... becomes '${API_URL}/...
content = re.sub(r"`API_URL/", r"`${API_URL}/", content)
content = re.sub(r"'API_URL/", r"'${API_URL}/", content)
content = re.sub(r'"API_URL/', r'"${API_URL}/', content)

# Fix fetch calls: fetch('API_URL/ becomes fetch(`${API_URL}/
content = re.sub(r"fetch\(`API_URL/", r"fetch(`${API_URL}/", content)

# Also handle href cases
content = re.sub(r"href=\{`API_URL", r"href={`${API_URL}", content)

with open('frontend/src/App.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed all API_URL template literals!')

