import mimetypes
import shutil
from datetime import datetime, timezone
from pathlib import Path

from scholartools.models import (
    AttachResult,
    DetachResult,
    FileRecord,
    FileRow,
    FilesListResult,
    LibraryCtx,
    MoveResult,
    ReindexResult,
)
from scholartools.services.list_helpers import paginate


def _resolve_file_path(ctx: LibraryCtx, raw_path: str) -> Path:
    p = Path(raw_path)
    if not p.is_absolute():
        return Path(ctx.files_dir) / raw_path
    if p.exists():
        return p
    return Path(ctx.files_dir) / p.name


async def move_file(citekey: str, dest_name: str, ctx: LibraryCtx) -> MoveResult:
    records = await ctx.read_all()
    for r in records:
        if r.get("id") == citekey:
            if not r.get("_file"):
                return MoveResult(error="no file linked")
            r["_file"]["path"] = dest_name
            await ctx.write_all(records)
            return MoveResult(new_path=str(Path(ctx.files_dir) / dest_name))

    return MoveResult(error=f"not found: {citekey}")


async def list_files(ctx: LibraryCtx, page: int = 1) -> FilesListResult:
    records = await ctx.read_all()
    rows = sorted(
        [
            FileRow(
                citekey=r["id"],
                path=str(_resolve_file_path(ctx, r["_file"]["path"])),
                mime_type=r["_file"]["mime_type"],
                size_bytes=r["_file"]["size_bytes"],
            )
            for r in records
            if r.get("_file") and r.get("id")
        ],
        key=lambda f: f.citekey,
    )
    items, page, pages = paginate(rows, page)
    return FilesListResult(files=items, total=len(rows), page=page, pages=pages)


def _detect_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


async def attach_file(ctx: LibraryCtx, citekey: str, path: str) -> AttachResult:
    src = Path(path).resolve()
    if not src.exists():
        return AttachResult(error=f"file not found: {path}")

    records = await ctx.read_all()
    record = next((r for r in records if r.get("id") == citekey), None)
    if record is None:
        return AttachResult(error=f"not found: {citekey}")

    files_dir = Path(ctx.files_dir)
    if src.is_relative_to(files_dir):
        dest = src
    else:
        files_dir.mkdir(parents=True, exist_ok=True)
        dest = files_dir / f"{citekey}{src.suffix}"
        try:
            shutil.copy2(src, dest)
        except OSError as exc:
            return AttachResult(error=f"file copy failed: {exc}")

    file_record = FileRecord(
        path=dest.name,
        mime_type=_detect_mime(str(dest)),
        size_bytes=dest.stat().st_size,
        added_at=datetime.now(timezone.utc).isoformat(),
    )
    record["_file"] = file_record.model_dump()
    await ctx.write_all(records)
    return AttachResult(citekey=citekey, file_record=file_record)


async def detach_file(ctx: LibraryCtx, citekey: str) -> DetachResult:
    records = await ctx.read_all()
    record = next((r for r in records if r.get("id") == citekey), None)
    if record is None:
        return DetachResult(error=f"not found: {citekey}")

    if not record.get("_file"):
        return DetachResult(error="no file attached")

    file_path = Path(ctx.files_dir) / record["_file"]["path"]
    try:
        file_path.unlink()
    except FileNotFoundError:
        pass

    record.pop("_file")
    await ctx.write_all(records)
    return DetachResult(detached=True)


async def get_file(ctx: LibraryCtx, citekey: str) -> Path | None:
    records = await ctx.read_all()
    record = next((r for r in records if r.get("id") == citekey), None)
    if record is None:
        return None

    file_rec = record.get("_file")
    if not file_rec:
        return None
    raw = file_rec["path"]
    p = Path(raw)
    if not p.is_absolute():
        p = Path(ctx.files_dir) / raw
    elif not p.exists():
        p = Path(ctx.files_dir) / p.name
    return p if p.exists() else None


async def reindex_files(ctx: LibraryCtx) -> ReindexResult:
    files_dir = Path(ctx.files_dir)
    if not files_dir.exists():
        return ReindexResult(repaired=0, already_ok=0, not_found=0)

    stem_map = {p.stem: p.name for p in files_dir.iterdir() if p.is_file()}
    records = await ctx.read_all()
    repaired = 0
    already_ok = 0
    not_found = 0

    for r in records:
        if not r.get("_file"):
            continue
        raw_path = r["_file"]["path"]
        p = Path(raw_path)
        direct = p if p.is_absolute() else files_dir / raw_path
        if direct.exists():
            already_ok += 1
        else:
            stem = p.stem
            if stem in stem_map:
                r["_file"]["path"] = stem_map[stem]
                repaired += 1
            else:
                not_found += 1

    if repaired:
        await ctx.write_all(records)

    return ReindexResult(repaired=repaired, already_ok=already_ok, not_found=not_found)
