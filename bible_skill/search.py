from __future__ import annotations

from collections.abc import Iterable

from bible_skill.query import QueryError
from bible_skill.store import InstalledTranslation


def search_installed(records: Iterable[InstalledTranslation], query: str) -> list[InstalledTranslation]:
    needle = query.strip().casefold()
    if not needle:
        raise QueryError("Search query cannot be blank.")

    return [record for record in records if _matches(record, needle)]


def _matches(record: InstalledTranslation, needle: str) -> bool:
    fields = (
        record.translation_id,
        record.name,
        record.language,
        record.license_url,
        record.source_url,
    )
    return any(needle in field.casefold() for field in fields)
