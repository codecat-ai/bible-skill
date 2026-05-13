from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from bible_skill.books import ALIASES
from bible_skill.references import Reference, ReferenceError, parse_reference


@dataclass(frozen=True)
class ExtractedReference:
    matched_text: str
    normalized_reference: str
    start: int
    end: int
    book_id: str
    book_name: str
    start_chapter: int | None
    start_verse: int | None
    end_chapter: int | None
    end_verse: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched_text": self.matched_text,
            "normalized_reference": self.normalized_reference,
            "start": self.start,
            "end": self.end,
            "book_id": self.book_id,
            "book_name": self.book_name,
            "start_chapter": self.start_chapter,
            "start_verse": self.start_verse,
            "end_chapter": self.end_chapter,
            "end_verse": self.end_verse,
        }


_BOOK_ALTERNATIVES = sorted(ALIASES, key=lambda alias: (len(alias.split()), len(alias)), reverse=True)
_BOOK_PATTERN = "|".join(re.escape(alias).replace(r"\ ", r"\s+") for alias in _BOOK_ALTERNATIVES)
_LOCATION_PATTERN = r"\d+(?::\d+(?:-(?:\d+|\d+:\d+))?)?"
_REFERENCE_RE = re.compile(
    rf"(?<![A-Za-z0-9:/._-])(?P<reference>(?:{_BOOK_PATTERN})\s+{_LOCATION_PATTERN})(?![A-Za-z0-9:/_-])",
    re.IGNORECASE,
)


def extract_references(text: str, *, deduplicate: bool = True) -> list[ExtractedReference]:
    rows: list[ExtractedReference] = []
    seen: set[str] = set()
    for match in _REFERENCE_RE.finditer(text):
        matched_text = match["reference"]
        try:
            reference = parse_reference(matched_text)
        except ReferenceError:
            continue
        row = _row_from_reference(matched_text, match.start("reference"), match.end("reference"), reference)
        if deduplicate and row.normalized_reference in seen:
            continue
        seen.add(row.normalized_reference)
        rows.append(row)
    return rows


def _row_from_reference(matched_text: str, start: int, end: int, reference: Reference) -> ExtractedReference:
    return ExtractedReference(
        matched_text=matched_text,
        normalized_reference=_format_reference(reference),
        start=start,
        end=end,
        book_id=reference.book.id,
        book_name=reference.book.name,
        start_chapter=reference.start_chapter,
        start_verse=reference.start_verse,
        end_chapter=reference.end_chapter,
        end_verse=reference.end_verse,
    )


def _format_reference(reference: Reference) -> str:
    if reference.start_chapter is None:
        return reference.book.name
    if reference.start_verse is None:
        return f"{reference.book.name} {reference.start_chapter}"
    if (reference.start_chapter, reference.start_verse) == (reference.end_chapter, reference.end_verse):
        return f"{reference.book.name} {reference.start_chapter}:{reference.start_verse}"
    if reference.start_chapter == reference.end_chapter:
        return f"{reference.book.name} {reference.start_chapter}:{reference.start_verse}-{reference.end_verse}"
    return (
        f"{reference.book.name} {reference.start_chapter}:{reference.start_verse}-"
        f"{reference.end_chapter}:{reference.end_verse}"
    )
