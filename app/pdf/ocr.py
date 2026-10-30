from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_page_ocr(page: Any, tesseract_path: str = "", languages: str = "fas+eng", dpi: int = 200) -> str:
    """Run local Tesseract OCR on a PyMuPDF page. Requires Tesseract and language data installed locally."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
        from io import BytesIO
    except ImportError as exc:
        raise RuntimeError("OCR dependencies are missing. Install pytesseract and Pillow, then install Tesseract locally.") from exc
    if tesseract_path.strip():
        executable = Path(tesseract_path.strip())
        if not executable.is_file():
            raise RuntimeError(f"Configured Tesseract executable was not found: {executable}")
        pytesseract.pytesseract.tesseract_cmd = str(executable)
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
    image = Image.open(BytesIO(pix.tobytes("png")))
    try:
        return pytesseract.image_to_string(image, lang=languages or "eng")
    except Exception as exc:
        raise RuntimeError("Tesseract OCR failed. Check Tesseract installation and its language packs (for example, fas and eng).") from exc
