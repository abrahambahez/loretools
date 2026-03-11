from scholartools.models import Reference
from scholartools.services.duplicates import is_duplicate, normalize_title


def ref(id: str, title: str | None = None, uid: str | None = None) -> Reference:
    return Reference(id=id, type="book", title=title, uid=uid)


# --- normalize_title ---


def test_normalize_lowercase():
    assert normalize_title("The Great Gatsby") == "the great gatsby"


def test_normalize_diacritics():
    assert normalize_title("Résumé") == "resume"


def test_normalize_diacritics_complex():
    assert normalize_title("Ñoño") == "nono"


def test_normalize_removes_quotes():
    assert normalize_title('He said "hello"') == "he said hello"


def test_normalize_removes_question_mark():
    assert normalize_title("What is life?") == "what is life"


def test_normalize_removes_apostrophe():
    assert normalize_title("Don't Stop") == "dont stop"


def test_normalize_removes_punctuation():
    assert normalize_title("One, Two: Three.") == "one two three"


def test_normalize_collapses_whitespace():
    assert normalize_title("  too   many   spaces  ") == "too many spaces"


def test_normalize_empty_string():
    assert normalize_title("") == ""


def test_normalize_only_punctuation():
    assert normalize_title("???...") == ""


# --- is_duplicate ---


def test_duplicate_by_uid():
    lib = [ref("smith2020", uid="abc123def456abcd")]
    candidate = ref("jones2021", uid="abc123def456abcd")
    assert is_duplicate(candidate, lib) == "smith2020"


def test_no_duplicate_different_uid():
    lib = [ref("smith2020", uid="abc123def456abcd")]
    candidate = ref("jones2021", uid="000000000000dead")
    assert is_duplicate(candidate, lib) is None


def test_no_uid_no_match():
    lib = [ref("smith2020", uid=None)]
    candidate = ref("jones2021", uid=None)
    assert is_duplicate(candidate, lib) is None


def test_empty_library():
    candidate = ref("jones2021", uid="abc123def456abcd")
    assert is_duplicate(candidate, []) is None


def test_returns_first_matching_citekey():
    lib = [
        ref("first2020", uid="abc123def456abcd"),
        ref("second2021", uid="abc123def456abcd"),
    ]
    candidate = ref("jones2022", uid="abc123def456abcd")
    assert is_duplicate(candidate, lib) == "first2020"
