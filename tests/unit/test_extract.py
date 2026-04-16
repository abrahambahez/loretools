from unittest.mock import patch

import pytest

from scholartools.models import LibraryCtx
from scholartools.services.extract import _confidence, extract_from_file


def make_ctx(files_dir="data/files"):
    from unittest.mock import AsyncMock

    async def noop(*_):
        pass

    return LibraryCtx(
        read_all=AsyncMock(return_value=[]),
        write_all=noop,
        copy_file=noop,
        delete_file=noop,
        rename_file=noop,
        list_file_paths=AsyncMock(return_value=[]),
        files_dir=files_dir,
    )


# --- confidence ---


def test_confidence_zero():
    assert _confidence({}) == 0.0


def test_confidence_partial():
    assert _confidence({"title": "X"}) == pytest.approx(1 / 3)


def test_confidence_full():
    fields = {
        "title": "X",
        "author": [{"family": "Smith"}],
        "issued": {"date-parts": [[2020]]},
    }
    assert _confidence(fields) == 1.0


# --- file not found ---


async def test_extract_file_not_found(tmp_path):
    ctx = make_ctx()
    result = await extract_from_file(str(tmp_path / "ghost.pdf"), ctx)
    assert result.reference is None
    assert result.error is not None
    assert "not found" in result.error


# --- pdfplumber path ---


async def test_extract_uses_pdfplumber_when_confident(tmp_path):
    good_fields = {
        "title": "Infrastructure in the Global South",
        "author": [{"family": "García"}],
        "issued": {"date-parts": [[2023]]},
    }
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"")
    with patch(
        "scholartools.services.extract._extract_with_pdfplumber",
        return_value=(good_fields, 1.0),
    ):
        ctx = make_ctx()
        result = await extract_from_file(str(fake), ctx)

    assert result.confidence == 1.0
    assert result.reference.title == "Infrastructure in the Global South"
    assert not result.agent_extraction_needed


# --- agent nudge on empty fields ---


async def test_extract_no_fields_returns_agent_nudge(tmp_path):
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"")
    with patch(
        "scholartools.services.extract._extract_with_pdfplumber",
        return_value=({}, 0.0),
    ):
        ctx = make_ctx()
        result = await extract_from_file(str(fake), ctx)

    assert result.agent_extraction_needed is True
    assert result.file_path == str(fake)
    assert result.reference is None


async def test_extract_partial_fields_returns_result(tmp_path):
    partial_fields = {"title": "Some Title", "DOI": "10.1/x"}
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"")
    with patch(
        "scholartools.services.extract._extract_with_pdfplumber",
        return_value=(partial_fields, 1 / 3),
    ):
        ctx = make_ctx()
        result = await extract_from_file(str(fake), ctx)

    assert result.reference.title == "Some Title"
    assert not result.agent_extraction_needed


# --- result never raises ---


async def test_extract_never_raises_on_corrupt_file(tmp_path):
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"not a pdf")
    ctx = make_ctx()
    result = await extract_from_file(str(corrupt), ctx)
    assert result is not None
