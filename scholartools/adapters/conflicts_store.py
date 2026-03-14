from pathlib import Path

from scholartools.models import ConflictRecord


def _conflict_path(data_dir: Path, uid: str, field: str) -> Path:
    return data_dir / "conflicts" / f"{uid}-{field}.json"


def write_conflict(data_dir: Path, conflict: ConflictRecord) -> None:
    path = _conflict_path(data_dir, conflict.uid, conflict.field)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(conflict.model_dump_json(), encoding="utf-8")


def read_conflicts(data_dir: Path) -> list[ConflictRecord]:
    conflicts_dir = data_dir / "conflicts"
    if not conflicts_dir.exists():
        return []
    result = []
    for f in sorted(conflicts_dir.iterdir()):
        if not f.is_file() or not f.suffix == ".json":
            continue
        try:
            result.append(
                ConflictRecord.model_validate_json(f.read_text(encoding="utf-8"))
            )
        except (ValueError, OSError):
            continue
    return result


def delete_conflict(data_dir: Path, uid: str, field: str) -> None:
    _conflict_path(data_dir, uid, field).unlink(missing_ok=True)
