import json

from scholartools.models import Settings


def test_settings_without_sync_block():
    data = {
        "backend": "local",
        "local": {"library_dir": "/tmp/lib"},
        "apis": {},
        "llm": {},
        "citekey": {},
    }
    s = Settings.model_validate(data)
    assert s.sync is None


def test_settings_with_sync_block():
    data = {
        "backend": "local",
        "local": {"library_dir": "/tmp/lib"},
        "apis": {},
        "llm": {},
        "citekey": {},
        "sync": {
            "endpoint": "http://minio:9000",
            "bucket": "mybucket",
            "access_key": "acc",
            "secret_key": "sec",
        },
    }
    s = Settings.model_validate(data)
    assert s.sync is not None
    assert s.sync.bucket == "mybucket"
    assert s.sync.endpoint == "http://minio:9000"


def test_ctx_uses_local_adapter_without_sync(tmp_path, monkeypatch):
    import scholartools
    from scholartools.models import Settings

    config_path = tmp_path / "config.json"
    config_path.write_text(
        Settings().model_dump_json(
            indent=2,
            exclude={
                "local": {
                    "library_file",
                    "files_dir",
                    "staging_file",
                    "staging_dir",
                    "peers_dir",
                }
            },
        )
    )
    monkeypatch.setattr("scholartools.config.CONFIG_PATH", config_path)
    scholartools.reset()

    ctx = scholartools._build_ctx()
    assert ctx.sync_config is None


def test_ctx_uses_sync_adapter_with_sync_block(tmp_path, monkeypatch):
    import scholartools
    from scholartools.models import Settings

    settings = Settings()
    data = json.loads(
        settings.model_dump_json(
            exclude={
                "local": {
                    "library_file",
                    "files_dir",
                    "staging_file",
                    "staging_dir",
                    "peers_dir",
                }
            }
        )
    )
    data["sync"] = {
        "endpoint": "http://localhost:9000",
        "bucket": "test",
        "access_key": "a",
        "secret_key": "s",
    }

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data))
    monkeypatch.setattr("scholartools.config.CONFIG_PATH", config_path)
    scholartools.reset()

    ctx = scholartools._build_ctx()
    assert ctx.sync_config is not None
    assert ctx.sync_config.bucket == "test"
