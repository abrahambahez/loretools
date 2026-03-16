import json
from unittest.mock import AsyncMock, patch

import pytest

from scholartools.models import (
    ConflictRecord,
    PullResult,
    PushResult,
    Result,
)


@pytest.fixture(autouse=True)
def reset_ctx(tmp_path, monkeypatch):
    import scholartools
    from scholartools.models import Settings

    data = json.loads(
        Settings().model_dump_json(
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
    data["peer"] = {"peer_id": "peer-a", "device_id": "dev-1"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data))
    monkeypatch.setattr("scholartools.config.CONFIG_PATH", config_path)
    scholartools.reset()
    yield
    scholartools.reset()


def test_push_returns_push_result():
    import scholartools

    with patch(
        "scholartools.sync_service.push",
        new=AsyncMock(return_value=PushResult(entries_pushed=2)),
    ):
        result = scholartools.push()

    assert isinstance(result, PushResult)
    assert result.entries_pushed == 2


def test_pull_returns_pull_result():
    import scholartools

    with patch(
        "scholartools.sync_service.pull",
        new=AsyncMock(return_value=PullResult(applied_count=3)),
    ):
        result = scholartools.pull()

    assert isinstance(result, PullResult)
    assert result.applied_count == 3


def test_create_snapshot_calls_service():
    import scholartools

    called = []

    async def fake_snapshot(ctx):
        called.append(True)

    with patch("scholartools.sync_service.create_snapshot", new=fake_snapshot):
        scholartools.create_snapshot()

    assert called


def test_list_conflicts_empty(tmp_path, monkeypatch):
    import scholartools

    monkeypatch.setattr(scholartools._get_ctx(), "data_dir", str(tmp_path))
    result = scholartools.list_conflicts()
    assert result == []


def test_list_conflicts_returns_records(tmp_path, monkeypatch):
    import scholartools
    from scholartools.adapters.conflicts_store import write_conflict

    conflict = ConflictRecord(
        uid="uid-1",
        field="title",
        local_value="A",
        local_timestamp_hlc="t1",
        remote_value="B",
        remote_timestamp_hlc="t2",
        remote_peer_id="peer-b",
    )
    write_conflict(tmp_path, conflict)

    with patch.object(scholartools._get_ctx(), "data_dir", str(tmp_path)):
        ctx = scholartools._get_ctx()
        ctx_copy = ctx.model_copy(update={"data_dir": str(tmp_path)})

    with patch("scholartools._get_ctx", return_value=ctx_copy):
        result = scholartools.list_conflicts()

    assert len(result) == 1
    assert result[0].uid == "uid-1"


def test_restore_reference_creates_log_entry(tmp_path, monkeypatch):
    import scholartools

    ctx = scholartools._get_ctx()
    ctx_with_dir = ctx.model_copy(update={"data_dir": str(tmp_path)})

    with patch("scholartools._get_ctx", return_value=ctx_with_dir):
        result = scholartools.restore_reference("smith2020")

    assert isinstance(result, Result)
    assert result.ok is True
    log_dir = tmp_path / "change_log"
    assert log_dir.exists()
    files = list(log_dir.iterdir())
    assert len(files) == 1
    entry_data = json.loads(files[0].read_text())
    assert entry_data["op"] == "restore_reference"
    assert entry_data["citekey"] == "smith2020"


def test_resolve_conflict_no_sync_config(tmp_path):
    import scholartools

    ctx = scholartools._get_ctx()
    ctx_no_sync = ctx.model_copy(
        update={"data_dir": str(tmp_path), "sync_config": None}
    )

    with patch("scholartools._get_ctx", return_value=ctx_no_sync):
        result = scholartools.resolve_conflict("uid-1", "title", "value")

    assert not result.ok
    assert "sync not configured" in result.error
