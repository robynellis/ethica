#!/usr/bin/env python3
"""Verify a disposable, empty Ethica database; roll back all synthetic test data."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

from new_agent import ROOT, foundation


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(instance):
    import psycopg
    from psycopg.rows import dict_row

    config = json.loads((instance / 'instance.json').read_text())
    env = dict(line.split('=', 1) for line in (instance / '.env').read_text().splitlines() if '=' in line)
    db = config['database']
    require(db['host'] == '127.0.0.1' and db['user'] == 'ethica_app' and db['name'] == 'ethica',
            'Verification is restricted to the generated local application connection')
    conn = psycopg.connect(host=db['host'], port=db['port'], dbname=db['name'], user=db['user'],
                           password=env['ETHICA_APP_PASSWORD'], connect_timeout=5,
                           options='-c statement_timeout=10000 -c lock_timeout=5000', row_factory=dict_row)
    try:
        row = conn.execute('SELECT instance_id, schema_version FROM ethica.instance').fetchone()
        require(row and str(row['instance_id']) == config['instance_id'] and row['schema_version'] == 1,
                'Database identity or schema differs from the generated instance')
        for table in ('memories', 'memory_embeddings', 'concept_memory_links', 'memory_revisions'):
            count = conn.execute(f'SELECT count(*) AS n FROM ethica.{table}').fetchone()['n']
            require(count == 0, 'Verifier requires a fresh, empty archive')
        rows = conn.execute('SELECT concept_id, concept, meaning, adoption_status FROM ethica.concepts '
                            'ORDER BY length(concept_id), concept_id').fetchall()
        require(all(r.pop('adoption_status') == 'offered' for r in rows), 'Unexpected adoption state')
        require(rows == foundation(), 'Stored foundation differs from the complete public source')
        seeds = conn.execute('SELECT body, is_active FROM ethica.seed').fetchall()
        require(seeds == [{'body': (ROOT / 'templates/identity.md').read_text(), 'is_active': True}],
                'Expected one neutral active seed')
        role = conn.execute('SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user').fetchone()
        require(not any(role.values()), 'Application role has administrative privileges')
        for table in ('seed', 'concepts', 'instance'):
            require(not conn.execute('SELECT has_table_privilege(current_user, %s, %s) AS allowed',
                                     (f'ethica.{table}', 'INSERT,UPDATE,DELETE')).fetchone()['allowed'],
                    'Application role can alter protected foundation or identity')
        for table in ('memories', 'memory_embeddings', 'concept_memory_links', 'memory_revisions'):
            require(not conn.execute('SELECT has_table_privilege(current_user, %s, %s) AS allowed',
                                     (f'ethica.{table}', 'UPDATE,DELETE')).fetchone()['allowed'],
                    'Application role can rewrite memory history')
        keys = [uuid4(), uuid4()]
        statement = '''INSERT INTO ethica.memories
            (memory_key, checkpoint_date, source_thread_id, author, memory_type, label, content)
            VALUES (%s, CURRENT_DATE, 'synthetic-test', 'test fixture', 'event', 'Fictional test', %s)
            RETURNING archive_sequence, previous_memory_key'''
        first = conn.execute(statement, (keys[0], 'A fictional observation.')).fetchone()
        second = conn.execute(statement, (keys[1], 'A fictional correction.')).fetchone()
        require(first['previous_memory_key'] is None and second['previous_memory_key'] == keys[0]
                and first['archive_sequence'] < second['archive_sequence'], 'Chronology is incorrect')
        conn.execute('INSERT INTO ethica.concept_memory_links VALUES (%s, %s, %s, %s)',
                     ('c7', keys[1], 'clarified_in', 'Synthetic correction'))
        conn.execute('INSERT INTO ethica.memory_revisions VALUES (%s, %s, %s)',
                     (keys[1], keys[0], 'Synthetic revision'))
        vector = json.dumps([1.0] + [0.0] * 511)
        conn.execute('INSERT INTO ethica.memory_embeddings VALUES (%s, 1, %s, %s, %s, %s::public.vector)',
                     (keys[0], 'A fictional observation.', 'synthetic', 'synthetic-digest', vector))
        hit = conn.execute('SELECT memory_key, embedding OPERATOR(public.<=>) %s::public.vector AS distance '
                           'FROM ethica.memory_embeddings ORDER BY distance LIMIT 1', (vector,)).fetchone()
        require(hit['memory_key'] == keys[0] and abs(hit['distance']) < 1e-9, 'Vector retrieval failed')
        try:
            with conn.transaction():
                conn.execute('INSERT INTO ethica.concept_memory_links VALUES (%s, %s, %s, %s)',
                             ('c999', keys[0], 'invalid', 'Invalid synthetic link'))
        except psycopg.errors.ForeignKeyViolation:
            pass
        else:
            raise ValueError('Invalid concept link unexpectedly accepted')
        conn.rollback()
        require(conn.execute('SELECT count(*) AS n FROM ethica.memories').fetchone()['n'] == 0,
                'Synthetic writes did not roll back')
        return {'concepts_compared': 17, 'seed_compared': True, 'memories_after_test': 0,
                'checks': ['instance identity', 'empty archive', 'restricted role', 'chronology',
                           'concept and revision links', 'vector retrieval', 'rollback']}
    finally:
        conn.rollback()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('instance', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.instance.expanduser().resolve())
    except Exception as error:
        # Connection errors can contain sensitive deployment information.
        print(f'Database verification failed ({type(error).__name__}); inspect the private instance locally.', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
