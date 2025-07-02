#!/usr/bin/env python3
"""
Script to fix Google Drive integration file
"""

import re

# Read the file
with open('app/integrations/google_drive.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Replace script_url checks
content = re.sub(
    r'if not self\.script_url:',
    'script_url = self._get_script_url()\n        if not script_url:',
    content
)

# Pattern 2: Replace requests.post calls with self.script_url
content = re.sub(
    r'requests\.post\(\s*self\.script_url,',
    'requests.post(\n                script_url,',
    content
)

# Write the file back
with open('app/integrations/google_drive.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Google Drive integration file")
