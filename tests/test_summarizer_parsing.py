from app.ai.summarizer import _parse_structured, detect_language


def test_structured_output_parse():
    parsed = _parse_structured("SUMMARY\nA summary.\nKEY POINTS\n- One\nIMPORTANT CONCEPTS\n- Concept\nKEYWORDS\nPDF, AI")
    assert parsed["SUMMARY"] == "A summary."
    assert "One" in parsed["KEY POINTS"]
    assert "AI" in parsed["KEYWORDS"]


def test_markdown_headings_and_inline_content_parse():
    parsed = _parse_structured("### SUMMARY: Inline summary\n### KEY POINTS\n- Point\n### IMPORTANT CONCEPTS\n- Term\n### KEYWORDS: PDF, Local AI")
    assert parsed["SUMMARY"] == "Inline summary"
    assert parsed["KEY POINTS"] == "- Point"
    assert parsed["KEYWORDS"] == "PDF, Local AI"


def test_local_language_detection():
    assert detect_language("این یک متن فارسی برای آزمایش است") == "fa"
    assert detect_language("This is a short English paragraph about machine learning.") == "en"
    assert detect_language("这是一段用于测试的中文文本") == "zh"
