"""Embeddings densos con bge-m3 en CPU (§1: la VRAM es para Ollama).

El modelo se carga perezosamente y una sola vez por proceso: importar este
módulo es gratis; la primera llamada paga la carga (~2 GB de RAM).
"""

from functools import lru_cache
from typing import TYPE_CHECKING

from fenix_retrieval.config import get_settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def _model() -> "SentenceTransformer":
    from sentence_transformers import SentenceTransformer

    model: SentenceTransformer = SentenceTransformer(get_settings().embedding_model, device="cpu")
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeddings normalizados (la distancia coseno de pgvector lo asume)."""
    if not texts:
        return []
    vectors = _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [vector.tolist() for vector in vectors]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]


def count_tokens(text: str) -> int:
    """Tokens según el tokenizer real del modelo (lo usa el chunking en ingesta)."""
    return len(_model().tokenizer.encode(text))
