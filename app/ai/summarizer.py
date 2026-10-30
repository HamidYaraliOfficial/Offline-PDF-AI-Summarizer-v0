from __future__ import annotations

import json
import logging
import re
import tempfile
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from itertools import chain
from typing import Any, Callable

from app.ai.llm_engine import LocalLLM
from app.ai.prompts import chunk_system, final_system, make_chunk_prompt
from app.pdf.chunker import iter_text_chunks
from app.pdf.extractor import inspect_pdf, iter_pdf_pages

logger = logging.getLogger(__name__)
ProgressCallback = Callable[[int, str], None]


@dataclass
class SummaryResult:
    title: str
    source_path: str
    page_count: int
    language: str
    processing_seconds: float
    summary_type: str
    summary: str = ""
    key_points: str = ""
    important_concepts: str = ""
    keywords: str = ""
    chapter_summaries: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SummaryResult":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in value.items() if k in allowed})


def detect_language(text: str) -> str:
    """Simple local script detection with an optional langdetect fallback."""
    sample = text[:10000]
    persian = len(re.findall(r"[\u0600-\u06FF]", sample))
    chinese = len(re.findall(r"[\u4e00-\u9fff]", sample))
    latin = len(re.findall(r"[A-Za-z]", sample))
    if persian > max(5, latin // 3):
        return "fa"
    if chinese > max(5, latin // 3):
        return "zh"
    try:
        from langdetect import detect
        code = detect(sample)
        if code.startswith("fa"):
            return "fa"
        if code.startswith("zh"):
            return "zh"
    except Exception:
        pass
    return "en"


def _parse_structured(text: str) -> dict[str, str]:
    names = ["SUMMARY", "KEY POINTS", "IMPORTANT CONCEPTS", "KEYWORDS"]
    pattern = re.compile(
        r"(?im)^[ \t]*(?:#{1,6}[ \t]*)?(SUMMARY|KEY[ \t]+POINTS|IMPORTANT[ \t]+CONCEPTS|KEYWORDS)[ \t]*:?[ \t]*(.*?)[ \t]*$"
    )
    matches = list(pattern.finditer(text))
    parsed: dict[str, str] = {}
    for index, match in enumerate(matches):
        key = " ".join(match.group(1).upper().split())
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        inline_content = match.group(2).strip()
        following_content = text[match.end():end].strip()
        parsed[key] = "\n".join(part for part in (inline_content, following_content) if part).strip()
    if "SUMMARY" not in parsed or not parsed["SUMMARY"]:
        parsed["SUMMARY"] = text.strip()
    for name in names:
        parsed.setdefault(name, "")
    return parsed


class LocalSummarizer:
    def __init__(self, config: dict[str, Any], cancel_event: Any = None, progress: ProgressCallback | None = None) -> None:
        self.config = config
        self.cancel_event = cancel_event
        self.progress = progress or (lambda percent, message: None)
        self._last_progress = 0
        self.llm = LocalLLM(config)

    def _check_cancel(self) -> None:
        if self.cancel_event is not None and self.cancel_event.is_set():
            raise InterruptedError("Processing was cancelled by the user.")

    def _emit(self, percent: int, message: str) -> None:
        # Keep progress monotonic even when chunk-based and page-based estimates overlap.
        current = max(self._last_progress, max(0, min(100, int(percent))))
        self._last_progress = current
        self.progress(current, message)

    def summarize_pdf(self, path: str | Path, summary_type: str = "standard", output_language: str = "auto") -> SummaryResult:
        started = time.monotonic()
        info = inspect_pdf(path)
        if summary_type not in {"short", "standard", "detailed", "chapter"}:
            summary_type = "standard"
        settings_lang = output_language if output_language in {"fa", "en", "zh"} else "auto"
        self._emit(1, f"Opening PDF ({info.page_count} pages)…")
        if self.config.get("enable_ocr"):
            self._emit(3, "OCR is enabled; scanning pages locally when needed…")

        configured_chunk_chars = max(2500, int(self.config.get("summary_chunk_chars", 7000)))
        context_size = max(2048, int(self.config.get("context_size", 4096)))
        chunk_output_tokens = {"short": 280, "standard": 450, "detailed": 700, "chapter": 500}[summary_type]
        pages_iterator = iter_pdf_pages(
            info.path,
            enable_ocr=bool(self.config.get("enable_ocr", False)),
            tesseract_path=str(self.config.get("tesseract_path", "")),
            ocr_languages=str(self.config.get("ocr_languages", "fas+eng")),
        )
        # Track pages with no extractable text so mixed text/scanned PDFs are not silently presented as complete.
        textless_pages: list[int] = []
        def tracked_pages():
            for page_no, page_text in pages_iterator:
                if not page_text.strip():
                    textless_pages.append(page_no)
                yield page_no, page_text
        tracked_iterator = iter(tracked_pages())
        prefetched_pages: list[tuple[int, str]] = []
        sample_text = ""
        # Buffer only a few pages to estimate source language and a safer model-context chunk size.
        for _ in range(min(3, info.page_count)):
            try:
                page_record = next(tracked_iterator)
            except StopIteration:
                break
            prefetched_pages.append(page_record)
            if page_record[1].strip():
                sample_text += "\n" + page_record[1]
            if len(sample_text) >= 1000:
                break
        source_language_hint = detect_language(sample_text) if sample_text.strip() else "en"
        chars_per_token = {"en": 2.5, "fa": 1.8, "zh": 0.85}.get(source_language_hint, 1.8)
        available_input_tokens = max(700, context_size - chunk_output_tokens - 300)
        context_safe_chars = max(1000, int(available_input_tokens * chars_per_token))
        chunk_char_limit = min(configured_chunk_chars, context_safe_chars)
        chunks = iter_text_chunks(chain(prefetched_pages, tracked_iterator), chunk_char_limit, split_on_headings=(summary_type == "chapter"))
        chunk_summaries: list[tuple[str, str, int, int]] = []
        first_text = sample_text[:5000]
        total_chunks = 0
        seen_pages = 0
        # Intermediate text is kept in a temporary file and deleted automatically on exit.
        with tempfile.TemporaryDirectory(prefix="offline_pdf_ai_") as temp_dir:
            intermediate_file = Path(temp_dir) / "chunk_summaries.jsonl"
            with intermediate_file.open("w", encoding="utf-8") as out:
                # The page progress is inferred from chunk boundaries; empty image-only pages are still handled by extraction.
                for chunk in chunks:
                    self._check_cancel()
                    if not first_text:
                        first_text = chunk.text[:5000]
                    language = settings_lang if settings_lang != "auto" else detect_language(first_text or chunk.text)
                    total_chunks += 1
                    self._emit(min(70, 5 + total_chunks), f"Summarizing text chunk {total_chunks} (pages {chunk.start_page}-{chunk.end_page})…")
                    response = self.llm.generate(
                        chunk_system(language),
                        make_chunk_prompt(chunk.text, summary_type, chunk.chapter),
                        max_tokens=chunk_output_tokens,
                    )
                    row = {"chapter": chunk.chapter, "summary": response, "start_page": chunk.start_page, "end_page": chunk.end_page}
                    out.write(json.dumps(row, ensure_ascii=False) + "\n")
                    chunk_summaries.append((chunk.chapter, response, chunk.start_page, chunk.end_page))
                    seen_pages = max(seen_pages, chunk.end_page)
                    # Avoid giving the impression that page-level extraction progress is exact for sparse PDFs.
                    self._emit(min(72, 5 + int(67 * seen_pages / max(1, info.page_count))), f"Processed through page {seen_pages} / {info.page_count}")
            self._check_cancel()
            if not chunk_summaries:
                raise RuntimeError("No usable text could be extracted from this PDF. It may be scanned; enable local OCR in Settings and install Tesseract with the needed language packs.")
            language = settings_lang if settings_lang != "auto" else detect_language(first_text)
            self._emit(74, "Combining intermediate summaries…")
            condensed = [entry[1] for entry in chunk_summaries]
            # Reduce notes hierarchically without truncating intermediate content.
            max_reduce_chars = max(2500, int(self.config.get("context_size", 4096)) * 2)

            def reduce_note_list(items: list[str], instruction: str) -> str:
                current = list(items)
                for _round in range(20):
                    self._check_cancel()
                    if len("\n\n".join(current)) <= max_reduce_chars:
                        return "\n\n".join(current)
                    next_level: list[str] = []
                    batch: list[str] = []
                    batch_len = 0
                    for item in current:
                        if batch and batch_len + len(item) > max_reduce_chars:
                            next_level.append(self.llm.generate(chunk_system(language), instruction + "\n\n" + "\n\n".join(batch), max_tokens=650))
                            batch, batch_len = [], 0
                        batch.append(item)
                        batch_len += len(item)
                    if batch:
                        next_level.append(self.llm.generate(chunk_system(language), instruction + "\n\n" + "\n\n".join(batch), max_tokens=650))
                    if sum(map(len, next_level)) >= sum(map(len, current)):
                        raise RuntimeError("The local model did not reduce the intermediate notes. Try a smaller chunk size or a model with a larger context window.")
                    current = next_level
                raise RuntimeError("The document produced too many intermediate summaries. Try a smaller chunk size in Settings.")

            self._emit(74, "Combining intermediate summaries…")
            notes = reduce_note_list(
                condensed,
                "Combine these notes into a concise, faithful summary. Preserve important facts, numbers and caveats.",
            )
            self._check_cancel()
            self._emit(82, "Generating the final structured summary…")
            final_text = self.llm.generate(
                final_system(language),
                f"Document title: {info.title}\nPages: {info.page_count}\nSummary style: {summary_type}\n\nIntermediate notes:\n{notes}",
                max_tokens={"short": 550, "standard": 1000, "detailed": 1600, "chapter": 1000}[summary_type],
                temperature=0.15,
            )
            parsed = _parse_structured(final_text)
            # Recover missing structured fields rather than silently returning empty tabs.
            fallbacks = {
                "KEY POINTS": ("List the key points from these document notes as concise bullets. Output only the list:\n\n" + notes, 450),
                "IMPORTANT CONCEPTS": ("List important concepts from these document notes with one-line explanations. Output only the list:\n\n" + notes, 500),
                "KEYWORDS": ("Return 5-15 important keywords or phrases from these document notes, comma-separated. Output only the keywords:\n\n" + notes, 180),
            }
            for key, (prompt, token_limit) in fallbacks.items():
                if not parsed.get(key, "").strip():
                    parsed[key] = self.llm.generate(chunk_system(language), prompt, max_tokens=token_limit, temperature=0.1)
            chapter_summaries: list[dict[str, str]] = []
            if summary_type == "chapter":
                grouped: dict[str, list[str]] = defaultdict(list)
                for chapter, summary, start, end in chunk_summaries:
                    grouped[chapter].append(summary)
                groups = list(grouped.items())[:30]
                for idx, (chapter, items) in enumerate(groups, start=1):
                    self._check_cancel()
                    text = reduce_note_list(
                        items,
                        f"Combine these notes from the chapter/section '{chapter}' into concise notes without losing important facts.",
                    )
                    chapter_summary = self.llm.generate(
                        chunk_system(language),
                        f"Summarize the chapter/section named '{chapter}' faithfully.\n\n{text}",
                        max_tokens=380,
                    )
                    chapter_summaries.append({"title": chapter, "summary": chapter_summary})
                    self._emit(min(98, 88 + int(10 * idx / max(1, len(groups)))), f"Summarizing section {idx} / {len(groups)}…")
            self._check_cancel()
            self._emit(100, "Summary complete.")
            return SummaryResult(
                title=info.title,
                source_path=info.path,
                page_count=info.page_count,
                language=language,
                processing_seconds=round(time.monotonic() - started, 2),
                summary_type=summary_type,
                summary=parsed.get("SUMMARY", "").strip() or final_text,
                key_points=parsed.get("KEY POINTS", "").strip(),
                important_concepts=parsed.get("IMPORTANT CONCEPTS", "").strip(),
                keywords=parsed.get("KEYWORDS", "").strip(),
                chapter_summaries=chapter_summaries,
                warnings=( ["No extractable text was found on page(s): " + ", ".join(map(str, textless_pages[:100])) + (" …" if len(textless_pages) > 100 else "") + ". These pages may be blank or scanned. Enable local OCR in Settings if they contain important content."] if textless_pages else [] ),
            )

    def close(self) -> None:
        self.llm.close()
