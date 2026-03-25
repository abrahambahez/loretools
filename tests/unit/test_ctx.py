import pytest


@pytest.fixture(autouse=True)
def reset_ctx(tmp_path, monkeypatch):
    import scholartools
    from scholartools.models import Settings

    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".scholartools"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
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
    scholartools.reset()
    yield
    scholartools.reset()


def test_anthropic_key_populates_llm_extract(monkeypatch):
    import scholartools

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-anthropic")
    monkeypatch.delenv("GBOOKS_API_KEY", raising=False)
    ctx = scholartools._build_ctx()
    assert ctx.llm_extract is not None


def test_no_anthropic_key_disables_llm_extract(monkeypatch):
    import scholartools

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ctx = scholartools._build_ctx()
    assert ctx.llm_extract is None


def test_gbooks_key_enables_google_books_source(monkeypatch):
    import scholartools

    monkeypatch.setenv("GBOOKS_API_KEY", "gbooks-test-key")
    ctx = scholartools._build_ctx()
    names = [s["name"] for s in ctx.api_sources]
    assert "google_books" in names


def test_no_gbooks_key_disables_google_books_source(monkeypatch):
    import scholartools

    monkeypatch.delenv("GBOOKS_API_KEY", raising=False)
    ctx = scholartools._build_ctx()
    names = [s["name"] for s in ctx.api_sources]
    assert "google_books" not in names
