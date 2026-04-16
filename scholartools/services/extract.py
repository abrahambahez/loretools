import re
import uuid
from pathlib import Path

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException
from pydantic import ValidationError

from scholartools.models import ExtractResult, LibraryCtx, Reference

_DOI_RE = re.compile(r"\b(10\.\d{4,}/[^\s,;]+)")
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_REQUIRED = ("title", "author", "issued")


async def extract_from_file(file_path: str, ctx: LibraryCtx) -> ExtractResult:
    if not Path(file_path).exists():
        return ExtractResult(error=f"file not found: {file_path}")

    fields, confidence = _extract_with_pdfplumber(file_path)

    if confidence >= 0.7 and _has_required(fields):
        return _build_result(fields, confidence)

    if not fields or (fields.get("title") is None and fields.get("author") is None):
        return ExtractResult(agent_extraction_needed=True, file_path=file_path)

    return _build_result(fields, confidence)


def _extract_with_pdfplumber(file_path: str) -> tuple[dict, float]:
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages[:3])
    except (OSError, PdfminerException):
        return {}, 0.0

    fields: dict = {}

    doi = _DOI_RE.search(text)
    if doi:
        fields["DOI"] = doi.group(1)

    years = _YEAR_RE.findall(text)
    if years:
        fields["issued"] = {"date-parts": [[int(years[0])]]}

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        if len(line) > 15 and not _YEAR_RE.fullmatch(line):
            fields["title"] = line
            break

    return fields, _confidence(fields)


def _has_required(fields: dict) -> bool:
    return all(fields.get(f) for f in _REQUIRED)


def _confidence(fields: dict) -> float:
    found = sum(1 for f in _REQUIRED if fields.get(f))
    return found / len(_REQUIRED)


def _build_result(fields: dict, confidence: float) -> ExtractResult:
    citekey = f"ref{uuid.uuid4().hex[:6]}"
    try:
        ref = Reference.model_validate(
            {"id": citekey, "type": "article-journal", **fields}
        )
    except ValidationError as e:
        return ExtractResult(error=str(e), confidence=confidence)
    return ExtractResult(reference=ref, confidence=confidence)
