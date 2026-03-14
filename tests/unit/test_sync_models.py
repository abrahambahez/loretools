import pytest
from pydantic import ValidationError

from scholartools.models import (
    ChangeLogEntry,
    ConflictRecord,
    PullResult,
    PushResult,
    SyncConfig,
)


def test_change_log_entry_roundtrip():
    e = ChangeLogEntry(
        op="add_reference",
        uid="uid-123",
        uid_confidence="authoritative",
        citekey="smith2020",
        data={"title": "Test"},
        peer_id="peer-a",
        device_id="dev-1",
        timestamp_hlc="2024-01-01T00:00:00.000Z-0001-peer-a",
        signature="abc",
    )
    assert ChangeLogEntry.model_validate_json(e.model_dump_json()) == e


def test_conflict_record_roundtrip():
    c = ConflictRecord(
        uid="uid-123",
        field="title",
        local_value="Local Title",
        local_timestamp_hlc="2024-01-01T00:00:00.000Z-0001-a",
        remote_value="Remote Title",
        remote_timestamp_hlc="2024-01-01T00:00:00.000Z-0001-b",
        remote_peer_id="peer-b",
    )
    assert ConflictRecord.model_validate_json(c.model_dump_json()) == c


def test_conflict_record_any_local_value():
    c = ConflictRecord(
        uid="u",
        field="f",
        local_value={"nested": [1, 2, 3]},
        local_timestamp_hlc="t1",
        remote_value=None,
        remote_timestamp_hlc="t2",
        remote_peer_id="p",
    )
    assert c.local_value == {"nested": [1, 2, 3]}
    assert c.remote_value is None


def test_push_result_defaults():
    r = PushResult()
    assert r.entries_pushed == 0
    assert r.errors == []


def test_pull_result_defaults():
    r = PullResult()
    assert r.applied_count == 0
    assert r.rejected_count == 0
    assert r.conflicted_count == 0
    assert r.errors == []


def test_sync_config_required_fields():
    with pytest.raises(ValidationError):
        SyncConfig(access_key="a", secret_key="b")  # missing bucket


def test_sync_config_optional_endpoint():
    c = SyncConfig(bucket="b", access_key="a", secret_key="s")
    assert c.endpoint is None

    c2 = SyncConfig(
        endpoint="http://localhost:9000", bucket="b", access_key="a", secret_key="s"
    )
    assert c2.endpoint == "http://localhost:9000"


def test_sync_config_roundtrip():
    c = SyncConfig(
        endpoint="http://minio:9000", bucket="test", access_key="acc", secret_key="sec"
    )
    assert SyncConfig.model_validate_json(c.model_dump_json()) == c
