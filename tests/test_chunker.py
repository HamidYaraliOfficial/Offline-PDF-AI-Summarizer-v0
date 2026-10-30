from app.pdf.chunker import iter_text_chunks, is_heading


def test_chunks_respect_maximum_size():
    text = " ".join(["earth observation"] * 600)
    chunks = list(iter_text_chunks([(1, text)], max_chars=1200))
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 1200 for chunk in chunks)
    assert "earth" in chunks[0].text


def test_heading_detection():
    assert is_heading("Chapter 1 Introduction")
    assert is_heading("3.2 Data Preparation")
    assert not is_heading("This is a normal sentence with a full stop.")


def test_empty_pages_produce_no_chunks():
    assert list(iter_text_chunks([(1, ""), (2, "   ")], max_chars=1000)) == []
