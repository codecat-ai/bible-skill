from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bible_skill.books import BY_ID, Book
from bible_skill.references import Reference, ReferenceError, parse_reference


class QueryError(ValueError):
    pass


@dataclass(frozen=True)
class VerseResult:
    reference: str
    text: str


@dataclass(frozen=True)
class PassageResult:
    translation_id: str
    translation_name: str
    normalized_reference: str
    verses: list[VerseResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "translation_id": self.translation_id,
            "translation_name": self.translation_name,
            "reference": self.normalized_reference,
            "verses": [verse.__dict__ for verse in self.verses],
        }


def render_usfm(passage: PassageResult) -> str:
    lines = [
        rf"\id {_usfm_text(passage.translation_id)}",
        rf"\h {_usfm_text(passage.translation_name)}",
    ]
    current_chapter: int | None = None
    for verse in passage.verses:
        chapter, verse_number = _reference_chapter_verse(verse.reference)
        if chapter != current_chapter:
            lines.append(rf"\c {chapter}")
            current_chapter = chapter
        lines.append(rf"\v {verse_number} {_usfm_text(verse.text)}")
    return "\n".join(lines)


def render_markdown(passage: PassageResult) -> str:
    lines = [f"# {_markdown_text(passage.normalized_reference)} ({_markdown_text(passage.translation_id)})", ""]
    for verse in passage.verses:
        lines.append(f"- **{_markdown_text(verse.reference)}** {_markdown_text(verse.text)}")
    return "\n".join(lines)


def query_passage(translation: dict[str, Any], raw_reference: str) -> PassageResult:
    try:
        reference = parse_reference(raw_reference)
    except ReferenceError as exc:
        raise QueryError(str(exc)) from exc

    data = normalize_translation(translation)
    book = data["books"].get(reference.book.id)
    if book is None:
        raise QueryError(f"Book is not available in this translation: {reference.book.name}")

    selected = _select_verses(reference, book)
    if not selected:
        raise QueryError(f"No verses found for reference: {raw_reference}")

    verses = [
        VerseResult(reference=_format_verse(reference.book, chapter, verse), text=text)
        for chapter, verse, text in selected
    ]
    metadata = data["metadata"]
    return PassageResult(
        translation_id=metadata.get("id", "unknown"),
        translation_name=metadata.get("name", metadata.get("id", "unknown")),
        normalized_reference=_format_range(reference.book, selected),
        verses=verses,
    )


def normalize_translation(translation: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(translation.get("metadata") or translation.get("translation") or {})
    if "id" not in metadata and translation.get("id"):
        metadata["id"] = translation["id"]
    if "name" not in metadata and translation.get("name"):
        metadata["name"] = translation["name"]

    books: dict[str, dict[int, dict[int, str]]] = {}
    for raw_book in _iter_books(translation):
        book_id = _book_id(raw_book)
        if book_id not in BY_ID:
            continue
        chapters: dict[int, dict[int, str]] = {}
        for chapter_number, raw_chapter in _iter_chapters(raw_book):
            verses = {
                verse_number: text for verse_number, text in _iter_verses(raw_chapter) if verse_number > 0 and text
            }
            if verses:
                chapters[chapter_number] = verses
        if chapters:
            books[book_id] = chapters
    return {"metadata": metadata, "books": books}


def _iter_books(translation: dict[str, Any]) -> list[Any]:
    books = translation.get("books") or translation.get("data") or []
    if isinstance(books, dict):
        return list(books.values())
    return list(books)


def _book_id(raw_book: dict[str, Any]) -> str:
    for key in ("id", "book_id", "usfm", "abbrev"):
        value = raw_book.get(key)
        if isinstance(value, str):
            return value.upper()
    name = raw_book.get("name")
    if isinstance(name, str):
        from bible_skill.books import match_book

        matched = match_book(name)
        if matched:
            return matched[0].id
    return ""


def _iter_chapters(raw_book: dict[str, Any]) -> list[tuple[int, Any]]:
    chapters = raw_book.get("chapters") or []
    if isinstance(chapters, dict):
        return [(int(number), chapter) for number, chapter in chapters.items()]
    output = []
    for index, chapter in enumerate(chapters, start=1):
        nested = chapter.get("chapter") if isinstance(chapter, dict) else None
        number = chapter.get("number") if isinstance(chapter, dict) else None
        if number is None and isinstance(nested, dict):
            number = nested.get("number")
        number = number or index
        output.append((int(number), chapter))
    return output


def _iter_verses(raw_chapter: Any) -> list[tuple[int, str]]:
    if isinstance(raw_chapter, dict) and "chapter" in raw_chapter:
        raw_chapter = raw_chapter["chapter"]
    if isinstance(raw_chapter, dict):
        verses = raw_chapter.get("verses") or raw_chapter.get("content") or []
    else:
        verses = raw_chapter
    if isinstance(verses, dict):
        return [(int(number), str(text)) for number, text in verses.items()]
    output = []
    for index, verse in enumerate(verses or [], start=1):
        if isinstance(verse, str):
            output.append((index, verse))
            continue
        if not isinstance(verse, dict) or verse.get("type", "verse") != "verse":
            continue
        number = verse.get("number") or verse.get("verse") or index
        text = verse.get("text") or verse.get("content") or ""
        if isinstance(text, list):
            text = " ".join("".join(part if isinstance(part, str) else " " for part in text).split())
        output.append((int(number), str(text)))
    return output


def _select_verses(reference: Reference, book: dict[int, dict[int, str]]) -> list[tuple[int, int, str]]:
    if reference.is_whole_book:
        chapter_numbers = sorted(book)
        return _collect(book, chapter_numbers[0], None, chapter_numbers[-1], None)

    assert reference.start_chapter is not None
    if reference.start_chapter not in book:
        raise QueryError(f"Requested chapter is out of range: {reference.start_chapter}")

    end_chapter = reference.end_chapter or reference.start_chapter
    if end_chapter not in book:
        raise QueryError(f"Requested chapter is out of range: {end_chapter}")

    if reference.start_verse is None:
        return _collect(book, reference.start_chapter, None, reference.start_chapter, None)

    assert reference.end_verse is not None
    _require_verse(book, reference.start_chapter, reference.start_verse)
    _require_verse(book, end_chapter, reference.end_verse)
    return _collect(book, reference.start_chapter, reference.start_verse, end_chapter, reference.end_verse)


def _collect(
    book: dict[int, dict[int, str]],
    start_chapter: int,
    start_verse: int | None,
    end_chapter: int,
    end_verse: int | None,
) -> list[tuple[int, int, str]]:
    selected = []
    for chapter in sorted(book):
        if chapter < start_chapter or chapter > end_chapter:
            continue
        for verse in sorted(book[chapter]):
            if chapter == start_chapter and start_verse is not None and verse < start_verse:
                continue
            if chapter == end_chapter and end_verse is not None and verse > end_verse:
                continue
            selected.append((chapter, verse, book[chapter][verse]))
    return selected


def _require_verse(book: dict[int, dict[int, str]], chapter: int, verse: int) -> None:
    if verse not in book[chapter]:
        raise QueryError(f"Requested verse is out of range: {chapter}:{verse}")


def _format_verse(book: Book, chapter: int, verse: int) -> str:
    return f"{book.name} {chapter}:{verse}"


def _format_range(book: Book, selected: list[tuple[int, int, str]]) -> str:
    start_chapter, start_verse, _ = selected[0]
    end_chapter, end_verse, _ = selected[-1]
    if (start_chapter, start_verse) == (end_chapter, end_verse):
        return _format_verse(book, start_chapter, start_verse)
    if start_chapter == end_chapter:
        return f"{book.name} {start_chapter}:{start_verse}-{end_verse}"
    return f"{book.name} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}"


def _reference_chapter_verse(reference: str) -> tuple[int, int]:
    location = reference.rsplit(" ", maxsplit=1)[-1]
    chapter, verse = location.split(":", maxsplit=1)
    return int(chapter), int(verse)


def _usfm_text(value: str) -> str:
    return " ".join(str(value).replace("\\", "/").split())


def _markdown_text(value: str) -> str:
    text = " ".join(str(value).split())
    escaped = text.replace("\\", "\\\\")
    for char in ("`", "*", "_", "[", "]", "#", "|", "<", ">"):
        escaped = escaped.replace(char, f"\\{char}")
    return escaped.replace("- ", "\\- ")
