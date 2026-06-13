"""Métricas de retrieval deterministas (sin LLM): hit@k y MRR.

Un chunk recuperado cuenta como relevante si su `source_path` está en el conjunto
dorado del caso. Anclar la relevancia al documento (source_path) —y no al chunk_id,
que Postgres reasigna en cada reingesta, ni al heading_path, que depende de la
estrategia de chunking— mantiene el golden set estable cuando se reingesta o se
recalibra el chunking. La pregunta que mide retrieval es "¿recuperé el documento
correcto?", no "¿qué sección exacta?".
"""

from collections.abc import Sequence


def hit_at_k(retrieved_paths: Sequence[str], relevant: set[str], k: int) -> float:
    """1.0 si algún documento relevante aparece en el top-k recuperado, 0.0 si no."""
    return 1.0 if any(path in relevant for path in retrieved_paths[:k]) else 0.0


def reciprocal_rank(retrieved_paths: Sequence[str], relevant: set[str]) -> float:
    """1/rango del primer documento relevante (rango 1-based); 0.0 si ninguno aparece.

    Se cuenta el primer rango en el que aparece un documento relevante, deduplicando
    documentos repetidos (varios chunks del mismo doc no mejoran el rango).
    """
    seen: set[str] = set()
    rank = 0
    for path in retrieved_paths:
        if path in seen:
            continue
        seen.add(path)
        rank += 1
        if path in relevant:
            return 1.0 / rank
    return 0.0


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0
