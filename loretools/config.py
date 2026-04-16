import json
from pathlib import Path

from loretools.models import (
    Settings,
)

_settings: Settings | None = None

_REQUIRED_KEYS = {"local"}

_LOCAL_COMPUTED = {
    "library_file",
    "files_dir",
    "staging_file",
    "staging_dir",
}


def _config_dir() -> Path:
    return Path.cwd() / ".lore"


def load_settings() -> Settings:
    global _settings
    if _settings is not None:
        return _settings
    config_path = _config_dir() / "config.json"
    if not config_path.exists():
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                Settings().model_dump_json(indent=2, exclude={"local": _LOCAL_COMPUTED})
            )
        except OSError as e:
            raise FileNotFoundError(
                f"Cannot create config at {config_path}: {e}. "
                "Run loretools from a writable collection directory."
            ) from e
    data = json.loads(config_path.read_text())
    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(
            f"Config file at {config_path} is incomplete. "
            f"Missing required keys: {sorted(missing)}. "
            "Please add them or delete the file to regenerate defaults."
        )
    _settings = Settings.model_validate(data)
    return _settings


def reset_settings() -> None:
    global _settings
    _settings = None
