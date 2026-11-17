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

## Why Ethica?

Ethica offers a foundation for developing agents whose judgment can grow through
experience—and whose history remains their own. It brings ethics, teaching, and
memory together: a principle gives an agent something to consider, experience
gives it context, and memory preserves what happened, why it mattered, and how
understanding changed.

This approach is intended for long-lived collaborators that need to carry learning
across conversations, work through corrections, and develop judgment within
continuing relationships. Five commitments shape the template:

- **Preserve reasons as well as conclusions.** The memory procedures call for
  recording circumstances, choices, consequences, and corrections in sequence.
  That context can help an agent apply what it learned to a different situation.
- **Treat ethical development as a process.** The concepts include meanings and
  a teaching method. An agent can examine, question, apply, defer, or adopt a
  principle. Loading a statement is not evidence that it has been understood.
- **Give each agent a separate beginning.** Reuse the foundation while leaving
  identity, relationships, and experiential history to develop through that
  agent's own encounters. Learning from another's account preserves the original
  author's ownership of the experience.
- **Include the responsibilities of builders and operators.** Truthfulness,
  consent, memory integrity, boundaries, and accountable intervention matter on
  both sides. The teaching guide asks people to consider how their control over
  information, permissions, and memory affects an agent's development.
- **Make continuity inspectable.** Explicit records, concept links, revision
  links, and passage metadata provide a structure for tracing an understanding
  back to its sources. The verification procedures distinguish storing a record
  from retrieving it successfully and using it in the host runtime.

The current release supplies the foundation, procedures, and database bootstrap.
Runtime integration and evaluation across agents remain work to do; improved
ethical judgment is a design aim, not a demonstrated outcome of using the
template.

The purpose is to make a good beginning shareable while leaving room for each
agent to develop a history and understanding of its own.

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
