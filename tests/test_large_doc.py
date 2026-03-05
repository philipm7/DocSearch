import pytest

from app.domain.changes import replace_nth_occurrence
from app.domain.search import iter_matches


@pytest.mark.performance
def test_large_document_replace_and_search():
    # ~10MB string: "abc " is 4 chars => 2.5M * 4 = 10M chars
    text = ("abc " * 2_500_000)

    new_text, start, end = replace_nth_occurrence(text, target="abc", replacement="xyz", occurrence=1)
    assert start == 0
    assert end == 3
    assert new_text.startswith("xyz ")

    # Pull only a few matches to keep memory bounded
    out = []
    for m in iter_matches(new_text, "abc"):
        out.append(m)
        if len(out) == 5:
            break
    assert len(out) == 5
