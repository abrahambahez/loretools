from pathlib import Path

from scholartools.models import ChangeLogEntry
from scholartools.services import hlc


def make_sync_storage(
    library_path: str,
    data_dir: str,
    peer_id: str,
    device_id: str,
):
    from scholartools.adapters.local import make_storage

    read_all, local_write_all = make_storage(library_path)
    _data_dir = Path(data_dir)

    async def write_all(records: list[dict]) -> None:
        old_raw = []
        try:
            old_raw = await read_all()
        except Exception:
            pass

        old_by_id = {r.get("id", ""): r for r in old_raw}
        new_by_id = {r.get("id", ""): r for r in records}

        await local_write_all(records)

        for rec_id, new_rec in new_by_id.items():
            op = "add_reference" if rec_id not in old_by_id else "update_reference"
            ts = hlc.now(peer_id)
            entry = ChangeLogEntry(
                op=op,
                uid=new_rec.get("uid") or "",
                uid_confidence=new_rec.get("uid_confidence") or "",
                citekey=rec_id,
                data=new_rec,
                peer_id=peer_id,
                device_id=device_id,
                timestamp_hlc=ts,
                signature="",
            )
            log_dir = _data_dir / "change_log"
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / f"{ts}.json").write_text(
                entry.model_dump_json(), encoding="utf-8"
            )

        for rec_id, old_rec in old_by_id.items():
            if rec_id not in new_by_id:
                ts = hlc.now(peer_id)
                entry = ChangeLogEntry(
                    op="delete_reference",
                    uid=old_rec.get("uid") or "",
                    uid_confidence=old_rec.get("uid_confidence") or "",
                    citekey=rec_id,
                    data={},
                    peer_id=peer_id,
                    device_id=device_id,
                    timestamp_hlc=ts,
                    signature="",
                )
                log_dir = _data_dir / "change_log"
                log_dir.mkdir(parents=True, exist_ok=True)
                (log_dir / f"{ts}.json").write_text(
                    entry.model_dump_json(), encoding="utf-8"
                )

    return read_all, write_all
