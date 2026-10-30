from __future__ import annotations

from pathlib import Path
from app.utils.config import project_root


def models_directory() -> Path:
    path = project_root() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_gguf_models() -> list[Path]:
    return sorted(models_directory().glob("*.gguf"), key=lambda p: p.name.lower())


def resolve_model_path(configured_path: str | None) -> Path | None:
    if configured_path and str(configured_path).strip():
        path = Path(str(configured_path).strip()).expanduser()
        if path.is_file() and path.suffix.lower() == ".gguf":
            return path.resolve()
        return None
    candidates = find_gguf_models()
    return candidates[0].resolve() if len(candidates) == 1 else None


def model_status(configured_path: str | None) -> tuple[bool, str]:
    model = resolve_model_path(configured_path)
    if model:
        return True, f"Ready: {model.name}"
    return False, "Model not found. Select a GGUF model in Settings or place one in the models folder."
