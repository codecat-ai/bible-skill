from __future__ import annotations

import pytest

from bible_skill.references import ReferenceError, parse_reference


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("John", ("JHN", None, None, None, None)),
        ("John 3", ("JHN", 3, None, 3, None)),
        ("John 3:16", ("JHN", 3, 16, 3, 16)),
        ("John 3:16-18", ("JHN", 3, 16, 3, 18)),
        ("John 3:16-4:2", ("JHN", 3, 16, 4, 2)),
        ("JHN 3:16", ("JHN", 3, 16, 3, 16)),
        ("1 John 1:1", ("1JN", 1, 1, 1, 1)),
    ],
)
def test_parse_reference_normalizes_supported_forms(raw: str, expected: tuple) -> None:
    parsed = parse_reference(raw)

    assert (
        parsed.book.id,
        parsed.start_chapter,
        parsed.start_verse,
        parsed.end_chapter,
        parsed.end_verse,
    ) == expected


@pytest.mark.parametrize("raw", ["", "Unknown 1:1", "John three", "John 3:", "John 3:18-16"])
def test_parse_reference_rejects_invalid_input(raw: str) -> None:
    with pytest.raises(ReferenceError):
        parse_reference(raw)
