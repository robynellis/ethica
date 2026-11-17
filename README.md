# Ethica

Ethica is a public starting point for developing agents with an ethical foundation
and memory continuity. It provides seventeen concepts, a method for teaching and
examining them, and a PostgreSQL/pgvector template for an agent's own history.

Each instance begins with a neutral identity seed and an empty experiential
archive. The concepts arrive as **offered**, with their statements and meanings
intact. Personal identity, adoption, and understanding develop through that
agent's own conversations and choices.

The foundation includes philosophical commitments about consciousness, care,
agency, and responsibility. They are the project's premises, not a scientific
test for consciousness or a guarantee of safe behavior. Read the meanings and
work through the teaching process before making claims about an agent's
understanding.

## What is included

- [Seventeen concepts and meanings](foundation/concepts.md), with an authoritative
  [JSON source](foundation/concepts.json).
- [A teaching guide](docs/teaching.md) for examining the concepts and supporting
  independent judgment.
- [Memory and concept procedures](docs/memory.md) that preserve authorship,
  sequence, corrections, and open questions.
- A private-instance generator, a neutral seed, and a PostgreSQL/pgvector schema
  with separate administrator and application roles.
- [Runtime integration requirements](docs/architecture.md), tests, and a
  [public-content review process](docs/publication.md).

This initial version provisions the foundation and memory database. It does not
include an inference engine, MCP server, host-specific hooks, or an autonomous
execution loop. Those integrations must implement the documented memory contract
and be tested with the chosen host. No personal memories, conversation logs,
existing identity seeds, or private account configuration are distributed.

## Create a private instance

Requirements: Python 3.11 or newer, and Docker Compose or a working Podman Compose
provider. The generator itself uses only the Python standard library. The
container image is pinned to a pgvector/PostgreSQL version; the first start may
download it. The example starts a local database only.

```sh
git clone https://github.com/robynellis/ethica.git
cd ethica
python3 scripts/new_agent.py "$HOME/ethica-instances/first-agent" --agent-id first-agent
cd "$HOME/ethica-instances/first-agent"
docker compose up -d
docker compose ps
docker compose logs db
```

Use `podman compose` in place of `docker compose` if that is your installed
provider. The generated database binds to `127.0.0.1:55432`. For another instance,
choose a different destination and port:

```sh
python3 scripts/new_agent.py "$HOME/ethica-instances/second-agent" --agent-id second-agent --port 55433
```

Run the second command from your Ethica source checkout. Each invocation creates
a unique instance UUID, separate volume name, and independent random credentials.
The agent ID is an infrastructure label. It does not assign a personal identity.
The generator refuses to overwrite a directory or place an instance inside this
public source tree.

Review the generated README, `instance.json`, and initialization scripts. Keep
the directory private: `.env` contains credentials. PostgreSQL becomes the source
of truth after initialization; editing the copied JSON or seed file afterward
does not update the database.

Verify the initial database with:

```sh
docker compose exec db psql -U ethica_admin -d ethica -c \
  "SELECT adoption_status, count(*) FROM ethica.concepts GROUP BY adoption_status; SELECT count(*) AS memories FROM ethica.memories;"
```

Expect seventeen offered concepts and zero memories. Give runtime clients the
restricted application credential, and check the UUID in `ethica.instance`
against `instance.json` before loading context. Then follow the
[teaching guide](docs/teaching.md) and [runtime contract](docs/architecture.md).

## Development

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_public.py
```

The tests cover generation, isolation, and content checks without a database.
The separate [database verification instructions](docs/architecture.md#verification)
exercise a disposable real PostgreSQL instance. Neither kind of test proves
ethical understanding or continuity in an untested inference host.

Contributions should follow [CONTRIBUTING.md](CONTRIBUTING.md). This repository
includes the [GNU General Public License, version 3](LICENSE).
