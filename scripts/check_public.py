#!/usr/bin/env python3
"""Check the public worktree and index without printing suspected secret values."""
from pathlib import Path
import re
import subprocess
import sys

from new_agent import ROOT, foundation
from render_concepts import render

PUBLIC_FILES = {
    '.gitignore', 'AGENTS.md', 'LICENSE', 'README.md', 'CONTRIBUTING.md',
    '.github/workflows/check.yml',
    'foundation/concepts.json', 'foundation/concepts.md',
    'docs/teaching.md', 'docs/memory.md', 'docs/architecture.md', 'docs/publication.md',
    'templates/identity.md', 'templates/schema.sql',
    'scripts/new_agent.py', 'scripts/render_concepts.py', 'scripts/check_public.py',
    'scripts/verify_database.py',
    'tests/test_template.py', 'tests/test_public.py',
}
PATTERNS = {
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'cloud access key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'provider token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{30,})'),
    'personal absolute path': re.compile(r'(?:[/]Users[/]|[/]home[/])[A-Za-z0-9_.-]+[/]|[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+'),
    'credential-bearing URL': re.compile(r'\b(?:postgres(?:ql)?|https?)://[^\s/:]+:[^\s/@]+@'),
    'assigned instance credential': re.compile(r'(?m)^ETHICA_(?:ADMIN|APP)_PASSWORD=[A-Za-z0-9]{16,}'),
}


def inspect_text(name, data):
    errors = []
    if name not in PUBLIC_FILES:
        errors.append(f'{name}: file is not in the reviewed public manifest')
    try:
        value = data.decode('utf-8')
    except UnicodeDecodeError:
        return errors + [f'{name}: non-UTF-8 content requires explicit review']
    for label, pattern in PATTERNS.items():
        if pattern.search(value):
            errors.append(f'{name}: possible {label}; inspect privately')
    return errors


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def check():
    errors = []
    paths = {p.decode() for p in git('ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0') if p}
    checked = 0
    for name in sorted(paths):
        path = ROOT / name
        if path.is_symlink():
            errors.append(f'{name}: symlinks are not permitted in the public manifest')
        elif path.is_file():
            errors.extend(inspect_text(name, path.read_bytes()))
            checked += 1
    for entry in git('ls-files', '--stage', '-z').split(b'\0'):
        if not entry:
            continue
        header, name_bytes = entry.split(b'\t', 1)
        mode, object_id, stage = header.decode().split()
        name = name_bytes.decode()
        if mode not in {'100644', '100755'} or stage != '0':
            errors.append(f'{name}: unexpected index entry requires review')
            continue
        errors.extend('index: ' + e for e in inspect_text(name, git('cat-file', 'blob', object_id)))
    for name in sorted(PUBLIC_FILES):
        if not (ROOT / name).is_file():
            errors.append(f'{name}: required public file is missing')
    try:
        foundation()
        if (ROOT / 'foundation/concepts.md').read_text() != render():
            errors.append('Concept documentation differs from its JSON source; regenerate it')
    except (ValueError, KeyError, OSError) as error:
        errors.append(f'Foundation validation failed ({type(error).__name__})')
    return checked, errors


def main():
    try:
        checked, errors = check()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f'Public-content check unavailable ({type(error).__name__})', file=sys.stderr)
        return 1
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f'Checked {checked} worktree files and all index entries: manifest and pattern checks passed.')
    print('Manual review of provenance, private meaning, and outgoing history is still required.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
