import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from loretools.models import LibraryCtx, ReadResult
from loretools.services.read import (
    _MARKITDOWN_SUFFIXES,
    _PDF_SUFFIXES,
    _check_quality,
    _convert_with_markitdown,
    read_reference,
)


def make_ctx(records, sources_raw_dir, sources_read_dir):
    async def read_all():
        return records

    async def write_all(r):
        pass

    async def noop(*_):
        pass

    return LibraryCtx(
        read_all=read_all,
        write_all=write_all,
        copy_file=noop,
        delete_file=noop,
        rename_file=noop,
        list_file_paths=lambda _: [],
        sources_raw_dir=str(sources_raw_dir),
        sources_read_dir=str(sources_read_dir),
        staging_read_all=read_all,
        staging_write_all=write_all,
        staging_copy_file=noop,
        staging_delete_file=noop,
        staging_dir="/tmp/staging",
        api_sources=[],
    )


# --- constants ---


def test_pdf_suffixes():
    assert ".pdf" in _PDF_SUFFIXES


def test_markitdown_suffixes():
    for ext in (".epub", ".docx", ".doc", ".html", ".htm", ".pptx"):
        assert ext in _MARKITDOWN_SUFFIXES


# --- _check_quality ---


def test_check_quality_dense_text():
    text = "word " * 600
    score = _check_quality(text, 1)
    assert score == 1.0


def test_check_quality_empty_text():
    score = _check_quality("", 1)
    assert score == 0.0


# --- _convert_with_markitdown ---


async def test_convert_with_markitdown_success(tmp_path):
    fake_result = MagicMock()
    fake_result.text_content = "# Hello\n\nContent here."
    fake_md = MagicMock()
    fake_md.convert.return_value = fake_result

    with patch.dict(
        "sys.modules", {"markitdown": MagicMock(MarkItDown=lambda: fake_md)}
    ):
        md, err = await _convert_with_markitdown(str(tmp_path / "fake.epub"))

    assert err == ""
    assert "Hello" in md


async def test_convert_with_markitdown_exception(tmp_path):
    broken_md = MagicMock()
    broken_md.convert.side_effect = RuntimeError("bad file")

    with patch.dict(
        "sys.modules", {"markitdown": MagicMock(MarkItDown=lambda: broken_md)}
    ):
        md, err = await _convert_with_markitdown(str(tmp_path / "bad.epub"))

    assert md == ""
    assert "bad file" in err


# --- read_reference dispatch ---


async def test_read_reference_unsupported_format(tmp_path):
    fake_file = tmp_path / "note.xyz"
    fake_file.write_text("data")
    record = {"id": "smith2021", "_file": {"path": str(fake_file)}}
    ctx = make_ctx([record], tmp_path, tmp_path / "read")

    result = await read_reference("smith2021", ctx)

    assert result.error == "unsupported format: .xyz"


async def test_read_reference_not_found(tmp_path):
    ctx = make_ctx([], tmp_path, tmp_path / "read")
    result = await read_reference("missing2021", ctx)
    assert "not found" in result.error


async def test_read_reference_no_file_linked(tmp_path):
    ctx = make_ctx([{"id": "smith2021"}], tmp_path, tmp_path / "read")
    result = await read_reference("smith2021", ctx)
    assert result.error == "no file linked"


async def test_read_reference_file_missing_on_disk(tmp_path):
    record = {"id": "smith2021", "_file": {"path": str(tmp_path / "missing.epub")}}
    ctx = make_ctx([record], tmp_path, tmp_path / "read")
    result = await read_reference("smith2021", ctx)
    assert "file not found" in result.error


async def test_read_reference_markitdown_dispatch(tmp_path):
    epub_file = tmp_path / "book.epub"
    epub_file.write_bytes(b"fake epub bytes")
    record = {"id": "jones2022", "_file": {"path": str(epub_file)}}
    read_dir = tmp_path / "read"
    ctx = make_ctx([record], tmp_path, read_dir)

    fake_result = MagicMock()
    fake_result.text_content = "# Chapter 1\n\n" + "word " * 200
    fake_md_instance = MagicMock()
    fake_md_instance.convert.return_value = fake_result

    with patch(
        "loretools.services.read._convert_with_markitdown",
        new=AsyncMock(return_value=("# Chapter 1\n\n" + "word " * 200, "")),
    ):
        result = await read_reference("jones2022", ctx)

    assert result.error is None
    assert result.method == "markitdown"
    assert result.format == "md"
    assert result.page_count is None
    assert result.quality_score is not None
    assert (read_dir / "jones2022.source.md").exists()


async def test_read_reference_markitdown_error(tmp_path):
    epub_file = tmp_path / "broken.epub"
    epub_file.write_bytes(b"bad")
    record = {"id": "fail2022", "_file": {"path": str(epub_file)}}
    ctx = make_ctx([record], tmp_path, tmp_path / "read")

    with patch(
        "loretools.services.read._convert_with_markitdown",
        new=AsyncMock(return_value=("", "corrupt epub")),
    ):
        result = await read_reference("fail2022", ctx)

    assert result.error == "markitdown conversion failed: corrupt epub"


async def test_read_reference_cache_hit(tmp_path):
    read_dir = tmp_path / "read"
    read_dir.mkdir()
    cached = read_dir / "jones2022.source.md"
    cached.write_text("cached content")

    ctx = make_ctx([], tmp_path, read_dir)
    result = await read_reference("jones2022", ctx)

    assert result.error is None
    assert result.output_path == str(cached)
    assert result.method is None


async def test_read_reference_force_bypasses_cache(tmp_path):
    epub_file = tmp_path / "book.epub"
    epub_file.write_bytes(b"epub")
    read_dir = tmp_path / "read"
    read_dir.mkdir()
    cached = read_dir / "jones2022.source.md"
    cached.write_text("old cached content")

    record = {"id": "jones2022", "_file": {"path": str(epub_file)}}
    ctx = make_ctx([record], tmp_path, read_dir)

    with patch(
        "loretools.services.read._convert_with_markitdown",
        new=AsyncMock(return_value=("new content", "")),
    ):
        result = await read_reference("jones2022", ctx, force=True)

    assert result.method == "markitdown"
    assert cached.read_text() == "new content"


# --- ReadResult model ---


def test_read_result_accepts_markitdown_method():
    r = ReadResult(citekey="x", method="markitdown", format="md")
    assert r.method == "markitdown"


def test_read_result_rejects_unknown_method():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ReadResult(citekey="x", method="unknown_tool")


# --- CLI ---


def test_lore_read_cli_registered():
    from loretools.cli import _build_parser

    parser = _build_parser()
    subparsers_action = next(
        a for a in parser._actions if hasattr(a, "_name_parser_map")
    )
    assert "read" in subparsers_action._name_parser_map


def test_lore_read_cli_outputs_json(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)

    fake_result = ReadResult(
        citekey="test2023",
        output_path="/tmp/test2023.source.md",
        format="md",
        method="markitdown",
        quality_score=0.9,
        page_count=None,
    )

    with patch("loretools.read_reference", return_value=fake_result):
        from loretools.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["read", "test2023"])
        args.func(args)

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["citekey"] == "test2023"
    assert data["method"] == "markitdown"


def test_lore_read_cli_exits_1_on_error(tmp_path, monkeypatch):
    fake_result = ReadResult(citekey="bad2023", error="not found: bad2023")

    with patch("loretools.read_reference", return_value=fake_result):
        from loretools.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["read", "bad2023"])
        with pytest.raises(SystemExit) as exc_info:
            args.func(args)

    assert exc_info.value.code == 1


def test_lore_read_cli_force_flag(tmp_path):
    fake_result = ReadResult(citekey="smith2023", method="markitdown", format="md")

    captured_kwargs = {}

    def fake_read(citekey, force=False):
        captured_kwargs["force"] = force
        return fake_result

    with patch("loretools.read_reference", side_effect=fake_read):
        from loretools.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["read", "smith2023", "--force"])
        args.func(args)

    assert captured_kwargs["force"] is True


# --- markitdown import ---


def test_markitdown_importable():
    import markitdown  # noqa: F401
