from __future__ import annotations

import re
from dataclasses import dataclass

from bible_skill.books import Book, match_book


class ReferenceError(ValueError):
    pass


@dataclass(frozen=True)
class Reference:
    book: Book
    start_chapter: int | None = None
    start_verse: int | None = None
    end_chapter: int | None = None
    end_verse: int | None = None

    @property
    def is_whole_book(self) -> bool:
        return self.start_chapter is None


_CHAPTER_RE = re.compile(r"^(?P<chapter>\d+)$")
_VERSE_RE = re.compile(r"^(?P<chapter>\d+):(?P<verse>\d+)$")
_SAME_CHAPTER_RANGE_RE = re.compile(r"^(?P<chapter>\d+):(?P<start>\d+)-(?P<end>\d+)$")
_CROSS_CHAPTER_RANGE_RE = re.compile(
    r"^(?P<start_chapter>\d+):(?P<start_verse>\d+)-(?P<end_chapter>\d+):(?P<end_verse>\d+)$"
)


def parse_reference(raw: str) -> Reference:
    value = raw.strip()
    if not value:
        raise ReferenceError("Reference is empty.")

    matched = match_book(value)
    if matched is None:
        raise ReferenceError(f"Unknown book in reference: {raw}")
    book, rest = matched

    if not rest:
        return Reference(book)

    if match := _CHAPTER_RE.fullmatch(rest):
        chapter = _positive(match["chapter"], "chapter")
        return Reference(book, chapter, None, chapter, None)

    if match := _VERSE_RE.fullmatch(rest):
        chapter = _positive(match["chapter"], "chapter")
        verse = _positive(match["verse"], "verse")
        return Reference(book, chapter, verse, chapter, verse)

    if match := _SAME_CHAPTER_RANGE_RE.fullmatch(rest):
        chapter = _positive(match["chapter"], "chapter")
        start = _positive(match["start"], "verse")
        end = _positive(match["end"], "verse")
        if end < start:
            raise ReferenceError("Range end must not come before range start.")
        return Reference(book, chapter, start, chapter, end)

    if match := _CROSS_CHAPTER_RANGE_RE.fullmatch(rest):
        start_chapter = _positive(match["start_chapter"], "chapter")
        start_verse = _positive(match["start_verse"], "verse")
        end_chapter = _positive(match["end_chapter"], "chapter")
        end_verse = _positive(match["end_verse"], "verse")
        if (end_chapter, end_verse) < (start_chapter, start_verse):
            raise ReferenceError("Range end must not come before range start.")
        return Reference(book, start_chapter, start_verse, end_chapter, end_verse)

    raise ReferenceError(f"Invalid reference syntax: {raw}")


def _positive(raw: str, label: str) -> int:
    value = int(raw)
    if value <= 0:
        raise ReferenceError(f"{label.title()} must be positive.")
    return value
