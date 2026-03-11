import httpx

from scholartools.apis._http import get as _get
from scholartools.ports import FetchFn, SearchFn

_BASE = "https://api.openalex.org"
_FIELDS = "title,authorships,publication_year,doi,primary_location,type"


def make_openalex(email: str | None = None) -> tuple[SearchFn, FetchFn]:
    headers = {"User-Agent": f"scholartools/0.1 (mailto:{email})"} if email else {}

    async def search(query: str, limit: int) -> list[dict]:
        async with httpx.AsyncClient(headers=headers, timeout=10) as client:
            r = await _get(
                client,
                f"{_BASE}/works",
                params={"search": query, "per-page": limit, "select": _FIELDS},
            )
            return [_normalize(w) for w in r.json().get("results", [])]

    async def fetch(identifier: str) -> dict | None:
        async with httpx.AsyncClient(headers=headers, timeout=10) as client:
            r = await client.get(
                f"{_BASE}/works/doi:{identifier}", params={"select": _FIELDS}
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return _normalize(r.json())

    return search, fetch


def _normalize(item: dict) -> dict:
    out: dict = {"type": _csl_type(item.get("type", ""))}
    if title := item.get("title"):
        out["title"] = title
    if authorships := item.get("authorships"):
        out["author"] = [
            _split_name(a["author"]["display_name"])
            for a in authorships
            if a.get("author", {}).get("display_name")
        ]
    if year := item.get("publication_year"):
        out["issued"] = {"date-parts": [[year]]}
    if doi := item.get("doi"):
        out["DOI"] = doi.removeprefix("https://doi.org/")
    if loc := item.get("primary_location"):
        if source := (loc.get("source") or {}):
            if name := source.get("display_name"):
                out["container-title"] = name
    return out


def _split_name(name: str) -> dict:
    parts = name.rsplit(" ", 1)
    if len(parts) == 2:
        return {"given": parts[0], "family": parts[1]}
    return {"family": name}


def _csl_type(raw: str) -> str:
    mapping = {
        "journal-article": "article-journal",
        "book": "book",
        "book-chapter": "chapter",
        "proceedings-article": "paper-conference",
        "dissertation": "thesis",
        "dataset": "dataset",
        "preprint": "article",
    }
    return mapping.get(raw, "article-journal")
