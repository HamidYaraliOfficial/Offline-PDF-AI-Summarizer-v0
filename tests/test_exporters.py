from pathlib import Path
from app.export.txt import save_txt
from app.export.markdown import save_markdown
from app.export.docx import save_docx


def test_text_markdown_and_docx_exports(tmp_path):
    result = {
        "title": "Demo PDF", "page_count": 2, "language": "en", "processing_seconds": 2.4,
        "summary": "A real local summary.", "key_points": "- Point one", "important_concepts": "Concept A",
        "keywords": "PDF, AI", "chapter_summaries": [{"title": "Chapter 1", "summary": "Section text"}],
        "warnings": ["Page 2 may be scanned."],
    }
    txt = tmp_path / "summary.txt"
    md = tmp_path / "summary.md"
    docx = tmp_path / "summary.docx"
    save_txt(result, txt)
    save_markdown(result, md)
    save_docx(result, docx)
    assert "A real local summary." in txt.read_text(encoding="utf-8")
    assert "## Chapter Summaries" in md.read_text(encoding="utf-8")
    assert docx.stat().st_size > 1000
