import asyncio
from pathlib import Path

from scholartools.models import LibraryCtx
from scholartools.services.files import (
    _resolve_file_path,
    list_files,
    move_file,
    reindex_files,
)


def make_ctx(tmp_path, initial=None):
    store = list(initial or [])
    files_dir = tmp_path / "files"
    files_dir.mkdir(exist_ok=True)

    async def read_all():
        return list(store)

    async def write_all(records):
        store.clear()
        store.extend(records)

    async def copy_file(src, dest):
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(Path(src).read_bytes())

    async def delete_file(path):
        Path(path).unlink(missing_ok=True)

    async def rename_file(old, new):
        Path(old).rename(new)

    async def list_file_paths(dir_path):
        return []

    return (
        LibraryCtx(
            read_all=read_all,
            write_all=write_all,
            copy_file=copy_file,
            delete_file=delete_file,
            rename_file=rename_file,
            list_file_paths=list_file_paths,
            files_dir=str(files_dir),
            api_sources=[],
        ),
        store,
        files_dir,
    )


async def test_move_file(tmp_path):
    ctx, store, files_dir = make_ctx(
        tmp_path,
        [
            {
                "id": "x",
                "type": "book",
                "_file": {
                    "path": "x.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 5,
                    "added_at": "2026-01-01T00:00:00Z",
                },
            }
        ],
    )
    (files_dir / "x.pdf").write_bytes(b"hello")

    result = await move_file("x", "x_renamed.pdf", ctx)

    assert result.error is None
    assert store[0]["_file"]["path"] == "x_renamed.pdf"
    assert result.new_path.endswith("x_renamed.pdf")


async def test_list_files_empty(tmp_path):
    ctx, _, _ = make_ctx(tmp_path, [{"id": "x", "type": "book"}])
    result = await list_files(ctx)
    assert result.total == 0
    assert result.files == []


async def test_list_files(tmp_path):
    ctx, _, _ = make_ctx(
        tmp_path,
        [
            {
                "id": "a",
                "type": "book",
                "_file": {
                    "path": "a.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 1,
                    "added_at": "2026-01-01T00:00:00Z",
                },
            },
            {"id": "b", "type": "book"},
            {
                "id": "c",
                "type": "book",
                "_file": {
                    "path": "c.epub",
                    "mime_type": "application/epub+zip",
                    "size_bytes": 2,
                    "added_at": "2026-01-01T00:00:00Z",
                },
            },
        ],
    )
    result = await list_files(ctx)
    assert result.total == 2
    citekeys = {f.citekey for f in result.files}
    assert citekeys == {"a", "c"}


def test_resolve_file_path_relative(tmp_path):
    ctx, _, files_dir = make_ctx(tmp_path)
    resolved = _resolve_file_path(ctx, "paper.pdf")
    assert resolved == files_dir / "paper.pdf"


def test_resolve_file_path_absolute_exists(tmp_path):
    ctx, _, files_dir = make_ctx(tmp_path)
    existing = tmp_path / "other" / "paper.pdf"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"data")
    resolved = _resolve_file_path(ctx, str(existing))
    assert resolved == existing


def test_resolve_file_path_absolute_missing_falls_back(tmp_path):
    ctx, _, files_dir = make_ctx(tmp_path)
    legacy = Path("/old/library/files/paper.pdf")
    resolved = _resolve_file_path(ctx, str(legacy))
    assert resolved == files_dir / "paper.pdf"


def test_reindex_files_repairs_stale_path(tmp_path):
    ctx, store, files_dir = make_ctx(
        tmp_path,
        [
            {
                "id": "x",
                "type": "book",
                "_file": {
                    "path": "/old/path/x.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 5,
                    "added_at": "2026-01-01T00:00:00Z",
                },
            }
        ],
    )
    (files_dir / "x.pdf").write_bytes(b"hello")
    result = asyncio.run(reindex_files(ctx))
    assert result.repaired == 1
    assert result.already_ok == 0
    assert result.not_found == 0
    assert store[0]["_file"]["path"] == "x.pdf"


def test_reindex_files_already_ok(tmp_path):
    ctx, _, files_dir = make_ctx(
        tmp_path,
        [
            {
                "id": "x",
                "type": "book",
                "_file": {
                    "path": "x.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 5,
                    "added_at": "2026-01-01T00:00:00Z",
                },
            }
        ],
    )
    (files_dir / "x.pdf").write_bytes(b"hello")
    result = asyncio.run(reindex_files(ctx))
    assert result.repaired == 0
    assert result.already_ok == 1
    assert result.not_found == 0


def test_reindex_files_not_found(tmp_path):
    ctx, _, _ = make_ctx(
        tmp_path,
        [
            {
                "id": "x",
                "type": "book",
                "_file": {
                    "path": "/old/path/x.pdf",
                    "mime_type": "application/pdf",
                    "size_bytes": 5,
                    "added_at": "2026-01-01T00:00:00Z",
                },
            }
        ],
    )
    result = asyncio.run(reindex_files(ctx))
    assert result.repaired == 0
    assert result.already_ok == 0
    assert result.not_found == 1
