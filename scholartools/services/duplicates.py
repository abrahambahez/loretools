import unicodedata

from scholartools.models import Reference

_PUNCTUATION = str.maketrans("", "", "\"'?.,;:!()[]{}-_/\\")


def normalize_title(title: str) -> str:
    nfkd = unicodedata.normalize("NFKD", title)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    tokens = stripped.lower().translate(_PUNCTUATION).split()
    return " ".join(tokens)


def _normalize_isbn(isbn: str) -> str:
    return isbn.replace("-", "").replace(" ", "")


def _isbns(ref: Reference) -> set[str]:
    raw = ref.model_extra.get("ISBN") if ref.model_extra else None
    if not raw:
        return set()
    values = [raw] if isinstance(raw, str) else raw
    return {_normalize_isbn(v) for v in values if v}


def is_duplicate(ref: Reference, library_refs: list[Reference]) -> str | None:
    ref_title = normalize_title(ref.title) if ref.title else None
    ref_isbns = _isbns(ref)

    for lib_ref in library_refs:
        if ref_title and lib_ref.title and normalize_title(lib_ref.title) == ref_title:
            return lib_ref.id
        if ref_isbns and ref_isbns & _isbns(lib_ref):
            return lib_ref.id

    return None
