from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    """Conexión a Postgres. Reusa las mismas variables POSTGRES_* del compose."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    host: str = "localhost"
    port: int = 5432
    user: str = "fenix"
    password: str = ""
    db: str = "fenix"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RetrievalSettings(BaseSettings):
    """Parámetros del retrieval (prefijo FENIX_). Umbrales y modelos, nunca hardcodeados."""

    model_config = SettingsConfigDict(env_prefix="FENIX_", extra="ignore")

    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Dispositivo de embedder/reranker. Por defecto "cpu" (§1/ADR-009: la VRAM es para
    # Ollama en F2+). "auto" usa GPU si está disponible; útil en evals, donde Ollama no
    # compite por la VRAM. "cuda" la fuerza.
    device: str = "cpu"

    rrf_k: int = 60
    candidates_per_source: int = 20
    rerank_candidates: int = 20
    top_k: int = 5


@lru_cache(maxsize=1)
def get_pg_settings() -> PostgresSettings:
    return PostgresSettings()


@lru_cache(maxsize=1)
def get_settings() -> RetrievalSettings:
    return RetrievalSettings()


def resolve_device() -> str:
    """Resuelve el setting `device` a un dispositivo concreto para sentence-transformers.

    "auto" elige cuda si hay GPU visible, cpu en caso contrario. "cpu"/"cuda" se respetan
    tal cual. La importación de torch es perezosa para no pagarla si no hace falta.
    """
    device = get_settings().device
    if device != "auto":
        return device
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"
