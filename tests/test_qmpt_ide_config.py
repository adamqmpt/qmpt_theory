from pathlib import Path

from code.qmpt_ide.config import IDEConfig, load_config, default_config_path


def test_default_config_path_exists() -> None:
    path = default_config_path()
    assert path.is_file()


def test_load_default_config() -> None:
    cfg = load_config()
    assert isinstance(cfg, IDEConfig)
    assert cfg.title.startswith("QMPT")
    assert cfg.window_width > 0
    assert cfg.window_height > 0
    # ensure theme merged with defaults
    assert "bg" in cfg.theme


def test_load_custom_config(tmp_path: Path) -> None:
    config_path = tmp_path / "custom.json"
    config_path.write_text('{"title": "Custom IDE", "window_width": 900}', encoding="utf-8")
    cfg = load_config(config_path)
    assert cfg.title == "Custom IDE"
    assert cfg.window_width == 900
    # fallback keys should remain present
    assert "accent" in cfg.theme
