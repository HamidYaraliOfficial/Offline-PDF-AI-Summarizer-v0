import pytest
fitz = pytest.importorskip("fitz")

import app.ai.summarizer as summarizer_module
from app.ai.summarizer import LocalSummarizer


class FakeLLM:
    """Deterministic test double; production code always uses the local llama.cpp runtime."""
    def __init__(self, config):
        self.closed = False

    def generate(self, system_prompt, user_prompt, max_tokens=700, temperature=0.2):
        if "Output exactly these four headings" in system_prompt:
            return (
                "SUMMARY\nA faithful test summary.\n"
                "KEY POINTS\n- Main point\n"
                "IMPORTANT CONCEPTS\n- PDF extraction: reading document text\n"
                "KEYWORDS\nPDF, local AI"
            )
        return "A concise intermediate summary of the supplied text."

    def close(self):
        self.closed = True


def test_summarizer_pipeline_without_model_weights(tmp_path, monkeypatch):
    path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "This document explains local PDF processing and offline AI. It uses text extraction.")
    doc.new_page()  # Empty page should be reported rather than silently hidden.
    doc.save(path)
    doc.close()

    monkeypatch.setattr(summarizer_module, "LocalLLM", FakeLLM)
    progress = []
    worker = LocalSummarizer({"summary_chunk_chars": 2500, "context_size": 4096, "model_path": ""}, progress=lambda n, m: progress.append((n, m)))
    result = worker.summarize_pdf(path, "standard", "en")
    worker.close()

    assert result.page_count == 2
    assert result.summary == "A faithful test summary."
    assert "Main point" in result.key_points
    assert result.warnings and "page(s): 2" in result.warnings[0]
    assert progress[-1][0] == 100
