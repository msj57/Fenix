"""Cross-encoder bge-reranker-v2-m3 en CPU, carga perezosa (como embedder)."""

from functools import lru_cache
from typing import TYPE_CHECKING

from fenix_retrieval.config import get_settings
from fenix_retrieval.models import ChunkResult

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder


@lru_cache(maxsize=1)
def _model() -> "CrossEncoder":
    from sentence_transformers import CrossEncoder

    model: CrossEncoder = CrossEncoder(get_settings().reranker_model, device="cpu")
    return model


def rerank(query: str, candidates: list[ChunkResult], top_k: int) -> list[ChunkResult]:
    """Reordena candidatos por relevancia query-chunk y corta a top_k.

    El score del cross-encoder sustituye al score RRF en los resultados.
    """
    if not candidates:
        return []
    pairs = [(query, chunk.content) for chunk in candidates]
    # El stub multimodal de CrossEncoder.predict no resuelve el caso texto-texto
    # con list invariante; en runtime es la firma correcta.
    scores = _model().predict(pairs, show_progress_bar=False, convert_to_numpy=True)  # type: ignore[arg-type]
    rescored = [
        chunk.model_copy(update={"score": float(score)})
        for chunk, score in zip(candidates, scores, strict=True)
    ]
    rescored.sort(key=lambda chunk: chunk.score, reverse=True)
    return rescored[:top_k]
