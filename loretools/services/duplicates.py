import unicodedata

from loretools.models import Reference

_PUNCTUATION = str.maketrans("", "", "\"'?.,;:!()[]{}-_/\\")


def normalize_title(title: str) -> str:
    nfkd = unicodedata.normalize("NFKD", title)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    tokens = stripped.lower().translate(_PUNCTUATION).split()
    return " ".join(tokens)


def is_duplicate(ref: Reference, library_refs: list[Reference]) -> str | None:
    if not ref.uid:
        return None
    for lib_ref in library_refs:
        if lib_ref.uid and lib_ref.uid == ref.uid:
            return lib_ref.id
    return None
