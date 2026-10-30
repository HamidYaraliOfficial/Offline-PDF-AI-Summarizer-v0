from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PDFInfo:
    path: str
    title: str
    page_count: int
    file_size: int
    metadata: dict


def inspect_pdf(path: str | Path) -> PDFInfo:
    """Validate a PDF and return metadata without reading the whole document into memory."""
    pdf_path = Path(path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Please choose a file with the .pdf extension.")
    try:
        with fitz.open(pdf_path) as doc:
            if doc.is_encrypted:
                raise ValueError("This PDF is encrypted or password-protected. Unlock it before summarizing.")
            if len(doc) < 1:
                raise ValueError("The PDF has no pages.")
            metadata = dict(doc.metadata or {})
            title = str(metadata.get("title") or pdf_path.stem).strip() or pdf_path.stem
            return PDFInfo(str(pdf_path.resolve()), title, len(doc), pdf_path.stat().st_size, metadata)
    except fitz.FileDataError as exc:
        raise ValueError("This PDF appears to be damaged or is not a valid PDF file.") from exc


def iter_pdf_pages(
    path: str | Path,
    *,
    enable_ocr: bool = False,
    tesseract_path: str = "",
    ocr_languages: str = "fas+eng",
    min_text_chars: int = 20,
) -> Iterator[tuple[int, str]]:
    """Yield (1-based page number, text) incrementally; OCR is used only for near-empty pages when enabled."""
    from app.pdf.ocr import extract_page_ocr

    pdf_path = Path(path)
    try:
        with fitz.open(pdf_path) as doc:
            if doc.is_encrypted:
                raise ValueError("This PDF is encrypted or password-protected.")
            for index, page in enumerate(doc):
                text = page.get_text("text", sort=True) or ""
                text = text.replace("\x00", " ").strip()
                if len(text) < min_text_chars and enable_ocr:
                    try:
                        ocr_text = extract_page_ocr(page, tesseract_path, ocr_languages)
                        if ocr_text.strip():
                            text = ocr_text.strip()
                    except Exception:
                        logger.exception("OCR failed on page %s", index + 1)
                        raise
                yield index + 1, text
    except fitz.FileDataError as exc:
        raise ValueError("This PDF appears to be damaged or is not a valid PDF file.") from exc
