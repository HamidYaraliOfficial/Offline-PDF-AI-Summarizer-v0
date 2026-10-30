from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass
class TextChunk:
    text: str
    start_page: int
    end_page: int
    chapter: str
    index: int


_CHAPTER_RE = re.compile(
    r"^(?:(?:chapter|section|part|فصل|بخش)\s+(?:\d+|[ivxlcdm]+|[\wآ-ی]+)(?:[\s:—–.-]+.{1,90})?|\d+(?:\.\d+)*[.)]?\s+.{3,90})$",
    re.IGNORECASE,
)


def is_heading(line: str) -> bool:
    value = " ".join(line.strip().split())
    if not value or len(value) > 100 or len(value) < 4:
        return False
    if _CHAPTER_RE.match(value):
        return True
    letters = [c for c in value if c.isalpha()]
    if len(letters) > 8 and len(value) < 72:
        uppercase = sum(1 for c in letters if c.isupper())
        return uppercase / len(letters) > 0.82
    return False


def iter_text_chunks(
    pages: Iterable[tuple[int, str]], max_chars: int = 7000, split_on_headings: bool = False
) -> Iterator[TextChunk]:
    """Create bounded chunks from a page stream; no full-document text copy is required."""
    max_chars = max(1000, int(max_chars))
    buffer: list[str] = []
    buffer_len = 0
    start_page = 1
    end_page = 1
    chapter = "Document"
    chunk_index = 0

    def make_chunk(text: str, start: int, end: int, section: str, idx: int) -> TextChunk:
        return TextChunk(text=text.strip(), start_page=start, end_page=end, chapter=section, index=idx)

    for page_no, page_text in pages:
        if not page_text or not page_text.strip():
            continue
        for raw_line in page_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if split_on_headings and is_heading(line):
                if buffer:
                    chunk_index += 1
                    yield make_chunk("\n".join(buffer), start_page, end_page, chapter, chunk_index)
                    buffer, buffer_len = [], 0
                chapter = line[:100]
                continue
            # Long individual lines are split to avoid an oversized model prompt.
            while len(line) > max_chars:
                piece, line = line[:max_chars], line[max_chars:]
                if buffer:
                    chunk_index += 1
                    yield make_chunk("\n".join(buffer), start_page, end_page, chapter, chunk_index)
                    buffer, buffer_len = [], 0
                chunk_index += 1
                yield make_chunk(piece, page_no, page_no, chapter, chunk_index)
            if buffer_len + len(line) + 1 > max_chars and buffer:
                chunk_index += 1
                yield make_chunk("\n".join(buffer), start_page, end_page, chapter, chunk_index)
                buffer, buffer_len = [], 0
            if not buffer:
                start_page = page_no
            end_page = page_no
            buffer.append(line)
            buffer_len += len(line) + 1
    if buffer:
        chunk_index += 1
        yield make_chunk("\n".join(buffer), start_page, end_page, chapter, chunk_index)
