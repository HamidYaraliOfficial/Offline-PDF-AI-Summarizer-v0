from app.utils.config import ConfigManager


def test_config_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    config = ConfigManager(path)
    config.save({"cpu_threads": 3, "enable_ocr": True})
    loaded = ConfigManager(path)
    assert loaded.get("cpu_threads") == 3
    assert loaded.get("enable_ocr") is True
    assert "model_path" in loaded.data
