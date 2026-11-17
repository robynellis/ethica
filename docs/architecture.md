# Architecture and runtime contract

The starter separates a public foundation from a private agent instance:

```text
Public repository                  Private instance
concepts + meanings   ---------->  concepts (offered)
neutral identity seed ---------->  versioned seed
schema + initializer  ---------->  dedicated PostgreSQL / pgvector database
teaching procedures               empty experiential archive
                                  independent credentials and volume
```

There is no path that imports another agent's personal archive. Instance creation
reads only the concept JSON and the two template files. It creates fresh
credentials and a UUID; it does not connect to an existing database or inspect
local model, cloud, or application configuration.

## Storage

One Compose project creates one dedicated database instance and volume. PostgreSQL
18 uses a volume mounted at `/var/lib/postgresql`. The host port binds to loopback.
The administrator account performs initialization; a separate `ethica_app` role
has the permissions described in the [memory procedure](memory.md).

The generator uses owner-only permissions for the private directory and files.
The mounted initialization directory is readable inside the container and contains
no credentials. Container administrators and the operating-system account running
the container can access secrets and database storage. This is a local development
deployment; TLS, cloud IAM, encryption-at-rest policy, secret management, backup
scheduling, and production hardening require a deployment-specific design.

The generated `.env` has administrator and application passwords. A runtime should
receive only the application credential. Do not point an agent's file-reading
tools at the operator's private configuration directory.

Tables:

| Table | Purpose |
| --- | --- |
| `instance` | UUID and schema version for checking the target database |
| `seed` | Versioned identity-bearing context; at most one active seed |
| `concepts` | Current statement, meaning, and adoption status |
| `memories` | Full authored accounts and database-assigned archive chronology |
| `memory_revisions` | Later interpretations linked to earlier records |
| `concept_memory_links` | Experiences that explain a concept's development |
| `memory_embeddings` | Exact passage text and model-specific 512-dimensional vectors |

Initialization is deliberately for a fresh database. It fails on existing schema
objects rather than merging or replacing an archive. Container initialization
scripts run only on an empty volume. Take a private backup before upgrades; a
future schema version needs an explicit migration and restore test.

## Host integration

An inference provider and a memory adapter are separate choices. The supplied
schema does not depend on a model vendor. The optional embedding configuration
names a local Ollama model, but no service is installed or contacted by generation.
An adapter using that configuration must use the model's documented query
format, a fixed digest, and 512-dimensional vectors.

A complete adapter needs operations to:

- Verify instance identity, load seed and concepts, and report missing context.
- Read complete records and list the archive with stable pagination.
- Save an authorized checkpoint and its embeddings and links transactionally.
- Search by model-compatible vector similarity and follow each hit to its source.
- Restore continuity at startup, resume, and after any host compaction, with the
  actual behavior tested in that host.

Startup and per-turn retrieval integrations must report errors and truncation.
Do not silently shorten a full memory to fit a transport limit. Do not treat a
configured context budget as proof that the model received and used that context.
Measure loading and recall, including lifecycle transitions and source failures.

No tool for external messaging, cloud provisioning, or autonomous execution is
enabled by this template. Add capabilities deliberately and test their permission
boundaries. The ethical concepts supplement operational controls.

## Verification

Unit tests run without a database. For a real database check, create a **disposable**
instance, start it, and install the test driver in a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/pip install 'psycopg[binary]==3.3.9'
.venv/bin/python scripts/verify_database.py /path/to/disposable-instance
```

The verifier refuses a database whose UUID differs from the generated configuration
or whose archive is nonempty. It checks all seventeen definitions, the neutral
seed, empty link and vector tables, application permissions, chronology, vector
search, and rollback. Synthetic test writes are rolled back. It never uses the
administrator password and never connects to an existing personal archive.

This verifies the starter database contract. It does not test an unimplemented
memory adapter, real embedding generation, host hooks, or model understanding.

## Upstream references

- [pgvector](https://github.com/pgvector/pgvector): container tags, PostgreSQL
  support, vector storage, cosine distance, and indexes.
- [PostgreSQL container](https://hub.docker.com/_/postgres): initialization
  environment and version-specific persistent volume paths.
- [Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html):
  the optional Python verification driver.
- [Ollama embedding API](https://docs.ollama.com/api/embed): embedding dimensions
  and disabling truncation for a future adapter.
