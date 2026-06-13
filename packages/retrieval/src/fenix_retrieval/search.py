"""Búsqueda híbrida: denso (HNSW) + FTS es/en → RRF → reranker (ADR-001).

Los tres modos existen para el experimento de F1 (denso vs híbrido vs
híbrido+rerank). Los scores NO son comparables entre modos: similitud coseno,
score RRF y score del cross-encoder respectivamente.

Una conexión por llamada: suficiente para evals y scripts; el pool llega con
la API en F2.
"""

import asyncio
from typing import Any, Literal

import psycopg

from fenix_retrieval.config import get_settings
from fenix_retrieval.db import connect, vector_literal
from fenix_retrieval.embedder import embed_query
from fenix_retrieval.models import ChunkResult
from fenix_retrieval.reranker import rerank
from fenix_retrieval.rrf import rrf_fuse

SearchMode = Literal["dense", "hybrid", "hybrid_rerank"]

_DENSE_SQL = """
SELECT id, 1 - (embedding <=> %s::vector) AS score
FROM chunks
ORDER BY embedding <=> %s::vector
LIMIT %s
"""

_LEXICAL_SQL = """
SELECT c.id
FROM chunks c, websearch_to_tsquery(%s::regconfig, %s) q
WHERE c.tsv @@ q
ORDER BY ts_rank_cd(c.tsv, q) DESC, c.id
LIMIT %s
"""

_FETCH_SQL = """
SELECT c.id, c.document_id, d.source_path, d.title, d.doc_type, c.lang, c.heading_path, c.content
FROM chunks c
JOIN documents d ON d.id = c.document_id
WHERE c.id = ANY(%s)
"""


async def _dense_ranking(
    conn: psycopg.AsyncConnection[Any], query_vector: list[float], limit: int
) -> list[tuple[int, float]]:
    literal = vector_literal(query_vector)
    cursor = await conn.execute(_DENSE_SQL, (literal, literal, limit))
    return [(row[0], row[1]) for row in await cursor.fetchall()]


async def _lexical_ranking(
    conn: psycopg.AsyncConnection[Any], query: str, ts_config: str, limit: int
) -> list[int]:
    cursor = await conn.execute(_LEXICAL_SQL, (ts_config, query, limit))
    return [row[0] for row in await cursor.fetchall()]


async def _fetch_chunks(
    conn: psycopg.AsyncConnection[Any], scored_ids: list[tuple[int, float]]
) -> list[ChunkResult]:
    ids = [chunk_id for chunk_id, _ in scored_ids]
    cursor = await conn.execute(_FETCH_SQL, (ids,))
    by_id = {
        row[0]: ChunkResult(
            chunk_id=row[0],
            document_id=row[1],
            source_path=row[2],
            title=row[3],
            doc_type=row[4],
            lang=row[5],
            heading_path=row[6],
            content=row[7],
            score=0.0,
        )
        for row in await cursor.fetchall()
    }
    return [
        by_id[chunk_id].model_copy(update={"score": score})
        for chunk_id, score in scored_ids
        if chunk_id in by_id
    ]


async def _candidates(
    conn: psycopg.AsyncConnection[Any], query: str, mode: SearchMode, limit: int
) -> list[tuple[int, float]]:
    settings = get_settings()
    per_source = settings.candidates_per_source
    query_vector = await asyncio.to_thread(embed_query, query)
    dense = await _dense_ranking(conn, query_vector, per_source)
    if mode == "dense":
        return dense[:limit]
    lexical_es = await _lexical_ranking(conn, query, "spanish", per_source)
    lexical_en = await _lexical_ranking(conn, query, "english", per_source)
    fused = rrf_fuse(
        [[chunk_id for chunk_id, _ in dense], lexical_es, lexical_en],
        k=settings.rrf_k,
    )
    return fused[:limit]


async def search(
    query: str, mode: SearchMode = "hybrid_rerank", top_k: int | None = None
) -> list[ChunkResult]:
    """Punto de entrada del retrieval. Devuelve top_k chunks con metadatos de cita."""
    settings = get_settings()
    final_k = top_k or settings.top_k
    candidate_k = settings.rerank_candidates if mode == "hybrid_rerank" else final_k
    async with await connect() as conn:
        scored = await _candidates(conn, query, mode, candidate_k)
        chunks = await _fetch_chunks(conn, scored)
    if mode == "hybrid_rerank":
        return await asyncio.to_thread(rerank, query, chunks, final_k)
    return chunks[:final_k]
