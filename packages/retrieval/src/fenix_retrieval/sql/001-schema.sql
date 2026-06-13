-- Schema del almacén RAG (F1). Idempotente: make ingest lo aplica en cada arranque.
-- ADR-001: un solo Postgres para vectores (pgvector HNSW) y léxico (FTS tsvector).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_path  text NOT NULL UNIQUE,
    doc_type     text NOT NULL CHECK (doc_type IN ('runbook', 'postmortem', 'ticket')),
    lang         text NOT NULL CHECK (lang IN ('es', 'en')),
    title        text NOT NULL,
    services     text[] NOT NULL DEFAULT '{}',
    content_hash text NOT NULL,
    ingested_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id  bigint NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index  int NOT NULL,
    heading_path text NOT NULL DEFAULT '',
    content      text NOT NULL,
    token_count  int NOT NULL,
    -- bge-m3 produce vectores de 1024 dims, normalizados -> distancia coseno.
    embedding    vector(1024) NOT NULL,
    -- FTS con diccionario según idioma del documento (stemming correcto ES/EN).
    lang         text NOT NULL CHECK (lang IN ('es', 'en')),
    tsv          tsvector GENERATED ALWAYS AS (
        to_tsvector(
            CASE lang WHEN 'es' THEN 'spanish'::regconfig ELSE 'english'::regconfig END,
            content
        )
    ) STORED,
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING gin (tsv);

CREATE INDEX IF NOT EXISTS chunks_document_id ON chunks (document_id);
