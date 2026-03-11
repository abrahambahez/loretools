from scholartools.models import Author, DateField, Reference
from scholartools.services.uid import _normalize_isbn, _normalize_text, compute_uid


def make_ref(**kwargs) -> Reference:
    defaults = {"id": "test", "type": "article-journal"}
    defaults.update(kwargs)
    return Reference(**defaults)


# --- _normalize_text ---


def test_normalize_text_nfc_and_lowercase():
    assert _normalize_text("Héllo") == "héllo"


def test_normalize_text_lowercase():
    assert _normalize_text("HELLO World") == "hello world"


def test_normalize_text_removes_punctuation():
    assert _normalize_text("Hello, World!") == "hello world"


def test_normalize_text_removes_symbols():
    assert _normalize_text("price: $100") == "price 100"


def test_normalize_text_collapses_whitespace():
    assert _normalize_text("  too   many   spaces  ") == "too many spaces"


def test_normalize_text_empty():
    assert _normalize_text("") == ""


def test_normalize_text_only_punctuation():
    assert _normalize_text("???...") == ""


# --- _normalize_isbn ---


def test_normalize_isbn_strips_hyphens():
    assert _normalize_isbn("978-3-16-148410-0") == "9783161484100"


def test_normalize_isbn_strips_spaces():
    assert _normalize_isbn("978 3 16 148410 0") == "9783161484100"


def test_normalize_isbn_10_to_13():
    result = _normalize_isbn("0-306-40615-2")
    assert result.startswith("978")
    assert len(result) == 13


def test_normalize_isbn_already_isbn13():
    result = _normalize_isbn("9783161484100")
    assert result == "9783161484100"


def test_normalize_isbn_10_conversion_check_digit():
    result = _normalize_isbn("0306406152")
    assert result == "9780306406157"


# --- compute_uid ---


def test_compute_uid_doi_is_authoritative():
    ref = make_ref(DOI="10.1234/test")
    uid, conf = compute_uid(ref)
    assert conf == "authoritative"
    assert len(uid) == 16


def test_compute_uid_doi_case_insensitive():
    ref1 = make_ref(DOI="10.1234/TEST")
    ref2 = make_ref(DOI="10.1234/test")
    assert compute_uid(ref1)[0] == compute_uid(ref2)[0]


def test_compute_uid_arxiv_is_authoritative():
    ref = make_ref(**{"arXiv-ID": "2301.00001"})
    uid, conf = compute_uid(ref)
    assert conf == "authoritative"
    assert len(uid) == 16


def test_compute_uid_arxiv_lowercase_key():
    ref = make_ref(**{"arxiv": "2301.00001"})
    uid, conf = compute_uid(ref)
    assert conf == "authoritative"


def test_compute_uid_isbn_is_authoritative():
    ref = make_ref(**{"ISBN": "978-3-16-148410-0"})
    uid, conf = compute_uid(ref)
    assert conf == "authoritative"
    assert len(uid) == 16


def test_compute_uid_isbn10_normalized_to_isbn13():
    ref_10 = make_ref(**{"ISBN": "0306406152"})
    ref_13 = make_ref(**{"ISBN": "9780306406157"})
    assert compute_uid(ref_10)[0] == compute_uid(ref_13)[0]


def test_compute_uid_tier2_fallback_is_semantic():
    ref = make_ref(
        title="Some Title",
        author=[Author(family="Smith")],
        issued=DateField(**{"date-parts": [[2020]]}),
    )
    uid, conf = compute_uid(ref)
    assert conf == "semantic"
    assert len(uid) == 16


def test_compute_uid_tier2_missing_fields_still_semantic():
    ref = make_ref()
    uid, conf = compute_uid(ref)
    assert conf == "semantic"
    assert len(uid) == 16


def test_compute_uid_idempotent():
    ref = make_ref(
        title="Reproducibility Test",
        author=[Author(family="Jones")],
        issued=DateField(**{"date-parts": [[2021]]}),
    )
    uid1, _ = compute_uid(ref)
    uid2, _ = compute_uid(ref)
    assert uid1 == uid2


def test_compute_uid_doi_takes_priority_over_isbn():
    ref = make_ref(DOI="10.1234/test", **{"ISBN": "9783161484100"})
    uid, conf = compute_uid(ref)
    ref_doi_only = make_ref(DOI="10.1234/test")
    uid_doi, _ = compute_uid(ref_doi_only)
    assert conf == "authoritative"
    assert uid == uid_doi
