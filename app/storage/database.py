from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.utils.config import app_data_dir


class HistoryDatabase:
    """Local SQLite history. Source PDF contents are not saved by the application."""
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "history.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source_path TEXT NOT NULL,
                title TEXT NOT NULL,
                summary_type TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                result_json TEXT NOT NULL
            )""")

    def add(self, result: dict[str, Any]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO summaries(created_at,source_path,title,summary_type,page_count,result_json) VALUES(?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(timespec="seconds"), result.get("source_path", ""), result.get("title", ""), result.get("summary_type", "standard"), int(result.get("page_count", 0)), json.dumps(result, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id,created_at,source_path,title,summary_type,page_count FROM summaries ORDER BY id DESC LIMIT ?", (max(1, min(int(limit), 500)),)).fetchall()
            return [dict(row) for row in rows]

    def get(self, item_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT result_json FROM summaries WHERE id=?", (int(item_id),)).fetchone()
            if not row:
                return None
            value = json.loads(row["result_json"])
            value["history_id"] = int(item_id)
            return value

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM summaries")
