from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

APP_NAME = "OfflinePDFSummarizer"


def app_data_dir() -> Path:
    """Return a writable per-user application data directory."""
    root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    base = Path(root) if root else Path.home() / ".local" / "share"
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_root() -> Path:
    # In a frozen PyInstaller build, keep the user-managed models folder beside the EXE.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def default_config() -> dict[str, Any]:
    return {
        "model_path": "",
        "cpu_threads": max(1, (os.cpu_count() or 4) - 1),
        "context_size": 4096,
        "gpu_layers": 0,
        "enable_ocr": False,
        "tesseract_path": "",
        "ocr_languages": "fas+eng",
        "output_directory": str(Path.home() / "Documents" / "PDF Summaries"),
        "theme": "System",
        "summary_chunk_chars": 7000,
    }


class ConfigManager:
    """Small JSON settings store. Configuration is always local."""
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "settings.json")
        self.data = default_config()
        self.load()

    def load(self) -> dict[str, Any]:
        if self.path.is_file():
            try:
                stored = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    self.data.update(stored)
            except (OSError, json.JSONDecodeError):
                # Keep safe defaults when a config file is damaged.
                pass
        return self.data

    def save(self, updates: dict[str, Any] | None = None) -> None:
        if updates:
            self.data.update(updates)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
