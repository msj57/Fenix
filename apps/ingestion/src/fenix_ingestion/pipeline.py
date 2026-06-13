"""Orquestación de la ingesta: parse → chunk → embed → upsert idempotente.

Idempotencia por hash de contenido: un documento sin cambios no se re-embebe
(re-ejecutar `make ingest` es gratis salvo que algo cambie).
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import psycopg

from fenix_ingestion.chunker import Chunk, chunk_markdown
from fenix_ingestion.parser import ParsedDocument, parse_document
from fenix_retrieval.db import apply_schema, connect, vector_literal
from fenix_retrieval.embedder import count_tokens, embed_texts

logger = logging.getLogger(__name__)

_UPSERT_DOCUMENT_SQL = """
INSERT INTO documents (source_path, doc_type, lang, title, services, content_hash)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (source_path) DO UPDATE SET
    doc_type = EXCLUDED.doc_type,
    lang = EXCLUDED.lang,
    title = EXCLUDED.title,
    services = EXCLUDED.services,
    content_hash = EXCLUDED.content_hash,
    ingested_at = now()
RETURNING id
"""

_INSERT_CHUNK_SQL = """
INSERT INTO chunks (document_id, chunk_index, heading_path, content, token_count, embedding, lang)
VALUES (%s, %s, %s, %s, %s, %s::vector, %s)
"""


def discover_documents(corpus_root: Path) -> list[Path]:
    return sorted(path for path in corpus_root.rglob("*.md") if path.name.lower() != "readme.md")


async def _stored_hash(conn: psycopg.AsyncConnection[Any], source_path: str) -> str | None:
    cursor = await conn.execute(
        "SELECT content_hash FROM documents WHERE source_path = %s", (source_path,)
    )
    row = await cursor.fetchone()
    return None if row is None else str(row[0])


async def _upsert_document(conn: psycopg.AsyncConnection[Any], doc: ParsedDocument) -> int:
    cursor = await conn.execute(
        _UPSERT_DOCUMENT_SQL,
        (doc.source_path, doc.doc_type, doc.lang, doc.title, list(doc.services), doc.content_hash),
    )
    row = await cursor.fetchone()
    assert row is not None
    return int(row[0])


async def _replace_chunks(
    conn: psycopg.AsyncConnection[Any], document_id: int, lang: str, chunks: list[Chunk]
) -> None:
    embeddings = await asyncio.to_thread(embed_texts, [chunk.content for chunk in chunks])
    await conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
    async with conn.cursor() as cursor:
        await cursor.executemany(
            _INSERT_CHUNK_SQL,
            [
                (
                    document_id,
                    index,
                    chunk.heading_path,
                    chunk.content,
                    chunk.token_count,
                    vector_literal(embedding),
                    lang,
                )
                for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
            ],
        )


async def _ingest_one(conn: psycopg.AsyncConnection[Any], path: Path, corpus_root: Path) -> int:
    """Ingesta un documento. Devuelve nº de chunks escritos (0 = sin cambios)."""
    doc = parse_document(path, corpus_root)
    if await _stored_hash(conn, doc.source_path) == doc.content_hash:
        logger.info("= %s (sin cambios)", doc.source_path)
        return 0
    chunks = await asyncio.to_thread(chunk_markdown, doc.body, count_tokens)
    document_id = await _upsert_document(conn, doc)
    await _replace_chunks(conn, document_id, doc.lang, chunks)
    await conn.commit()
    logger.info("✓ %s (%d chunks)", doc.source_path, len(chunks))
    return len(chunks)


async def run(corpus_root: Path) -> int:
    paths = discover_documents(corpus_root)
    if not paths:
        logger.error("No hay documentos .md en %s", corpus_root)
        return 1
    async with await connect() as conn:
        await apply_schema(conn)
        written = [await _ingest_one(conn, path, corpus_root) for path in paths]
    updated = sum(1 for count in written if count)
    logger.info(
        "Ingesta completa: %d documentos (%d nuevos/actualizados, %d sin cambios), %d chunks",
        len(paths),
        updated,
        len(paths) - updated,
        sum(written),
    )
    return 0
