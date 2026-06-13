"""Chunking por estructura de headers markdown (objetivo 400-600 tokens, solape ~12%).

El contador de tokens se inyecta: el pipeline usa el tokenizer real de bge-m3;
los tests usan un contador trivial (sin descargar modelos).
"""

import re
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict

TokenCounter = Callable[[str], int]

_HEADER_RE = re.compile(r"^(#{1,3})\s+(.*)$")


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    heading_path: str
    content: str
    token_count: int


class _Section(BaseModel):
    heading_path: str
    text: str


def _split_sections(body: str) -> list[_Section]:
    sections: list[_Section] = []
    stack: list[tuple[int, str]] = []
    lines: list[str] = []

    def flush() -> None:
        text = "\n".join(lines).strip()
        if text:
            path = " > ".join(title for _, title in stack)
            sections.append(_Section(heading_path=path, text=text))
        lines.clear()

    for line in body.splitlines():
        match = _HEADER_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, match.group(2).strip()))
        else:
            lines.append(line)
    flush()
    return sections


def _merge_small(sections: list[_Section], count: TokenCounter, target: int) -> list[_Section]:
    merged: list[_Section] = []
    for section in sections:
        if merged and count(merged[-1].text) + count(section.text) <= target:
            previous = merged[-1]
            merged[-1] = _Section(
                heading_path=previous.heading_path,
                text=f"{previous.text}\n\n{section.text}",
            )
        else:
            merged.append(section)
    return merged


def _split_long(
    section: _Section, count: TokenCounter, target: int, overlap: int
) -> list[_Section]:
    paragraphs = [p for p in re.split(r"\n\s*\n", section.text) if p.strip()]
    windows: list[_Section] = []
    current: list[str] = []

    def emit() -> None:
        if current:
            windows.append(_Section(heading_path=section.heading_path, text="\n\n".join(current)))

    for paragraph in paragraphs:
        if current and count("\n\n".join([*current, paragraph])) > target:
            emit()
            tail: list[str] = []
            for previous in reversed(current):
                if count("\n\n".join([previous, *tail])) > overlap:
                    break
                tail.insert(0, previous)
            current = tail
        current.append(paragraph)
    emit()
    return windows


def chunk_markdown(
    body: str,
    count_tokens: TokenCounter,
    target_tokens: int = 500,
    overlap_ratio: float = 0.12,
) -> list[Chunk]:
    """Trocea un cuerpo markdown en chunks coherentes con su ruta de headers."""
    overlap = int(target_tokens * overlap_ratio)
    sections = _merge_small(_split_sections(body), count_tokens, target_tokens)
    chunks: list[Chunk] = []
    for section in sections:
        pieces = (
            _split_long(section, count_tokens, target_tokens, overlap)
            if count_tokens(section.text) > target_tokens
            else [section]
        )
        chunks.extend(
            Chunk(
                heading_path=piece.heading_path,
                content=piece.text,
                token_count=count_tokens(piece.text),
            )
            for piece in pieces
        )
    return chunks
