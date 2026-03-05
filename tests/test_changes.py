import pytest

from app.domain.changes import replace_nth_occurrence, apply_replace_changes, TargetNotFoundError, ChangeValidationError


def test_replace_first_occurrence():
    text = "a b a b"
    new_text, start, end = replace_nth_occurrence(text, target="a", replacement="X", occurrence=1)
    assert new_text == "X b a b"
    assert (start, end) == (0, 1)


def test_replace_second_occurrence():
    text = "a b a b"
    new_text, start, end = replace_nth_occurrence(text, target="a", replacement="X", occurrence=2)
    assert new_text == "a b X b"
    assert (start, end) == (4, 5)


def test_occurrence_not_found():
    with pytest.raises(TargetNotFoundError):
        replace_nth_occurrence("hello", target="z", replacement="X", occurrence=1)


def test_empty_target_rejected():
    with pytest.raises(ChangeValidationError):
        replace_nth_occurrence("hello", target="", replacement="X", occurrence=1)


def test_apply_multiple_changes_sequentially():
    text = "alpha beta alpha beta"
    new_text, applied = apply_replace_changes(
        text,
        [
            {"target_text": "alpha", "occurrence": 2, "replacement": "ALPHA"},
            {"target_text": "beta", "occurrence": 1, "replacement": "BETA"},
        ],
    )
    assert new_text == "alpha BETA ALPHA beta"
    assert len(applied) == 2
