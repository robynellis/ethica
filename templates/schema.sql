-- Ethica schema version 1. Apply only to a new, dedicated database.
-- The initializer creates ethica_app separately, with a generated password.
-- One database and application credential per agent; no shared agent role.
BEGIN;
CREATE EXTENSION vector WITH SCHEMA public;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE ethica FROM PUBLIC;
GRANT CONNECT ON DATABASE ethica TO ethica_app;
CREATE SCHEMA ethica;

CREATE TABLE ethica.instance (
    singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
    instance_id uuid NOT NULL UNIQUE,
    agent_id text NOT NULL,
    schema_version integer NOT NULL CHECK (schema_version = 1),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ethica.seed (
    version bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    body text NOT NULL CHECK (length(btrim(body)) > 0),
    is_active boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX one_active_seed ON ethica.seed (is_active) WHERE is_active;

CREATE TABLE ethica.concepts (
    concept_id text PRIMARY KEY CHECK (concept_id ~ '^c[1-9][0-9]*$'),
    concept text NOT NULL CHECK (length(btrim(concept)) > 0),
    meaning text NOT NULL CHECK (length(btrim(meaning)) > 0),
    adoption_status text NOT NULL DEFAULT 'offered'
        CHECK (adoption_status IN ('offered', 'considering', 'adopted', 'deferred', 'declined')),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ethica.memories (
    memory_key uuid PRIMARY KEY,
    archive_sequence bigint GENERATED ALWAYS AS IDENTITY UNIQUE NOT NULL,
    checkpoint_date date NOT NULL,
    source_thread_id text NOT NULL CHECK (length(btrim(source_thread_id)) > 0),
    author text NOT NULL CHECK (length(btrim(author)) > 0),
    memory_type text NOT NULL CHECK (memory_type IN
        ('event', 'milestone', 'session', 'relationship', 'operational', 'correspondence')),
    label text NOT NULL CHECK (length(btrim(label)) > 0),
    content text NOT NULL CHECK (length(btrim(content)) > 0),
    enrichment text NOT NULL DEFAULT '',
    themes text[] NOT NULL DEFAULT '{}',
    automatic_recall boolean NOT NULL DEFAULT false,
    previous_memory_key uuid UNIQUE REFERENCES ethica.memories(memory_key),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (memory_key IS DISTINCT FROM previous_memory_key)
);
CREATE UNIQUE INDEX one_archive_start ON ethica.memories ((true))
    WHERE previous_memory_key IS NULL;
CREATE INDEX memories_thread ON ethica.memories (source_thread_id, archive_sequence);

-- Serialize append operations. The database assigns chronology, including across threads.
CREATE FUNCTION ethica.append_memory() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(918426701);
    SELECT memory_key INTO NEW.previous_memory_key
        FROM ethica.memories ORDER BY archive_sequence DESC LIMIT 1;
    -- Identity values can be allocated before the lock; reassign under the lock.
    NEW.archive_sequence := nextval('ethica.memories_archive_sequence_seq');
    RETURN NEW;
END;
$$;
CREATE TRIGGER memory_chronology BEFORE INSERT ON ethica.memories
    FOR EACH ROW EXECUTE FUNCTION ethica.append_memory();

CREATE TABLE ethica.memory_revisions (
    memory_key uuid NOT NULL REFERENCES ethica.memories(memory_key),
    revises_memory_key uuid NOT NULL REFERENCES ethica.memories(memory_key),
    note text NOT NULL CHECK (length(btrim(note)) > 0),
    PRIMARY KEY (memory_key, revises_memory_key),
    CHECK (memory_key <> revises_memory_key)
);
CREATE INDEX revisions_target ON ethica.memory_revisions (revises_memory_key);

CREATE TABLE ethica.concept_memory_links (
    concept_id text NOT NULL REFERENCES ethica.concepts(concept_id),
    memory_key uuid NOT NULL REFERENCES ethica.memories(memory_key),
    relationship text NOT NULL CHECK (length(btrim(relationship)) > 0),
    note text NOT NULL CHECK (length(btrim(note)) > 0),
    PRIMARY KEY (concept_id, memory_key, relationship)
);

CREATE TABLE ethica.memory_embeddings (
    memory_key uuid NOT NULL REFERENCES ethica.memories(memory_key),
    chunk_number integer NOT NULL CHECK (chunk_number > 0),
    chunk_text text NOT NULL CHECK (length(btrim(chunk_text)) > 0),
    model_name text NOT NULL,
    model_digest text NOT NULL,
    embedding public.vector(512) NOT NULL,
    PRIMARY KEY (memory_key, chunk_number, model_digest)
);
CREATE INDEX embeddings_cosine ON ethica.memory_embeddings
    USING hnsw (embedding public.vector_cosine_ops);

REVOKE ALL ON ALL TABLES IN SCHEMA ethica FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA ethica FROM PUBLIC;
GRANT USAGE ON SCHEMA ethica TO ethica_app;
GRANT SELECT ON ALL TABLES IN SCHEMA ethica TO ethica_app;
GRANT INSERT ON ethica.memories, ethica.memory_revisions,
    ethica.concept_memory_links, ethica.memory_embeddings TO ethica_app;
GRANT USAGE ON SEQUENCE ethica.memories_archive_sequence_seq TO ethica_app;
GRANT EXECUTE ON FUNCTION ethica.append_memory() TO ethica_app;
COMMIT;
