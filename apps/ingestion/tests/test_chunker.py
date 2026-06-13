from fenix_ingestion.chunker import chunk_markdown


def count_words(text: str) -> int:
    return len(text.split())


def test_small_doc_single_chunk() -> None:
    body = "# Título\n\nUn párrafo corto."
    chunks = chunk_markdown(body, count_words, target_tokens=100)
    assert len(chunks) == 1
    assert chunks[0].heading_path == "Título"
    assert chunks[0].token_count == count_words(chunks[0].content)


def test_heading_path_nested() -> None:
    body = (
        "# Runbook\n\n"
        + "intro " * 60
        + "\n\n## Diagnóstico\n\n"
        + "palabra " * 60
        + "\n\n### Logs\n\n"
        + "log " * 60
    )
    chunks = chunk_markdown(body, count_words, target_tokens=50)
    paths = [chunk.heading_path for chunk in chunks]
    assert "Runbook" in paths
    assert "Runbook > Diagnóstico" in paths
    assert "Runbook > Diagnóstico > Logs" in paths


def test_sibling_header_resets_stack() -> None:
    body = "## A\n\ntexto a\n\n## B\n\ntexto b"
    chunks = chunk_markdown(body, count_words, target_tokens=2)
    assert [chunk.heading_path for chunk in chunks] == ["A", "B"]


def test_small_sections_merge() -> None:
    body = "## A\n\nuno dos\n\n## B\n\ntres cuatro"
    chunks = chunk_markdown(body, count_words, target_tokens=100)
    assert len(chunks) == 1
    assert chunks[0].heading_path == "A"


def test_long_section_splits_with_overlap() -> None:
    paragraphs = [f"p{i} " + "palabra " * 19 for i in range(6)]
    body = "## Larga\n\n" + "\n\n".join(paragraphs)
    chunks = chunk_markdown(body, count_words, target_tokens=45, overlap_ratio=0.5)
    assert len(chunks) > 1
    assert all(chunk.token_count <= 45 for chunk in chunks)
    first_tail = chunks[0].content.split("\n\n")[-1]
    assert first_tail in chunks[1].content


def test_text_before_first_header() -> None:
    body = "preámbulo sin header\n\n# Título\n\ncuerpo"
    chunks = chunk_markdown(body, count_words, target_tokens=2)
    assert chunks[0].heading_path == ""
    assert "preámbulo" in chunks[0].content
