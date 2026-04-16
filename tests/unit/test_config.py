import json
from pathlib import Path

import pytest

from loretools.config import load_settings, reset_settings
from loretools.models import LocalSettings


@pytest.fixture(autouse=True)
def clear_settings():
    reset_settings()
    yield
    reset_settings()


def test_defaults_when_no_config_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    s = load_settings()
    assert s.backend == "local"
    config_path = tmp_path / ".loretools" / "config.json"
    assert config_path.exists()
    data = json.loads(config_path.read_text())
    assert "local" in data


def test_loads_from_existing_config_file(tmp_path, monkeypatch):
    library_dir = str(tmp_path / "mylib")
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".loretools"
    config_dir.mkdir()
    config_path = config_dir / "config.json"
    config = {
        "backend": "local",
        "local": {"library_dir": library_dir},
    }
    config_path.write_text(json.dumps(config))
    s = load_settings()
    assert s.local.library_dir == Path(library_dir)
    assert s.local.library_file == Path(library_dir) / "library.json"
    assert s.local.files_dir == Path(library_dir) / "files"


def test_library_dir_derives_paths(tmp_path):
    ls = LocalSettings(library_dir=tmp_path / "mylib")
    assert ls.library_file == tmp_path / "mylib" / "library.json"
    assert ls.files_dir == tmp_path / "mylib" / "files"


def test_settings_cached(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    s1 = load_settings()
    s2 = load_settings()
    assert s1 is s2


def test_partial_config_raises_with_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".loretools"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(json.dumps({"backend": "local"}))
    with pytest.raises(ValueError, match="incomplete"):
        load_settings()
