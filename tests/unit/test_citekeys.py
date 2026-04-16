from loretools.services.citekeys import generate, resolve_collision


def _ref(family=None, year=None, authors=None):
    ref = {"type": "article-journal"}
    if authors is not None:
        ref["author"] = authors
    elif family:
        ref["author"] = [{"family": family, "given": "J."}]
    if year:
        ref["issued"] = {"date-parts": [[year]]}
    return ref


def test_generate_standard():
    assert generate(_ref("Smith", 2020)) == "smith2020"


def test_generate_normalizes_diacritics():
    # García → garcia (diacríticos eliminados, no preservados)
    assert generate(_ref("García", 2019)) == "garcia2019"


def test_generate_normalizes_compound():
    assert generate(_ref("García-Méndez", 2021)) == "garciamendez2021"


def test_generate_missing_author_returns_ref_prefix():
    key = generate(_ref(year=2020))
    assert key.startswith("ref")
    assert len(key) == 9  # "ref" + 6 hex chars


def test_generate_missing_year_returns_ref_prefix():
    key = generate(_ref(family="Smith"))
    assert key.startswith("ref")


def test_generate_missing_both_returns_ref_prefix():
    key = generate({})
    assert key.startswith("ref")


def test_generate_two_authors():
    ref = _ref(authors=[{"family": "Star"}, {"family": "Griesemer"}], year=1989)
    assert generate(ref) == "star_griesemer1989"


def test_generate_three_plus_authors():
    ref = _ref(
        authors=[{"family": "Anand"}, {"family": "Gupta"}, {"family": "Appel"}],
        year=2018,
    )
    assert generate(ref) == "anand_etal2018"


def test_generate_literal_author():
    ref = {
        "type": "book",
        "author": [{"literal": "John Smith"}],
        "issued": {"date-parts": [[2020]]},
    }
    assert generate(ref) == "smith2020"


def test_generate_issued_none():
    ref = {"type": "article-journal", "author": [{"family": "Smith"}], "issued": None}
    key = generate(ref)
    assert key.startswith("ref")


def test_resolve_collision_no_collision():
    assert resolve_collision("smith2020", set()) == "smith2020"


def test_resolve_collision_appends_suffix():
    existing = {"smith2020"}
    assert resolve_collision("smith2020", existing) == "smith2020a"


def test_resolve_collision_chains():
    existing = {"smith2020", "smith2020a", "smith2020b"}
    assert resolve_collision("smith2020", existing) == "smith2020c"


def test_resolve_collision_exhausts_letters():
    existing = {"smith2020"} | {f"smith2020{c}" for c in "abcdefghijklmnopqrstuvwxyz"}
    result = resolve_collision("smith2020", existing)
    assert result.startswith("smith2020a")


# --- CitekeySettings config tests ---

from loretools.models import CitekeySettings  # noqa: E402


def _settings(**kwargs) -> CitekeySettings:
    return CitekeySettings(**kwargs)


def test_custom_separator():
    s = _settings(pattern="{author[2]}{year}", separator="-", etal="-etal")
    ref = _ref(authors=[{"family": "Star"}, {"family": "Griesemer"}], year=1989)
    assert generate(ref, s) == "star-griesemer1989"


def test_custom_etal():
    s = _settings(pattern="{author[2]}{year}", separator="_", etal="_et-al")
    ref = _ref(
        authors=[{"family": "Anand"}, {"family": "Gupta"}, {"family": "Appel"}],
        year=2018,
    )
    assert generate(ref, s) == "anand_et-al2018"


def test_author_limit_one():
    s = _settings(pattern="{author[1]}{year}", separator="_", etal="_etal")
    ref = _ref(authors=[{"family": "Star"}, {"family": "Griesemer"}], year=1989)
    assert generate(ref, s) == "star_etal1989"


def test_author_limit_three_allows_two():
    s = _settings(pattern="{author[3]}{year}", separator="_", etal="_etal")
    ref = _ref(authors=[{"family": "Star"}, {"family": "Griesemer"}], year=1989)
    assert generate(ref, s) == "star_griesemer1989"


def test_title_disambiguation():
    s = _settings(disambiguation_suffix="title2")
    ref = _ref("Smith", 2020)
    ref["title"] = "The Great Experiment"
    existing = {"smith2020"}
    result = resolve_collision("smith2020", existing, s, ref)
    assert result == "smith2020greatexperiment"


def test_title_disambiguation_skips_stop_words():
    s = _settings(disambiguation_suffix="title1")
    ref = _ref("Smith", 2020)
    ref["title"] = "The Revolution"
    existing = {"smith2020"}
    result = resolve_collision("smith2020", existing, s, ref)
    assert result == "smith2020revolution"


def test_title_disambiguation_falls_back_to_letters_when_no_title():
    s = _settings(disambiguation_suffix="title2")
    ref = _ref("Smith", 2020)
    existing = {"smith2020"}
    result = resolve_collision("smith2020", existing, s, ref)
    assert result == "smith2020a"


def test_title_disambiguation_falls_back_when_candidate_taken():
    s = _settings(disambiguation_suffix="title1")
    ref = _ref("Smith", 2020)
    ref["title"] = "Revolution"
    existing = {"smith2020", "smith2020revolution"}
    result = resolve_collision("smith2020", existing, s, ref)
    assert result == "smith2020a"


# --- CitekeySettings validation tests ---

import pytest  # noqa: E402


def test_settings_invalid_token():
    with pytest.raises(ValueError, match="unknown pattern token"):
        _settings(pattern="{author[2]}{initials}{year}")


def test_settings_empty_pattern():
    with pytest.raises(ValueError, match="at least one token"):
        _settings(pattern="prefix-only")


def test_settings_invalid_separator():
    with pytest.raises(ValueError, match="separator"):
        _settings(separator="__--")


def test_settings_invalid_etal():
    with pytest.raises(ValueError, match="etal"):
        _settings(etal="toolongvalue!")


def test_settings_invalid_disambiguation():
    with pytest.raises(ValueError, match="disambiguation_suffix"):
        _settings(disambiguation_suffix="title0")


def test_settings_invalid_disambiguation_free_text():
    with pytest.raises(ValueError, match="disambiguation_suffix"):
        _settings(disambiguation_suffix="uuid")
