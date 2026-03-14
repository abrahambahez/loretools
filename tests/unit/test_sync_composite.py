import asyncio
import json

from scholartools.adapters.sync_composite import make_sync_storage
from scholartools.models import ChangeLogEntry


def test_read_delegates_to_local(tmp_path):
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps([{"id": "s2020", "type": "article"}]))

    read_all, _ = make_sync_storage(str(lib), str(tmp_path), "peer-a", "dev-1")
    records = asyncio.run(read_all())
    assert len(records) == 1
    assert records[0]["id"] == "s2020"


def test_write_creates_change_log(tmp_path):
    lib = tmp_path / "library.json"
    lib.write_text("[]")

    _, write_all = make_sync_storage(str(lib), str(tmp_path), "peer-a", "dev-1")
    asyncio.run(write_all([{"id": "s2020", "type": "article", "title": "Test"}]))

    log_dir = tmp_path / "change_log"
    assert log_dir.exists()
    files = list(log_dir.iterdir())
    assert len(files) == 1

    entry = ChangeLogEntry.model_validate_json(files[0].read_text())
    assert entry.op == "add_reference"
    assert entry.citekey == "s2020"
    assert entry.peer_id == "peer-a"
    assert entry.device_id == "dev-1"


def test_write_update_creates_update_entry(tmp_path):
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps([{"id": "s2020", "type": "article", "title": "Old"}]))

    _, write_all = make_sync_storage(str(lib), str(tmp_path), "peer-a", "dev-1")
    asyncio.run(write_all([{"id": "s2020", "type": "article", "title": "New"}]))

    log_dir = tmp_path / "change_log"
    files = list(log_dir.iterdir())
    assert len(files) == 1
    entry = ChangeLogEntry.model_validate_json(files[0].read_text())
    assert entry.op == "update_reference"


def test_write_delete_creates_delete_entry(tmp_path):
    lib = tmp_path / "library.json"
    lib.write_text(
        json.dumps(
            [
                {"id": "s2020", "type": "article"},
                {"id": "jones2021", "type": "book"},
            ]
        )
    )

    _, write_all = make_sync_storage(str(lib), str(tmp_path), "peer-a", "dev-1")
    # Only s2020 remains — jones2021 is deleted
    asyncio.run(write_all([{"id": "s2020", "type": "article"}]))

    log_dir = tmp_path / "change_log"
    files = list(log_dir.iterdir())
    entries = [ChangeLogEntry.model_validate_json(f.read_text()) for f in files]
    ops = {e.op for e in entries}
    assert "delete_reference" in ops
    delete_entries = [e for e in entries if e.op == "delete_reference"]
    assert delete_entries[0].citekey == "jones2021"


def test_no_upload_on_write(tmp_path):
    from unittest.mock import patch

    lib = tmp_path / "library.json"
    lib.write_text("[]")

    _, write_all = make_sync_storage(str(lib), str(tmp_path), "peer-a", "dev-1")

    with patch("scholartools.adapters.s3_sync.upload") as mock_upload:
        asyncio.run(write_all([{"id": "s2020", "type": "article"}]))

    mock_upload.assert_not_called()


def test_write_persists_to_disk(tmp_path):
    lib = tmp_path / "library.json"
    lib.write_text("[]")

    _, write_all = make_sync_storage(str(lib), str(tmp_path), "peer-a", "dev-1")
    asyncio.run(write_all([{"id": "s2020", "type": "article"}]))

    data = json.loads(lib.read_text())
    assert len(data) == 1
    assert data[0]["id"] == "s2020"
