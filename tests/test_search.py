from __future__ import annotations

import pytest

from bible_skill.query import QueryError
from bible_skill.search import search_installed
from bible_skill.store import InstalledTranslation


def record(
    translation_id: str,
    name: str,
    language: str,
    license_url: str = "",
    source_url: str = "",
    verse_count: int = 8,
) -> InstalledTranslation:
    return InstalledTranslation(
        translation_id=translation_id,
        name=name,
        language=language,
        license_url=license_url,
        fetched_at="2026-01-01T00:00:00+00:00",
        source_url=source_url,
        book_count=3,
        chapter_count=4,
        verse_count=verse_count,
    )


def test_search_installed_matches_metadata_fields_case_insensitively() -> None:
    records = [
        record(
            "toy",
            "Toy Test Translation",
            "en",
            license_url="https://example.invalid/license",
            source_url="https://example.invalid/toy.json",
        ),
        record(
            "alt",
            "Alternate Fixture Translation",
            "de",
            license_url="https://rights.example.invalid/alternate",
            source_url="https://mirror.example.invalid/alt.json",
        ),
    ]

    assert [item.translation_id for item in search_installed(records, "TOY")] == ["toy"]
    assert [item.translation_id for item in search_installed(records, "fixture")] == ["alt"]
    assert [item.translation_id for item in search_installed(records, "DE")] == ["alt"]
    assert [item.translation_id for item in search_installed(records, "rights.example")] == ["alt"]
    assert [item.translation_id for item in search_installed(records, "toy.json")] == ["toy"]


def test_search_installed_rejects_blank_queries() -> None:
    with pytest.raises(QueryError, match="Search query cannot be blank"):
        search_installed([], "  ")
