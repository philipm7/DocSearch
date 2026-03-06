from app.domain.search import iter_matches


def test_search_finds_matches_and_snippets():
    text = "This contract is a contract."
    matches = list(iter_matches(text, "contract", context=5, case_sensitive=False))
    assert len(matches) == 2
    assert matches[0]["start"] == text.lower().find("contract")
    assert "contr" in matches[0]["snippet"].lower()


def test_search_case_sensitive():
    text = "Contract contract"
    insensitive = list(iter_matches(text, "contract", case_sensitive=False))
    sensitive = list(iter_matches(text, "contract", case_sensitive=True))
    assert len(insensitive) == 2
    assert len(sensitive) == 1


def test_search_allows_overlapping():
    text = "banana"
    # "ana" occurs at 1 and 3 if overlaps allowed
    matches = list(iter_matches(text, "ana", case_sensitive=True))
    assert [m["start"] for m in matches] == [1, 3]


def test_search_empty_query_yields_no_matches():
    text = "anything"
    assert list(iter_matches(text, "", case_sensitive=True)) == []
