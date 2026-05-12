from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    id: str
    osis: str
    name: str
    aliases: tuple[str, ...] = ()


BOOKS: tuple[Book, ...] = (
    Book("GEN", "Gen", "Genesis", ("gen",)),
    Book("EXO", "Exod", "Exodus", ("exod", "ex")),
    Book("LEV", "Lev", "Leviticus", ("lev",)),
    Book("NUM", "Num", "Numbers", ("num", "nm")),
    Book("DEU", "Deut", "Deuteronomy", ("deut", "deu", "dt")),
    Book("JOS", "Josh", "Joshua", ("josh", "jos")),
    Book("JDG", "Judg", "Judges", ("judg", "jdg")),
    Book("RUT", "Ruth", "Ruth", ("rut",)),
    Book("1SA", "1Sam", "1 Samuel", ("1 samuel", "1 sam", "i samuel", "first samuel")),
    Book("2SA", "2Sam", "2 Samuel", ("2 samuel", "2 sam", "ii samuel", "second samuel")),
    Book("1KI", "1Kgs", "1 Kings", ("1 kings", "1 kgs", "i kings", "first kings")),
    Book("2KI", "2Kgs", "2 Kings", ("2 kings", "2 kgs", "ii kings", "second kings")),
    Book("1CH", "1Chr", "1 Chronicles", ("1 chronicles", "1 chr", "i chronicles", "first chronicles")),
    Book("2CH", "2Chr", "2 Chronicles", ("2 chronicles", "2 chr", "ii chronicles", "second chronicles")),
    Book("EZR", "Ezra", "Ezra", ("ezr",)),
    Book("NEH", "Neh", "Nehemiah", ("neh",)),
    Book("EST", "Esth", "Esther", ("esth", "est")),
    Book("JOB", "Job", "Job"),
    Book("PSA", "Ps", "Psalms", ("psalm", "ps", "psa")),
    Book("PRO", "Prov", "Proverbs", ("prov", "pro")),
    Book("ECC", "Eccl", "Ecclesiastes", ("eccl", "ecc")),
    Book("SNG", "Song", "Song of Solomon", ("song", "songs", "song of songs", "sng")),
    Book("ISA", "Isa", "Isaiah", ("isa",)),
    Book("JER", "Jer", "Jeremiah", ("jer",)),
    Book("LAM", "Lam", "Lamentations", ("lam",)),
    Book("EZK", "Ezek", "Ezekiel", ("ezek", "ezk")),
    Book("DAN", "Dan", "Daniel", ("dan",)),
    Book("HOS", "Hos", "Hosea", ("hos",)),
    Book("JOL", "Joel", "Joel", ("jol",)),
    Book("AMO", "Amos", "Amos", ("amo",)),
    Book("OBA", "Obad", "Obadiah", ("obad", "oba")),
    Book("JON", "Jonah", "Jonah", ("jon",)),
    Book("MIC", "Mic", "Micah", ("mic",)),
    Book("NAM", "Nah", "Nahum", ("nah", "nam")),
    Book("HAB", "Hab", "Habakkuk", ("hab",)),
    Book("ZEP", "Zeph", "Zephaniah", ("zeph", "zep")),
    Book("HAG", "Hag", "Haggai", ("hag",)),
    Book("ZEC", "Zech", "Zechariah", ("zech", "zec")),
    Book("MAL", "Mal", "Malachi", ("mal",)),
    Book("MAT", "Matt", "Matthew", ("matt", "mat", "mt")),
    Book("MRK", "Mark", "Mark", ("mrk", "mk")),
    Book("LUK", "Luke", "Luke", ("luk", "lk")),
    Book("JHN", "John", "John", ("jhn", "jn")),
    Book("ACT", "Acts", "Acts", ("act",)),
    Book("ROM", "Rom", "Romans", ("rom",)),
    Book("1CO", "1Cor", "1 Corinthians", ("1 corinthians", "1 cor", "i corinthians", "first corinthians")),
    Book("2CO", "2Cor", "2 Corinthians", ("2 corinthians", "2 cor", "ii corinthians", "second corinthians")),
    Book("GAL", "Gal", "Galatians", ("gal",)),
    Book("EPH", "Eph", "Ephesians", ("eph",)),
    Book("PHP", "Phil", "Philippians", ("phil", "php")),
    Book("COL", "Col", "Colossians", ("col",)),
    Book("1TH", "1Thess", "1 Thessalonians", ("1 thessalonians", "1 thess", "i thessalonians")),
    Book("2TH", "2Thess", "2 Thessalonians", ("2 thessalonians", "2 thess", "ii thessalonians")),
    Book("1TI", "1Tim", "1 Timothy", ("1 timothy", "1 tim", "i timothy")),
    Book("2TI", "2Tim", "2 Timothy", ("2 timothy", "2 tim", "ii timothy")),
    Book("TIT", "Titus", "Titus", ("tit",)),
    Book("PHM", "Phlm", "Philemon", ("phlm", "phm")),
    Book("HEB", "Heb", "Hebrews", ("heb",)),
    Book("JAS", "Jas", "James", ("jas", "jam")),
    Book("1PE", "1Pet", "1 Peter", ("1 peter", "1 pet", "i peter")),
    Book("2PE", "2Pet", "2 Peter", ("2 peter", "2 pet", "ii peter")),
    Book("1JN", "1John", "1 John", ("1 john", "1 jn", "i john", "first john")),
    Book("2JN", "2John", "2 John", ("2 john", "2 jn", "ii john", "second john")),
    Book("3JN", "3John", "3 John", ("3 john", "3 jn", "iii john", "third john")),
    Book("JUD", "Jude", "Jude", ("jud",)),
    Book("REV", "Rev", "Revelation", ("rev", "revelations")),
)

BY_ID = {book.id: book for book in BOOKS}


def _key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower().replace(".", ""))


ALIASES: dict[str, Book] = {}
for _book in BOOKS:
    for _alias in (_book.id, _book.osis, _book.name, *_book.aliases):
        ALIASES[_key(_alias)] = _book


def match_book(reference: str) -> tuple[Book, str] | None:
    normalized = _key(reference)
    matches: list[tuple[int, Book, str]] = []
    for alias, book in ALIASES.items():
        if normalized == alias:
            matches.append((len(alias), book, ""))
        elif normalized.startswith(alias + " "):
            matches.append((len(alias), book, reference.strip()[len(alias) :].strip()))
    if not matches:
        return None
    _, book, rest = max(matches, key=lambda item: item[0])
    return book, rest
