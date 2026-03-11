import httpx

from scholartools.apis._http import get as _get
from scholartools.ports import FetchFn, SearchFn

_BASE = "https://doaj.org/api"


def make_doaj() -> tuple[SearchFn, FetchFn]:
    async def search(query: str, limit: int) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await _get(
                client,
                f"{_BASE}/search/articles/{query}",
                params={"pageSize": limit},
            )
            return [_normalize(a) for a in r.json().get("results", [])]

    async def fetch(identifier: str) -> dict | None:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await _get(
                client,
                f"{_BASE}/search/articles/doi:{identifier}",
                params={"pageSize": 1},
            )
            results = r.json().get("results", [])
            return _normalize(results[0]) if results else None

    return search, fetch


def _normalize(item: dict) -> dict:
    bib = item.get("bibjson", {})
    out: dict = {"type": "article-journal"}
    if title := bib.get("title"):
        out["title"] = title
    if authors := bib.get("author"):
        out["author"] = [
            {"family": a.get("name", "")} for a in authors if a.get("name")
        ]
    if year := (bib.get("year") or (bib.get("month_of_publication") or "")[:4]):
        try:
            out["issued"] = {"date-parts": [[int(year)]]}
        except (ValueError, TypeError):
            pass
    if identifiers := bib.get("identifier", []):
        for ident in identifiers:
            if ident.get("type") == "doi":
                out["DOI"] = ident["id"]
                break
    if journal := bib.get("journal", {}).get("title"):
        out["container-title"] = journal
    return out
