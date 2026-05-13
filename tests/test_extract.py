from __future__ import annotations

from bible_skill.extract import extract_references


def test_extract_references_returns_ordered_normalized_rows_with_offsets() -> None:
    text = "Opening with John 3:16, then see JHN 3:16-4:2 and Genesis 1."

    rows = extract_references(text)

    assert [row.normalized_reference for row in rows] == [
        "John 3:16",
        "John 3:16-4:2",
        "Genesis 1",
    ]
    first = rows[0]
    assert first.matched_text == "John 3:16"
    assert text[first.start : first.end] == "John 3:16"
    assert first.book_id == "JHN"
    assert first.book_name == "John"
    assert first.start_chapter == 3
    assert first.start_verse == 16
    assert first.end_chapter == 3
    assert first.end_verse == 16


def test_extract_references_deduplicates_by_normalized_display() -> None:
    text = "John 3:16 starts it. JHN 3:16 repeats it. Romans 8:28-30 closes it."

    rows = extract_references(text)

    assert [row.normalized_reference for row in rows] == ["John 3:16", "Romans 8:28-30"]
    assert rows[0].matched_text == "John 3:16"


def test_extract_references_handles_wrapping_punctuation() -> None:
    text = "Read (Romans 8:28-30), then 'John 3:16'."

    rows = extract_references(text)

    assert [(row.matched_text, row.normalized_reference) for row in rows] == [
        ("Romans 8:28-30", "Romans 8:28-30"),
        ("John 3:16", "John 3:16"),
    ]


def test_extract_references_avoids_word_and_urlish_false_positives() -> None:
    text = "notJohn 3:16 https://example.test/John 3:16 valid John 3:16"

    rows = extract_references(text)

    assert [row.normalized_reference for row in rows] == ["John 3:16"]
    assert rows[0].matched_text == "John 3:16"
    assert rows[0].start == text.rindex("John 3:16")


def test_extracted_reference_to_dict_matches_cli_json_shape() -> None:
    row = extract_references("See JHN 3:16-4:2.")[0]

    assert row.to_dict() == {
        "matched_text": "JHN 3:16-4:2",
        "normalized_reference": "John 3:16-4:2",
        "start": 4,
        "end": 16,
        "book_id": "JHN",
        "book_name": "John",
        "start_chapter": 3,
        "start_verse": 16,
        "end_chapter": 4,
        "end_verse": 2,
    }
