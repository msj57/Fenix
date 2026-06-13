"""Acceso a Postgres compartido por retrieval e ingesta."""

from importlib.resources import files
from typing import Any

import psycopg

from fenix_retrieval.config import get_pg_settings


def vector_literal(vector: list[float]) -> str:
    """Serializa un embedding al literal textual de pgvector ('[0.1,0.2,...]').

    Evita depender del adaptador pgvector-python: el cast `%s::vector` en SQL
    hace el resto.
    """
    return "[" + ",".join(repr(value) for value in vector) + "]"


async def connect() -> psycopg.AsyncConnection[Any]:
    return await psycopg.AsyncConnection.connect(get_pg_settings().dsn)


async def apply_schema(conn: psycopg.AsyncConnection[Any]) -> None:
    """Aplica el schema (idempotente). Se invoca en cada ingesta."""
    schema = (files("fenix_retrieval") / "sql" / "001-schema.sql").read_text(encoding="utf-8")
    await conn.execute(schema)
    await conn.commit()
