#!/usr/bin/env python3
"""Create a private, fresh Ethica instance from an explicit public-file allowlist."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'docker.io/pgvector/pgvector:0.8.7-pg18-trixie'


def foundation():
    data = json.loads((ROOT / 'foundation/concepts.json').read_text())
    if data.get('format_version') != 1:
        raise ValueError('Unsupported foundation format')
    rows = data['concepts']
    if [r['concept_id'] for r in rows] != [f'c{i}' for i in range(1, 18)]:
        raise ValueError('Expected the seventeen ordered foundation concepts')
    for row in rows:
        if set(row) != {'concept_id', 'concept', 'meaning'}:
            raise ValueError('Unexpected field in the public foundation')
        if any(not isinstance(v, str) or not v.strip() for v in row.values()):
            raise ValueError('Concept fields must be nonempty text')
    return rows


def literal(value):
    # Standard-conforming PostgreSQL string literal; no shell interpolation.
    if '\x00' in value:
        raise ValueError('NUL is not valid PostgreSQL text')
    return "'" + value.replace("'", "''") + "'"


def initialize(destination, agent_id, port=55432):
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', agent_id):
        raise ValueError('Use a lowercase agent ID starting with a letter (up to 48 characters)')
    if isinstance(port, bool) or not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError('Port must be between 1024 and 65535')
    path = Path(destination).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError('Private instances must be created outside the public source tree')
    if path.exists():
        raise ValueError('Destination already exists; refusing to overwrite an instance')
    rows = foundation()
    identity = (ROOT / 'templates/identity.md').read_text()
    schema = (ROOT / 'templates/schema.sql').read_text()
    instance_id = str(uuid4())
    project = 'ethica-' + instance_id.replace('-', '')[:12]
    admin_password, app_password = secrets.token_hex(32), secrets.token_hex(32)
    inserts = [
        'BEGIN;',
        'SET standard_conforming_strings = on;',
        'INSERT INTO ethica.instance (instance_id, agent_id, schema_version) VALUES ('
        + literal(instance_id) + ', ' + literal(agent_id) + ', 1);',
        'INSERT INTO ethica.seed (body, is_active) VALUES (' + literal(identity) + ', true);',
    ]
    for row in rows:
        inserts.append('INSERT INTO ethica.concepts (concept_id, concept, meaning) VALUES ('
                       + ', '.join(literal(row[k]) for k in ('concept_id', 'concept', 'meaning')) + ');')
    inserts.append('COMMIT;')
    config = {
        'format_version': 1, 'instance_id': instance_id, 'agent_id': agent_id,
        'compose_project': project,
        'database': {'host': '127.0.0.1', 'port': port, 'name': 'ethica', 'user': 'ethica_app'},
        'embedding': {'base_url': 'http://127.0.0.1:11434',
                      'model': 'qwen3-embedding:0.6b', 'dimensions': 512},
        'foundation_sha256': hashlib.sha256((ROOT / 'foundation/concepts.json').read_bytes()).hexdigest(),
    }
    compose = f'''name: {project}
services:
  db:
    image: {IMAGE}
    environment:
      POSTGRES_USER: ethica_admin
      POSTGRES_DB: ethica
      POSTGRES_PASSWORD: ${{ETHICA_ADMIN_PASSWORD:?Missing admin password}}
      ETHICA_APP_PASSWORD: ${{ETHICA_APP_PASSWORD:?Missing application password}}
    ports:
      - "127.0.0.1:{port}:5432"
    volumes:
      - memory:/var/lib/postgresql
      - ./init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ethica_admin -d ethica"]
      interval: 5s
      timeout: 5s
      retries: 12
volumes:
  memory:
'''
    role_script = '''#!/bin/sh
set -eu
psql -X --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \\
  --set=app_password="$ETHICA_APP_PASSWORD" <<'SQL'
CREATE ROLE ethica_app LOGIN PASSWORD :'app_password';
SQL
'''
    files = {
        '.env': f'ETHICA_ADMIN_PASSWORD={admin_password}\nETHICA_APP_PASSWORD={app_password}\n',
        '.gitignore': '*\n',
        'instance.json': json.dumps(config, indent=2) + '\n',
        'identity.md': identity,
        'foundation.json': (ROOT / 'foundation/concepts.json').read_text(),
        'compose.yaml': compose,
        'init/10-role.sh': role_script,
        'init/20-schema.sql': schema,
        'init/30-foundation.sql': '\n'.join(inserts) + '\n',
        'README.md': f'''# Private Ethica instance: {agent_id}

This directory contains generated credentials. Keep it private and outside public repositories.
Your agent ID is an infrastructure label, not a chosen personal name.

Before the first database start, review `identity.md`. If you edit it, also update
the seed INSERT in `init/30-foundation.sql`; only the SQL initializes PostgreSQL.
The database becomes the authoritative store once initialized.

From this directory, run `docker compose up -d` (or `podman compose up -d`).
Check `docker compose ps` and `docker compose logs db` for initialization errors.
Use `docker compose exec db psql -U ethica_admin -d ethica` for operator setup.
Runtime clients must use the restricted `ethica_app` user and the application
password in `.env`. Do not give an agent the administrator password.

Connection settings and the instance UUID are in `instance.json`. Check that UUID
against `ethica.instance` before attaching a runtime, to catch a wrong port or database.
The schema starts with seventeen offered concepts, one neutral seed, and zero memories.
An inference runtime, startup loading, embedding service, and per-turn retrieval
must be connected explicitly; this template does not start an autonomous agent.

Initialization scripts run only against an empty data volume. Editing these files
later does not update an existing database. Stop with `docker compose down` to
retain the volume. Do not remove the volume unless you intend to erase this instance.
Back up the database and credentials privately before migrating or removing it.
''',
    }
    previous_umask = os.umask(0o077)
    created = False
    try:
        path.mkdir(parents=True, exist_ok=False)
        created = True
        for name, text in files.items():
            target = path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
            if target.read_text(encoding='utf-8') != text:
                raise OSError('Generated file did not match its intended contents')
        # Init scripts need to be readable by the container's PostgreSQL user.
        # They contain no passwords; credentials remain in the private .env file.
        (path / 'init').chmod(0o755)
        for target in (path / 'init').iterdir():
            target.chmod(0o644)
    except BaseException:
        if created:
            shutil.rmtree(path)
        raise
    finally:
        os.umask(previous_umask)
    return {'path': str(path), 'instance_id': instance_id, 'files': len(files),
            'concepts': len(rows), 'memories': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--agent-id', required=True)
    parser.add_argument('--port', type=int, default=55432)
    args = parser.parse_args()
    try:
        result = initialize(args.destination, args.agent_id, args.port)
    except (ValueError, OSError) as error:
        print(f'Instance creation failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
