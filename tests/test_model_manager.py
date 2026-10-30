from app.ai.model_manager import resolve_model_path, model_status


def test_resolve_single_local_gguf_model(tmp_path, monkeypatch):
    import app.ai.model_manager as manager
    models = tmp_path / "models"
    models.mkdir()
    model = models / "local-instruct.gguf"
    model.write_bytes(b"test marker; not a real model")
    monkeypatch.setattr(manager, "models_directory", lambda: models)
    assert manager.resolve_model_path("") == model.resolve()
    assert manager.model_status("")[0] is True
    assert manager.resolve_model_path(str(tmp_path / "missing.gguf")) is None


def test_no_model_returns_clear_status(tmp_path, monkeypatch):
    import app.ai.model_manager as manager
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setattr(manager, "models_directory", lambda: models)
    assert manager.model_status("")[0] is False
    assert "Model not found" in manager.model_status("")[1]
