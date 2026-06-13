"""Experimento de retrieval L1 (F1): denso vs híbrido vs híbrido+rerank.

Determinista y sin LLM. Corre los 3 modos sobre el golden set, calcula hit@k y MRR,
imprime la tabla y la escribe en docs/evals.md entre marcadores. Reproduce el DoD de
F1: hit@5 de híbrido+rerank debe superar a denso solo.

Diseño consciente del coste: el trabajo caro se comparte entre los tres modos. Las
queries se embeben en un solo batch y, por caso, los candidatos se calculan una vez y de
ahí se derivan denso, híbrido (RRF) e híbrido+rerank. Evita el trabajo redundante de la
versión ingenua (una `search()` por modo y caso). Usa GPU si está disponible (ADR-009,
`FENIX_DEVICE=auto`), lo que en una máquina con GPU baja el gate de minutos a segundos.

Uso: `make eval-retrieval` (no invocar a mano; necesita Postgres con corpus ingestado).
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

# Limitar los hilos de torch ANTES de importar nada que lo cargue: con modelos
# pequeños en CPU, demasiados hilos generan contención y ralentizan. Hacerlo aquí
# (no solo vía OMP_NUM_THREADS en el Makefile) lo deja fijado pase como pase.
os.environ.setdefault("OMP_NUM_THREADS", "4")
# En evals Ollama no compite por la VRAM, así que usamos GPU si la hay (ADR-009).
# El usuario puede forzar cpu con FENIX_DEVICE=cpu (p. ej. en CI sin GPU).
os.environ.setdefault("FENIX_DEVICE", "auto")

from fenix_retrieval.config import get_settings
from fenix_retrieval.db import connect
from fenix_retrieval.embedder import embed_texts
from fenix_retrieval.metrics import hit_at_k, mean, reciprocal_rank
from fenix_retrieval.reranker import rerank
from fenix_retrieval.rrf import rrf_fuse
from fenix_retrieval.search import (
    _dense_ranking,
    _fetch_chunks,
    _lexical_ranking,
)

Mode = str
MODES: tuple[Mode, ...] = ("dense", "hybrid", "hybrid_rerank")
MODE_LABELS = {"dense": "denso", "hybrid": "híbrido", "hybrid_rerank": "híbrido+rerank"}

_MARK_START = "<!-- BEGIN eval-retrieval (autogenerado) -->"
_MARK_END = "<!-- END eval-retrieval -->"


class Case:
    def __init__(self, raw: dict[str, object]) -> None:
        self.id = str(raw["id"])
        self.question = str(raw["question"])
        self.relevant: set[str] = set(cast(list[str], raw["relevant"]))


def load_cases(path: Path) -> list[Case]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Case(item) for item in raw]


async def _paths_per_mode(
    conn: psycopg.AsyncConnection[Any], question: str, query_vector: list[float], final_k: int
) -> dict[Mode, list[str]]:
    """Calcula, para una query, los source_paths recuperados por cada modo.

    El embedding de la query se calcula una sola vez en batch (ver `evaluate`); aquí
    solo se hacen búsquedas SQL (rápidas) y un rerank por caso.
    """
    settings = get_settings()
    per_source = settings.candidates_per_source

    dense = await _dense_ranking(conn, query_vector, per_source)
    lexical_es = await _lexical_ranking(conn, question, "spanish", per_source)
    lexical_en = await _lexical_ranking(conn, question, "english", per_source)

    dense_ids = [chunk_id for chunk_id, _ in dense]
    fused = rrf_fuse([dense_ids, lexical_es, lexical_en], k=settings.rrf_k)

    # Chunks de la unión de candidatos (un solo fetch reutilizable).
    union_scored = dense + fused
    chunks = await _fetch_chunks(conn, union_scored)
    by_id = {c.chunk_id: c for c in chunks}

    dense_paths = [by_id[cid].source_path for cid, _ in dense[:final_k] if cid in by_id]
    hybrid_paths = [by_id[cid].source_path for cid, _ in fused[:final_k] if cid in by_id]

    rerank_input = [by_id[cid] for cid, _ in fused[: settings.rerank_candidates] if cid in by_id]
    reranked = await asyncio.to_thread(rerank, question, rerank_input, final_k)
    rerank_paths = [c.source_path for c in reranked]

    return {"dense": dense_paths, "hybrid": hybrid_paths, "hybrid_rerank": rerank_paths}


async def evaluate(cases: Sequence[Case], final_k: int) -> dict[Mode, dict[str, float]]:
    acc: dict[Mode, dict[str, list[float]]] = {m: {"hit": [], "rr": []} for m in MODES}

    # Una sola pasada del embedder para TODAS las queries: bge-m3 es mucho más eficiente
    # en batch que en N llamadas sueltas (era el cuello de botella en CPU).
    vectors = await asyncio.to_thread(embed_texts, [case.question for case in cases])

    async with await connect() as conn:
        for case, vector in zip(cases, vectors, strict=True):
            paths = await _paths_per_mode(conn, case.question, vector, final_k)
            for mode in MODES:
                acc[mode]["hit"].append(hit_at_k(paths[mode], case.relevant, final_k))
                acc[mode]["rr"].append(reciprocal_rank(paths[mode], case.relevant))
    return {mode: {"hit@k": mean(acc[mode]["hit"]), "mrr": mean(acc[mode]["rr"])} for mode in MODES}


def render_table(results: dict[Mode, dict[str, float]], k: int, n: int) -> str:
    lines = [
        f"_Generado el {datetime.now(UTC):%Y-%m-%d %H:%M UTC} · {n} casos · top_k={k}_",
        "",
        f"| Modo | hit@{k} | MRR |",
        "|---|---|---|",
    ]
    for mode in MODES:
        m = results[mode]
        lines.append(f"| {MODE_LABELS[mode]} | {m['hit@k']:.3f} | {m['mrr']:.3f} |")
    return "\n".join(lines)


def write_report(table: str, doc: Path) -> None:
    block = f"{_MARK_START}\n{table}\n{_MARK_END}"
    if doc.exists() and _MARK_START in doc.read_text(encoding="utf-8"):
        text = doc.read_text(encoding="utf-8")
        pre = text.split(_MARK_START)[0]
        post = text.split(_MARK_END)[1]
        doc.write_text(f"{pre}{block}{post}", encoding="utf-8")
    else:
        header = "# Resultados de evaluación\n\n## L1 · Retrieval (determinista)\n\n"
        doc.write_text(f"{header}{block}\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", type=Path, default=Path("evals/golden/retrieval/cases.yaml"))
    parser.add_argument("--report", type=Path, default=Path("docs/evals.md"))
    args = parser.parse_args()

    k = get_settings().top_k
    cases = load_cases(args.golden)
    results = await evaluate(cases, k)

    table = render_table(results, k, len(cases))
    print(table)
    write_report(table, args.report)

    dense_hit = results["dense"]["hit@k"]
    rerank_hit = results["hybrid_rerank"]["hit@k"]
    if rerank_hit < dense_hit:
        print(
            f"\n⚠ DoD F1 no cumplido: hit@{k} híbrido+rerank ({rerank_hit:.3f}) "
            f"< denso ({dense_hit:.3f}). Investigar antes de cerrar la fase."
        )
        return 1
    print(f"\n✔ DoD F1: hit@{k} híbrido+rerank ({rerank_hit:.3f}) ≥ denso ({dense_hit:.3f}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
