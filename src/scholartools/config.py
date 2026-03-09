import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, computed_field

CONFIG_PATH = Path.home() / ".config" / "scholartools" / "config.json"


class LocalSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    library_dir: Path = Field(
        default_factory=lambda: Path.home() / ".local/share/scholartools"
    )

    @computed_field
    @property
    def library_file(self) -> Path:
        return self.library_dir / "library.json"

    @computed_field
    @property
    def files_dir(self) -> Path:
        return self.library_dir / "files"


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    enabled: bool = True
    email: str | None = None


def _default_sources() -> list[SourceConfig]:
    return [
        SourceConfig(name="crossref"),
        SourceConfig(name="semantic_scholar"),
        SourceConfig(name="arxiv"),
        SourceConfig(name="latindex"),
        SourceConfig(name="google_books"),
    ]


class ApiSettings(BaseModel):
    sources: list[SourceConfig] = Field(default_factory=_default_sources)


class LlmSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = "claude-sonnet-4-6"


class Settings(BaseModel):
    backend: str = "local"
    local: LocalSettings = Field(default_factory=LocalSettings)
    apis: ApiSettings = Field(default_factory=ApiSettings)
    llm: LlmSettings = Field(default_factory=LlmSettings)


_settings: Settings | None = None


def load_settings() -> Settings:
    global _settings
    if _settings is not None:
        return _settings
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            Settings().model_dump_json(
                indent=2, exclude={"local": {"library_file", "files_dir"}}
            )
        )
    _settings = Settings.model_validate(json.loads(CONFIG_PATH.read_text()))
    return _settings


def reset_settings() -> None:
    global _settings
    _settings = None
