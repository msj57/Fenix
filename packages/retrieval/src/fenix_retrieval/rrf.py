"""Reciprocal Rank Fusion: fusión de rankings sin calibrar pesos (ADR-001)."""

from collections import defaultdict
from collections.abc import Sequence


def rrf_fuse(rankings: Sequence[Sequence[int]], k: int = 60) -> list[tuple[int, float]]:
    """Fusiona rankings de IDs. score(id) = sum(1 / (k + rank_i)), rank 1-based.

    Devuelve [(id, score)] ordenado por score desc. Los IDs ausentes de un
    ranking simplemente no suman en él. Empates: orden estable por id asc.
    """
    if k < 1:
        raise ValueError("k debe ser >= 1")
    scores: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
