import pytest
fitz = pytest.importorskip("fitz")
from app.pdf.extractor import inspect_pdf, iter_pdf_pages


def test_pdf_extracts_text_incrementally(tmp_path):
    path = tmp_path / "example.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Offline PDF AI summarizer test")
    doc.save(path)
    doc.close()
    info = inspect_pdf(path)
    assert info.page_count == 1
    pages = list(iter_pdf_pages(path))
    assert pages[0][0] == 1
    assert "Offline PDF" in pages[0][1]
