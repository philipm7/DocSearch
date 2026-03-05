from __future__ import annotations

from typing import Dict, Iterator


def iter_matches(
    text: str,
    query: str,
    context: int = 30,
    case_sensitive: bool = False,
) -> Iterator[Dict]:
    """
    Yield matches one-by-one as dicts:
      { start, end, snippet }

    This is memory-friendly for large documents.
    """
    if query is None or query == "":
        return
        yield  # pragma: no cover (keeps function as generator)

    haystack = text if case_sensitive else text.lower()
    needle = query if case_sensitive else query.lower()

    start = 0
    qlen = len(needle)

    while True:
        idx = haystack.find(needle, start)
        if idx == -1:
            break

        m_start = idx
        m_end = idx + qlen

        left = max(0, m_start - context)
        right = min(len(text), m_end + context)
        snippet = text[left:right]

        yield {"start": m_start, "end": m_end, "snippet": snippet}

        # Move forward by 1 to allow overlapping matches (e.g., "ana" in "banana")
        start = idx + 1
