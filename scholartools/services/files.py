"""Gestión de archivos vinculados a referencias.

A diferencia del scholartools original, no copia archivos — solo registra
la ruta absoluta del archivo existente en librero/. El manejo físico
de archivos queda en manos de los scripts de la bóveda.
"""

import mimetypes
from datetime import datetime, timezone
from pathlib import Path

from scholartools.models import (
    FileRecord,
    FileRow,
    FilesListResult,
    LibraryCtx,
    LinkResult,
    MoveResult,
    ReindexResult,
    UnlinkResult,
)
from scholartools.services.list_helpers import paginate


async def link_file(citekey: str, file_path: str, ctx: LibraryCtx) -> LinkResult:
    records = await ctx.read_all()
    for r in records:
        if r.get("id") == citekey:
            src = Path(file_path).resolve()
            if not src.exists():
                return LinkResult(error=f"file not found: {file_path}")

            record = FileRecord(
                path=str(src),
                mime_type=_detect_mime(str(src)),
                size_bytes=src.stat().st_size,
                added_at=datetime.now(timezone.utc).isoformat(),
            )
            r["_file"] = record.model_dump()
            await ctx.write_all(records)
            return LinkResult(citekey=citekey, file_record=record)

    return LinkResult(error=f"not found: {citekey}")


async def unlink_file(citekey: str, ctx: LibraryCtx) -> UnlinkResult:
    records = await ctx.read_all()
    for r in records:
        if r.get("id") == citekey:
            if not r.get("_file"):
                return UnlinkResult(unlinked=False, error="no file linked")
            r.pop("_file", None)
            await ctx.write_all(records)
            return UnlinkResult(unlinked=True)

    return UnlinkResult(unlinked=False, error=f"not found: {citekey}")


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
