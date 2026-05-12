from __future__ import annotations

import pytest

from bible_skill.query import QueryError, query_passage, render_usfm
from tests.fixtures import tiny_translation


def test_query_whole_book_returns_ordered_verses() -> None:
    result = query_passage(tiny_translation(), "John")

    assert result.normalized_reference == "John 3:16-4:2"
    assert [verse.reference for verse in result.verses] == [
        "John 3:16",
        "John 3:17",
        "John 3:18",
        "John 4:1",
        "John 4:2",
    ]


def test_query_chapter_single_verse_and_ranges() -> None:
    translation = tiny_translation()

    assert query_passage(translation, "John 3").normalized_reference == "John 3:16-18"
    assert query_passage(translation, "John 3:16").verses[0].text == "Fixture loved line."
    assert [v.reference for v in query_passage(translation, "John 3:16-18").verses] == [
        "John 3:16",
        "John 3:17",
        "John 3:18",
    ]
    assert [v.reference for v in query_passage(translation, "John 3:18-4:1").verses] == [
        "John 3:18",
        "John 4:1",
    ]


def test_query_aliases_numeric_book_names() -> None:
    result = query_passage(tiny_translation(), "1 John 1:1")

    assert result.normalized_reference == "1 John 1:1"
    assert result.verses[0].text == "Fixture first letter line."


def test_query_normalizes_free_use_bible_api_chapter_content_shape() -> None:
    translation = {
        "translation": {"id": "shape", "name": "Shape Fixture"},
        "books": [
            {
                "id": "JHN",
                "chapters": [
                    {
                        "chapter": {
                            "number": 3,
                            "content": [
                                {"type": "heading", "content": ["Fixture heading"]},
                                {
                                    "type": "verse",
                                    "number": 16,
                                    "content": ["Fixture ", {"noteId": 1}, "API line."],
                                },
                            ],
                        }
                    }
                ],
            }
        ],
    }

    result = query_passage(translation, "John 3:16")

    assert result.translation_id == "shape"
    assert result.verses[0].text == "Fixture API line."


def test_render_usfm_exports_cross_chapter_passage() -> None:
    result = query_passage(tiny_translation(), "John 3:18-4:1")

    assert render_usfm(result) == "\n".join(
        [
            r"\id toy",
            r"\h Toy Test Translation",
            r"\c 3",
            r"\v 18 Fixture believed line.",
            r"\c 4",
            r"\v 1 Fixture travel line.",
        ]
    )


def test_render_usfm_normalizes_unsafe_verse_text() -> None:
    translation = tiny_translation()
    translation["books"][1]["chapters"][0]["verses"][0]["text"] = "  First\\id bad\n\n   second\t\\v marker   text.  "
    result = query_passage(translation, "John 3:16")

    assert render_usfm(result).splitlines() == [
        r"\id toy",
        r"\h Toy Test Translation",
        r"\c 3",
        r"\v 16 First/id bad second /v marker text.",
    ]


def test_query_reports_out_of_range() -> None:
    with pytest.raises(QueryError, match="chapter"):
        query_passage(tiny_translation(), "John 9")

    with pytest.raises(QueryError, match="verse"):
        query_passage(tiny_translation(), "John 3:99")
