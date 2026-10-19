#!/usr/bin/env python3
"""Fail if any relative Markdown link points to a file that does not exist."""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
bad = []
for md in ROOT.rglob('*.md'):
    for m in re.finditer(r'\[[^\]]*\]\(([^)\s]+)\)', md.read_text()):
        t = m[1].split('#')[0]
        if not t or t.startswith(('http://', 'https://', 'mailto:')): continue
        if not (md.parent / t).resolve().exists(): bad.append(f'{md.relative_to(ROOT)}: {m[1]}')
print('\n'.join(bad) if bad else 'All relative links resolve.')
sys.exit(1 if bad else 0)
