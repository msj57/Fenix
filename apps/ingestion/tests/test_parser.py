from pathlib import Path

import pytest

from fenix_ingestion.parser import parse_document

VALID = """---
title: "Diagnóstico de 502 en nginx"
doc_type: runbook
lang: es
services: [nginx, webapp]
---

## Síntomas

La web devuelve 502.
"""


def write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "runbooks" / "rb-001.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_document(tmp_path: Path) -> None:
    doc = parse_document(write(tmp_path, VALID), tmp_path)
    assert doc.source_path == "runbooks/rb-001.md"
    assert doc.doc_type == "runbook"
    assert doc.lang == "es"
    assert doc.services == ("nginx", "webapp")
    assert doc.body.startswith("## Síntomas")
    assert len(doc.content_hash) == 64


def test_hash_changes_with_content(tmp_path: Path) -> None:
    first = parse_document(write(tmp_path, VALID), tmp_path)
    second = parse_document(write(tmp_path, VALID + "\nMás texto."), tmp_path)
    assert first.content_hash != second.content_hash


def test_missing_frontmatter(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="frontmatter"):
        parse_document(write(tmp_path, "# Sin frontmatter\n\ntexto"), tmp_path)


def test_invalid_doc_type(tmp_path: Path) -> None:
    bad = VALID.replace("doc_type: runbook", "doc_type: poema")
    with pytest.raises(ValueError, match="inválido"):
        parse_document(write(tmp_path, bad), tmp_path)


def test_empty_body(tmp_path: Path) -> None:
    headless = VALID.split("## Síntomas")[0]
    with pytest.raises(ValueError, match="sin cuerpo"):
        parse_document(write(tmp_path, headless), tmp_path)
