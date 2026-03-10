from scholartools.models import Reference
from scholartools.services.duplicates import is_duplicate, normalize_title


def ref(id: str, title: str | None = None, isbn: str | list | None = None) -> Reference:
    extra = {}
    if isbn is not None:
        extra["ISBN"] = isbn
    return Reference(id=id, type="book", title=title, **extra)


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


def test_duplicate_by_exact_title():
    lib = [ref("smith2020", title="The Origin of Species")]
    candidate = ref("jones2021", title="The Origin of Species")
    assert is_duplicate(candidate, lib) == "smith2020"


def test_duplicate_title_case_insensitive():
    lib = [ref("smith2020", title="the origin of species")]
    candidate = ref("jones2021", title="THE ORIGIN OF SPECIES")
    assert is_duplicate(candidate, lib) == "smith2020"


def test_duplicate_title_diacritics():
    lib = [ref("smith2020", title="Resumen ejecutivo")]
    candidate = ref("jones2021", title="Résumen ejecutivo")
    assert is_duplicate(candidate, lib) == "smith2020"


def test_no_duplicate_different_titles():
    lib = [ref("smith2020", title="Introduction to Algorithms")]
    candidate = ref("jones2021", title="Advanced Data Structures")
    assert is_duplicate(candidate, lib) is None


def test_duplicate_by_isbn13():
    lib = [ref("smith2020", isbn="978-3-16-148410-0")]
    candidate = ref("jones2021", isbn="9783161484100")
    assert is_duplicate(candidate, lib) == "smith2020"


def test_duplicate_by_isbn10():
    lib = [ref("smith2020", isbn="0-306-40615-2")]
    candidate = ref("jones2021", isbn="0306406152")
    assert is_duplicate(candidate, lib) == "smith2020"


def test_duplicate_isbn10_vs_isbn13_different_numbers():
    lib = [ref("smith2020", isbn="0306406152")]
    candidate = ref("jones2021", isbn="9780306406157")
    # Different ISBN values — no match expected (not the same normalized string)
    assert is_duplicate(candidate, lib) is None


def test_no_duplicate_missing_isbn():
    lib = [ref("smith2020", title="A Book")]
    candidate = ref("jones2021", title="Other Book")
    assert is_duplicate(candidate, lib) is None


def test_no_duplicate_candidate_no_isbn_lib_has_isbn():
    lib = [ref("smith2020", isbn="9783161484100")]
    candidate = ref("jones2021", title="Some Title")
    assert is_duplicate(candidate, lib) is None


def test_empty_library():
    candidate = ref("jones2021", title="The Origin of Species")
    assert is_duplicate(candidate, []) is None


def test_no_title_no_isbn_no_match():
    lib = [ref("smith2020")]
    candidate = ref("jones2021")
    assert is_duplicate(candidate, lib) is None


def test_short_title_requires_exact_match():
    # "On" and "On" would match — that's correct; "On" vs "In" should not
    lib = [ref("smith2020", title="On")]
    candidate = ref("jones2021", title="In")
    assert is_duplicate(candidate, lib) is None


def test_isbn_list_field():
    lib = [ref("smith2020", isbn=["978-3-16-148410-0", "0-306-40615-2"])]
    candidate = ref("jones2021", isbn="0306406152")
    assert is_duplicate(candidate, lib) == "smith2020"


def test_returns_first_matching_citekey():
    lib = [
        ref("first2020", title="Matching Title"),
        ref("second2021", title="Matching Title"),
    ]
    candidate = ref("jones2022", title="Matching Title")
    assert is_duplicate(candidate, lib) == "first2020"
