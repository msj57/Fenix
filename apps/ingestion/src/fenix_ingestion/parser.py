"""Parseo de documentos del corpus: frontmatter YAML + cuerpo markdown."""

import hashlib
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ParsedDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_path: str
    doc_type: Literal["runbook", "postmortem", "ticket"]
    lang: Literal["es", "en"]
    title: str = Field(min_length=1)
    services: tuple[str, ...] = ()
    body: str
    content_hash: str


def _split_frontmatter(raw: str, path: Path) -> tuple[dict[str, object], str]:
    if not raw.startswith("---\n"):
        raise ValueError(f"{path}: falta el frontmatter YAML inicial ('---')")
    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(f"{path}: frontmatter sin cierre ('---')")
    meta = yaml.safe_load(parts[0].removeprefix("---\n"))
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: el frontmatter debe ser un mapeo YAML")
    return meta, parts[1].strip()


def parse_document(path: Path, corpus_root: Path) -> ParsedDocument:
    raw = path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(raw, path)
    if not body:
        raise ValueError(f"{path}: documento sin cuerpo")
    try:
        return ParsedDocument(
            source_path=path.relative_to(corpus_root).as_posix(),
            doc_type=meta.get("doc_type"),  # type: ignore[arg-type]
            lang=meta.get("lang"),  # type: ignore[arg-type]
            title=meta.get("title"),  # type: ignore[arg-type]
            services=tuple(meta.get("services") or ()),  # type: ignore[arg-type]
            body=body,
            content_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )
    except ValidationError as exc:
        raise ValueError(f"{path}: frontmatter inválido — {exc}") from exc
