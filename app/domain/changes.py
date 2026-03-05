from __future__ import annotations

from typing import List, Dict, Tuple


class ChangeValidationError(ValueError):
    """Raised when a change request is structurally valid JSON but semantically invalid."""


class TargetNotFoundError(ValueError):
    """Raised when the requested occurrence of the target text can't be found."""


def replace_nth_occurrence(text: str, target: str, replacement: str, occurrence: int) -> Tuple[str, int, int]:
    """
    Replace the Nth (1-based) occurrence of `target` in `text` with `replacement`.

    Returns: (new_text, found_start, found_end) where found_end is the end index
    (exclusive) of the matched target span in the *old* text.
    """
    if target is None or target == "":
        raise ChangeValidationError("target.text must be a non-empty string")
    if occurrence is None or occurrence < 1:
        raise ChangeValidationError("target.occurrence must be >= 1")

    start = 0
    found_at = -1
    for _ in range(occurrence):
        found_at = text.find(target, start)
        if found_at == -1:
            raise TargetNotFoundError(f"Could not find occurrence {occurrence} of target text")
        start = found_at + len(target)

    found_start = found_at
    found_end = found_at + len(target)
    new_text = text[:found_start] + replacement + text[found_end:]
    return new_text, found_start, found_end


def apply_replace_changes(text: str, changes: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    Apply a list of replace changes sequentially.

    `changes` items are dicts like:
      { "target_text": str, "occurrence": int, "replacement": str }

    Returns: (new_text, applied_changes_info)
    """
    if not isinstance(changes, list) or len(changes) == 0:
        raise ChangeValidationError("changes must be a non-empty list")

    current = text
    applied: List[Dict] = []

    for ch in changes:
        if not isinstance(ch, dict):
            raise ChangeValidationError("each change must be an object/dict")

        target_text = ch.get("target_text")
        occurrence = ch.get("occurrence")
        replacement = ch.get("replacement", "")

        new_text, found_start, found_end = replace_nth_occurrence(
            current, target=target_text, replacement=replacement, occurrence=occurrence
        )

        applied.append(
            {
                "target_text": target_text,
                "occurrence": occurrence,
                "replacement": replacement,
                "found_start": found_start,
                "found_end": found_end,
            }
        )
        current = new_text

    return current, applied
