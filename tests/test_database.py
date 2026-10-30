from app.storage.database import HistoryDatabase


def test_history_roundtrip(tmp_path):
    db = HistoryDatabase(tmp_path / "history.sqlite3")
    result = {"title": "Example", "source_path": "C:/test.pdf", "summary_type": "standard", "page_count": 3,
              "language": "en", "processing_seconds": 1.0, "summary": "A test summary", "key_points": "- one",
              "important_concepts": "concept", "keywords": "test", "chapter_summaries": []}
    item_id = db.add(result)
    assert item_id > 0
    assert db.get(item_id)["summary"] == "A test summary"
    assert db.list_recent()[0]["title"] == "Example"
    db.clear()
    assert db.list_recent() == []
