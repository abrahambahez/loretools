import json
from unittest.mock import patch

import pytest

from scholartools.cli import _build_parser
from scholartools.models import (
    FileRow,
    FilesListResult,
    MoveResult,
    PrefetchResult,
)


def _run(argv):
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.func(args)


def test_files_get_dispatches(capsys):
    with patch("scholartools.get_file", return_value="/files/smith2020.pdf") as mock_fn:
        with pytest.raises(SystemExit) as exc_info:
            _run(["files", "get", "smith2020"])
        assert exc_info.value.code == 0
        mock_fn.assert_called_once_with("smith2020")
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["ok"] is True
        assert data["data"] == "/files/smith2020.pdf"


def test_files_get_none_result(capsys):
    with patch("scholartools.get_file", return_value=None):
        with pytest.raises(SystemExit):
            _run(["files", "get", "missing"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["data"] is None


def test_files_move_dispatches():
    result = MoveResult(new_path="/files/smith2020_renamed.pdf")
    with patch("scholartools.move_file", return_value=result) as mock_fn:
        with pytest.raises(SystemExit) as exc_info:
            _run(["files", "move", "smith2020", "renamed.pdf"])
        assert exc_info.value.code == 0
        mock_fn.assert_called_once_with("smith2020", "renamed.pdf")


def test_files_list_json(capsys):
    row = FileRow(
        citekey="smith2020",
        path="/files/smith2020.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
    )
    result = FilesListResult(files=[row], total=1, page=1)
    with patch("scholartools.list_files", return_value=result) as mock_fn:
        with pytest.raises(SystemExit) as exc_info:
            _run(["files", "list"])
        assert exc_info.value.code == 0
        mock_fn.assert_called_once_with(page=1)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "data" in data
        assert "page_info" in data
        assert len(data["data"]) == 1


def test_files_list_plain(capsys):
    row = FileRow(
        citekey="smith2020",
        path="/files/smith2020.pdf",
        mime_type="application/pdf",
        size_bytes=1024,
    )
    result = FilesListResult(files=[row], total=1, page=1)
    with patch("scholartools.list_files", return_value=result):
        with pytest.raises(SystemExit) as exc_info:
            _run(["--plain", "files", "list"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "citekey" in out
        assert "smith2020" in out
        assert "smith2020.pdf" in out
        assert "{" not in out


def test_files_list_page_arg():
    result = FilesListResult(files=[], total=0, page=2)
    with patch("scholartools.list_files", return_value=result) as mock_fn:
        with pytest.raises(SystemExit):
            _run(["files", "list", "--page", "2"])
        mock_fn.assert_called_once_with(page=2)


def test_files_prefetch_no_citekeys():
    result = PrefetchResult(fetched=0, already_cached=0, errors=[])
    with patch("scholartools.prefetch_blobs", return_value=result) as mock_fn:
        with pytest.raises(SystemExit) as exc_info:
            _run(["files", "prefetch"])
        assert exc_info.value.code == 0
        mock_fn.assert_called_once_with(citekeys=None)


def test_files_prefetch_with_citekeys():
    result = PrefetchResult(fetched=2, already_cached=0, errors=[])
    with patch("scholartools.prefetch_blobs", return_value=result) as mock_fn:
        with pytest.raises(SystemExit) as exc_info:
            _run(["files", "prefetch", "--citekeys", "smith2020,jones2021"])
        assert exc_info.value.code == 0
        mock_fn.assert_called_once_with(citekeys=["smith2020", "jones2021"])
