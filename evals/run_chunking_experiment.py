"""Experimento de estrategias de chunking (F1 DoD): target=500 vs target=250 tokens.

Compara cómo afecta el tamaño de chunk a la calidad del retrieval (hit@5, MRR de los
tres modos). Es autocontenido y NO toca la tabla `chunks` de producción: ingesta el
corpus en una tabla temporal `chunks_exp` (misma estructura) por cada estrategia, mide,
y vuelca una tabla comparativa a docs/evals.md.

Determinista y sin LLM. Reproducible con `make eval-chunking` (corpus ingestado no es
requisito: este script ingesta por su cuenta en la tabla temporal).

Uso de GPU según FENIX_DEVICE (ADR-009). En CPU es lento (reembebe el corpus 2 veces).
"""

import argparse
import asyncio
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import psycopg
import yaml

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("FENIX_DEVICE", "auto")

from fenix_ingestion.chunker import chunk_markdown
from fenix_ingestion.parser import parse_document
from fenix_retrieval.config import get_settings
from fenix_retrieval.db import connect, vector_literal
from fenix_retrieval.embedder import count_tokens, embed_texts
from fenix_retrieval.metrics import hit_at_k, mean, reciprocal_rank
from fenix_retrieval.rrf import rrf_fuse

MODES = ("dense", "hybrid", "hybrid_rerank")
STRATEGIES = {"target=500 (actual)": 500, "target=250": 250}

_MARK_START = "<!-- BEGIN eval-chunking (autogenerado) -->"
_MARK_END = "<!-- END eval-chunking -->"

_EXP_TABLE = "chunks_exp"

_CREATE_SQL = f"""
DROP TABLE IF EXISTS {_EXP_TABLE};
CREATE TABLE {_EXP_TABLE} (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_path  text NOT NULL,
    title        text NOT NULL,
    doc_type     text NOT NULL,
    heading_path text NOT NULL DEFAULT '',
    content      text NOT NULL,
    embedding    vector(1024) NOT NULL,
    lang         text NOT NULL,
    tsv          tsvector GENERATED ALWAYS AS (
        to_tsvector(
            CASE lang WHEN 'es' THEN 'spanish'::regconfig ELSE 'english'::regconfig END,
            content
        )
    ) STORED
);
CREATE INDEX {_EXP_TABLE}_hnsw ON {_EXP_TABLE}
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX {_EXP_TABLE}_tsv ON {_EXP_TABLE} USING gin (tsv);
"""

_INSERT_SQL = f"""
INSERT INTO {_EXP_TABLE} (source_path, title, doc_type, heading_path, content, embedding, lang)
VALUES (%s, %s, %s, %s, %s, %s::vector, %s)
"""

_DENSE_SQL = f"""
SELECT id, source_path FROM {_EXP_TABLE}
ORDER BY embedding <=> %s::vector LIMIT %s
"""

_LEXICAL_SQL = f"""
SELECT c.id, c.source_path
FROM {_EXP_TABLE} c, websearch_to_tsquery(%s::regconfig, %s) q
WHERE c.tsv @@ q ORDER BY ts_rank_cd(c.tsv, q) DESC, c.id LIMIT %s
"""


class Case:
    def __init__(self, raw: dict[str, object]) -> None:
        self.question = str(raw["question"])
        self.relevant: set[str] = set(cast(list[str], raw["relevant"]))


def load_cases(path: Path) -> list[Case]:
    return [Case(item) for item in yaml.safe_load(path.read_text(encoding="utf-8"))]


async def _ingest_strategy(
    conn: psycopg.AsyncConnection[Any], corpus_root: Path, target_tokens: int
) -> int:
    await conn.execute(_CREATE_SQL)
    await conn.commit()
    paths = sorted(p for p in corpus_root.rglob("*.md") if p.name.lower() != "readme.md")
    total = 0
    for path in paths:
        doc = parse_document(path, corpus_root)
        chunks = await asyncio.to_thread(
            chunk_markdown, doc.body, count_tokens, target_tokens=target_tokens
        )
        embeddings = await asyncio.to_thread(embed_texts, [c.content for c in chunks])
        async with conn.cursor() as cur:
            await cur.executemany(
                _INSERT_SQL,
                [
                    (
                        doc.source_path,
                        doc.title,
                        doc.doc_type,
                        chunk.heading_path,
                        chunk.content,
                        vector_literal(emb),
                        doc.lang,
                    )
                    for chunk, emb in zip(chunks, embeddings, strict=True)
                ],
            )
        total += len(chunks)
    await conn.commit()
    return total


async def _paths_per_mode(
    conn: psycopg.AsyncConnection[Any], question: str, k: int
) -> dict[str, list[str]]:
    settings = get_settings()
    per_source = settings.candidates_per_source
    vector = (await asyncio.to_thread(embed_texts, [question]))[0]

    dense_cur = await conn.execute(_DENSE_SQL, (vector_literal(vector), per_source))
    dense = [(row[0], row[1]) for row in await dense_cur.fetchall()]

    es_cur = await conn.execute(_LEXICAL_SQL, ("spanish", question, per_source))
    en_cur = await conn.execute(_LEXICAL_SQL, ("english", question, per_source))
    lex_es = [(row[0], row[1]) for row in await es_cur.fetchall()]
    lex_en = [(row[0], row[1]) for row in await en_cur.fetchall()]

    path_by_id = dict(dense + lex_es + lex_en)
    fused = rrf_fuse(
        [[c for c, _ in dense], [c for c, _ in lex_es], [c for c, _ in lex_en]],
        k=settings.rrf_k,
    )
    dense_paths = [sp for _, sp in dense[:k]]
    hybrid_paths = [path_by_id[cid] for cid, _ in fused[:k] if cid in path_by_id]
    # Sin reranker aquí: el experimento de chunking compara estrategias de troceado;
    # añadir el cross-encoder duplicaría coste sin cambiar la conclusión sobre chunking.
    return {"dense": dense_paths, "hybrid": hybrid_paths, "hybrid_rerank": hybrid_paths}


async def _evaluate(
    conn: psycopg.AsyncConnection[Any], cases: Sequence[Case], k: int
) -> dict[str, dict[str, float]]:
    acc: dict[str, dict[str, list[float]]] = {m: {"hit": [], "rr": []} for m in MODES}
    for case in cases:
        paths = await _paths_per_mode(conn, case.question, k)
        for mode in MODES:
            acc[mode]["hit"].append(hit_at_k(paths[mode], case.relevant, k))
            acc[mode]["rr"].append(reciprocal_rank(paths[mode], case.relevant))
    return {m: {"hit@k": mean(acc[m]["hit"]), "mrr": mean(acc[m]["rr"])} for m in MODES}


def render(results: dict[str, dict[str, dict[str, float]]], chunks: dict[str, int], k: int) -> str:
    lines = [
        f"_Generado el {datetime.now(UTC):%Y-%m-%d %H:%M UTC} · top_k={k} · sin reranker_",
        "",
        f"| Estrategia | nº chunks | hit@{k} denso | MRR denso | hit@{k} híbrido | MRR híbrido |",
        "|---|---|---|---|---|---|",
    ]
    for name in STRATEGIES:
        r = results[name]
        lines.append(
            f"| {name} | {chunks[name]} | {r['dense']['hit@k']:.3f} | {r['dense']['mrr']:.3f} "
            f"| {r['hybrid']['hit@k']:.3f} | {r['hybrid']['mrr']:.3f} |"
        )
    return "\n".join(lines)


def write_report(table: str, doc: Path) -> None:
    block = f"{_MARK_START}\n{table}\n{_MARK_END}"
    text = doc.read_text(encoding="utf-8")
    if _MARK_START in text:
        doc.write_text(
            f"{text.split(_MARK_START)[0]}{block}{text.split(_MARK_END)[1]}", encoding="utf-8"
        )
    else:
        section = "\n\n## L1 · Experimento de chunking (determinista)\n\n"
        doc.write_text(f"{text.rstrip()}\n{section}{block}\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", type=Path, default=Path("evals/golden/retrieval/cases.yaml"))
    parser.add_argument("--report", type=Path, default=Path("docs/evals.md"))
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    args = parser.parse_args()

    k = get_settings().top_k
    cases = load_cases(args.golden)
    results: dict[str, dict[str, dict[str, float]]] = {}
    n_chunks: dict[str, int] = {}
    async with await connect() as conn:
        for name, target in STRATEGIES.items():
            n_chunks[name] = await _ingest_strategy(conn, args.corpus, target)
            results[name] = await _evaluate(conn, cases, k)
        await conn.execute(f"DROP TABLE IF EXISTS {_EXP_TABLE}")
        await conn.commit()

    table = render(results, n_chunks, k)
    print(table)
    write_report(table, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
