from scholartools.adapters.conflicts_store import (
    delete_conflict,
    read_conflicts,
    write_conflict,
)
from scholartools.models import ConflictRecord


def make_conflict(uid="uid-1", field="title"):
    return ConflictRecord(
        uid=uid,
        field=field,
        local_value="Local",
        local_timestamp_hlc="2024-01-01T00:00:00.000Z-0001-a",
        remote_value="Remote",
        remote_timestamp_hlc="2024-01-01T00:00:00.000Z-0001-b",
        remote_peer_id="peer-b",
    )


def test_write_creates_file(tmp_path):
    conflict = make_conflict()
    write_conflict(tmp_path, conflict)
    path = tmp_path / "conflicts" / "uid-1-title.json"
    assert path.exists()


def test_write_creates_missing_directory(tmp_path):
    data_dir = tmp_path / "nonexistent"
    conflict = make_conflict()
    write_conflict(data_dir, conflict)
    assert (data_dir / "conflicts" / "uid-1-title.json").exists()


def test_read_conflicts_empty(tmp_path):
    assert read_conflicts(tmp_path) == []


def test_read_conflicts_returns_records(tmp_path):
    c1 = make_conflict("uid-1", "title")
    c2 = make_conflict("uid-2", "author")
    write_conflict(tmp_path, c1)
    write_conflict(tmp_path, c2)
    results = read_conflicts(tmp_path)
    assert len(results) == 2
    uids = {r.uid for r in results}
    assert uids == {"uid-1", "uid-2"}


def test_delete_conflict(tmp_path):
    conflict = make_conflict()
    write_conflict(tmp_path, conflict)
    delete_conflict(tmp_path, "uid-1", "title")
    assert not (tmp_path / "conflicts" / "uid-1-title.json").exists()


def test_delete_missing_conflict_is_noop(tmp_path):
    delete_conflict(tmp_path, "nonexistent", "field")


def test_read_conflict_roundtrip(tmp_path):
    conflict = make_conflict()
    write_conflict(tmp_path, conflict)
    results = read_conflicts(tmp_path)
    assert len(results) == 1
    assert results[0] == conflict
