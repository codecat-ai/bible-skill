from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from bible_skill.cli import _render_compare_csv, _render_live_csv, main
from bible_skill.providers import BibleApiClient
from bible_skill.query import PassageResult, VerseResult
from bible_skill.store import Store
from tests.fixtures import tiny_translation


def seed_translation(path: Path) -> None:
    Store(path).save_translation("toy", tiny_translation())


def seed_second_translation(path: Path) -> None:
    data = tiny_translation()
    data["metadata"] = {
        **data["metadata"],
        "id": "alt",
        "name": "Alternate Fixture Translation",
        "language": "de",
        "source_url": "https://mirror.example.invalid/alternate.json",
    }
    data["books"][1]["chapters"][0]["verses"][0]["text"] = "Alternate loved line."
    Store(path).save_translation("alt", data)


def seed_markdown_sensitive_translation(path: Path) -> None:
    data = tiny_translation()
    data["metadata"] = {
        **data["metadata"],
        "id": "md",
        "name": "# Heading | Translation",
    }
    data["books"][1]["chapters"][0]["verses"][0]["text"] = "Fixture loved line.\n- accidental list | table"
    Store(path).save_translation("md", data)


def test_cli_query_json_outputs_machine_readable_passage(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["translation_id"] == "toy"
    assert payload["reference"] == "John 3:16"
    assert payload["verses"] == [{"reference": "John 3:16", "text": "Fixture loved line."}]


def test_cli_query_json_includes_attribution_when_requested(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--json", "--attribution"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["attribution"] == {
        "license_url": "https://example.invalid/license",
    }


def test_cli_query_json_without_attribution_preserves_existing_shape(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "attribution" not in payload


def test_cli_query_usfm_outputs_minimal_passage(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:18-4:1", "--usfm"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        r"\id toy",
        r"\h Toy Test Translation",
        r"\c 3",
        r"\v 18 Fixture believed line.",
        r"\c 4",
        r"\v 1 Fixture travel line.",
    ]


def test_cli_query_usfm_includes_attribution_when_requested(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--usfm", "--attribution"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        r"\id toy",
        r"\h Toy Test Translation",
        r"\rem License: https://example.invalid/license",
        r"\c 3",
        r"\v 16 Fixture loved line.",
    ]


def test_cli_query_markdown_outputs_note_friendly_passage(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16-17", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# John 3:16-17 (toy)",
        "",
        "- **John 3:16** Fixture loved line.",
        "- **John 3:17** Fixture sent line.",
    ]


def test_cli_query_markdown_includes_attribution_when_requested(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--markdown", "--attribution"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# John 3:16 (toy)",
        "",
        "> License: https://example.invalid/license",
        "",
        "- **John 3:16** Fixture loved line.",
    ]


def test_cli_query_text_includes_attribution_when_requested(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--attribution"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "toy John 3:16",
        "License: https://example.invalid/license",
        "John 3:16 Fixture loved line.",
    ]


def test_cli_query_markdown_escapes_sensitive_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = tiny_translation()
    data["metadata"]["id"] = "md"
    data["books"][1]["chapters"][0]["verses"][0]["text"] = "Text with *stars*, [link], <tag>"
    Store(tmp_path).save_translation("md", data)

    code = main(["--data-dir", str(tmp_path), "query", "md", "John 3:16", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# John 3:16 (md)",
        "",
        "- **John 3:16** Text with \\*stars\\*, \\[link\\], \\<tag\\>",
    ]


def test_cli_query_rejects_json_and_usfm_together(tmp_path: Path) -> None:
    seed_translation(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--json", "--usfm"])

    assert exc_info.value.code == 2


@pytest.mark.parametrize("command", ["query", "compare"])
def test_cli_local_export_help_mentions_attribution(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([command, "--help"])

    assert exc_info.value.code == 0
    assert "--attribution" in capsys.readouterr().out


@pytest.mark.parametrize("other_flag", ["--json", "--usfm"])
def test_cli_query_rejects_markdown_with_other_output_modes(tmp_path: Path, other_flag: str) -> None:
    seed_translation(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--markdown", other_flag])

    assert exc_info.value.code == 2


def test_cli_reports_missing_translation_friendly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--data-dir", str(tmp_path), "query", "missing", "John 3:16"])

    assert code == 2
    captured = capsys.readouterr()
    assert "missing local translation" in captured.err.lower()


def test_cli_installed_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "installed", "--json"])

    assert code == 0
    assert json.loads(capsys.readouterr().out)[0]["translation_id"] == "toy"


def test_cli_validate_text_reports_cache_status(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "validate", "toy"])

    assert code == 0
    output = capsys.readouterr().out.strip()
    assert output.startswith("toy\tok\tsha256:")


def test_cli_validate_json_reports_issue_lists(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)
    path = tmp_path / "translations" / "toy" / "translation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["metadata"]["checksum"] = "sha256:" + ("0" * 64)
    path.write_text(json.dumps(data), encoding="utf-8")

    code = main(["--data-dir", str(tmp_path), "validate", "toy", "missing", "--json"])

    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload == [
        {
            "translation_id": "toy",
            "ok": False,
            "checksum": Store(tmp_path).translation_checksum(data),
            "issues": [
                "metadata.checksum does not match translation content",
                "metadata.json.checksum does not match translation.json metadata",
            ],
        },
        {
            "translation_id": "missing",
            "ok": False,
            "checksum": "",
            "issues": ["translation cache is missing"],
        },
    ]


def test_cli_validate_json_reports_sidecar_metadata_issues(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)
    (tmp_path / "translations" / "toy" / "metadata.json").unlink()

    code = main(["--data-dir", str(tmp_path), "validate", "toy", "--json"])

    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["translation_id"] == "toy"
    assert payload[0]["ok"] is False
    assert payload[0]["issues"] == ["metadata.json is missing"]


def test_cli_validate_without_ids_checks_installed_translations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "validate"])

    assert code == 0
    assert [line.split("\t")[:2] for line in capsys.readouterr().out.splitlines()] == [
        ["alt", "ok"],
        ["toy", "ok"],
    ]


def test_cli_validate_without_ids_reports_broken_cache_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "translations" / "broken"
    path.mkdir(parents=True)
    (path / "translation.json").write_text("{", encoding="utf-8")

    code = main(["--data-dir", str(tmp_path), "validate", "--json"])

    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload == [
        {
            "translation_id": "broken",
            "ok": False,
            "checksum": "",
            "issues": ["translation.json is invalid JSON: Expecting property name enclosed in double quotes"],
        }
    ]


def test_cli_cache_manifest_json_writes_manifest_to_stdout_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "cache", "manifest", "--json"])

    assert code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["schema_version"] == 1
    assert payload["data_dir"] == str(tmp_path)
    assert payload["translations"][0]["id"] == "toy"
    assert payload["translations"][0]["relative_path"] == "translations/toy/translation.json"
    assert payload["translations"][0]["validation_ok"] is True


def test_cli_cache_manifest_text_summarizes_valid_and_invalid_entries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)
    path = tmp_path / "translations" / "broken"
    path.mkdir(parents=True)
    (path / "translation.json").write_text("{", encoding="utf-8")

    code = main(["--data-dir", str(tmp_path), "cache", "manifest"])

    assert code == 0
    output = capsys.readouterr().out.splitlines()
    assert output[0] == f"Cache manifest for {tmp_path}"
    assert output[1] == (
        "broken\tinvalid\ttranslations/broken/translation.json\t"
        "translation.json is invalid JSON: Expecting property name enclosed in double quotes"
    )
    assert output[2].startswith("toy\tok\ttranslations/toy/translation.json\tsha256:")


def test_cli_search_text_outputs_local_metadata_matches(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "search", "mirror.example"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "alt\tAlternate Fixture Translation\tde\t8 verses",
    ]


def test_cli_search_json_outputs_local_metadata_matches(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "search", "fixture", "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [row["translation_id"] for row in payload] == ["alt"]
    assert payload[0]["source_url"] == "https://mirror.example.invalid/alternate.json"


def test_cli_search_rejects_blank_query(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--data-dir", str(tmp_path), "search", "  "])

    assert code == 2
    assert "Search query cannot be blank" in capsys.readouterr().err


def test_cli_extract_text_outputs_normalized_references(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["extract", "--text", "See John 3:16, then JHN 3:16 and Genesis 1."])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == ["John 3:16", "Genesis 1"]


def test_cli_extract_file_json_outputs_machine_readable_rows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text("Discuss Romans 8:28-30 and JHN 3:16-4:2.", encoding="utf-8")

    code = main(["extract", "--file", str(notes), "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == [
        {
            "matched_text": "Romans 8:28-30",
            "normalized_reference": "Romans 8:28-30",
            "start": 8,
            "end": 22,
            "book_id": "ROM",
            "book_name": "Romans",
            "start_chapter": 8,
            "start_verse": 28,
            "end_chapter": 8,
            "end_verse": 30,
        },
        {
            "matched_text": "JHN 3:16-4:2",
            "normalized_reference": "John 3:16-4:2",
            "start": 27,
            "end": 39,
            "book_id": "JHN",
            "book_name": "John",
            "start_chapter": 3,
            "start_verse": 16,
            "end_chapter": 4,
            "end_verse": 2,
        },
    ]


def test_cli_extract_text_markdown_exports_note_friendly_summary(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["extract", "--text", "See John 3:16 and Romans 8:28-30", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# Extracted Bible references",
        "",
        "- **John 3:16** See John 3:16 and Romans 8:28-30",
        "- **Romans 8:28-30** See John 3:16 and Romans 8:28-30",
    ]


def test_cli_extract_file_markdown_escapes_source_context(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text("Topic: *See* John 3:16 - discuss | table\n", encoding="utf-8")

    code = main(["extract", "--file", str(notes), "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# Extracted Bible references",
        "",
        "- **John 3:16** Topic: \\*See\\* John 3:16 \\- discuss \\| table",
    ]


def test_cli_extract_file_csv_exports_spreadsheet_rows_with_source_context(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text(
        'First line: "quote", John 3:16\nSecond line: Romans 8:28-30, review\n',
        encoding="utf-8",
    )

    code = main(["extract", "--file", str(notes), "--csv"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "reference,book,chapter,start_verse,end_verse,start,end,context",
        'John 3:16,John,3,16,16,21,30,"First line: ""quote"", John 3:16"',
        'Romans 8:28-30,Romans,8,28,30,44,58,"Second line: Romans 8:28-30, review"',
    ]


def test_cli_extract_csv_reports_header_only_when_no_matches(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["extract", "--text", "No references in this note.", "--csv"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "reference,book,chapter,start_verse,end_verse,start,end,context",
    ]


def test_cli_extract_markdown_reports_no_matches(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["extract", "--text", "No references in this note.", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# Extracted Bible references",
        "",
        "No Bible references found.",
    ]


@pytest.mark.parametrize("other_flag", ["--json", "--markdown"])
def test_cli_extract_rejects_csv_with_other_output_modes(other_flag: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["extract", "--text", "John 3:16", "--csv", other_flag])

    assert exc_info.value.code == 2


def test_cli_extract_rejects_json_and_markdown_together() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["extract", "--text", "John 3:16", "--json", "--markdown"])

    assert exc_info.value.code == 2


def test_cli_extract_rejects_text_and_file_together(tmp_path: Path) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text("John 3:16", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["extract", "--text", "John 3:16", "--file", str(notes)])

    assert exc_info.value.code == 2


def test_cli_compare_json_aligns_multiple_local_translations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt", "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "reference": "John 3:16",
        "translations": [
            {
                "translation_id": "toy",
                "translation_name": "Toy Test Translation",
                "verses": [{"reference": "John 3:16", "text": "Fixture loved line."}],
            },
            {
                "translation_id": "alt",
                "translation_name": "Alternate Fixture Translation",
                "verses": [{"reference": "John 3:16", "text": "Alternate loved line."}],
            },
        ],
    }


def test_cli_compare_json_includes_per_translation_attribution_when_requested(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt", "--json", "--attribution"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["translations"][0]["attribution"] == {
        "license_url": "https://example.invalid/license",
    }
    assert payload["translations"][1]["attribution"] == {
        "license_url": "https://example.invalid/license",
        "source_url": "https://mirror.example.invalid/alternate.json",
    }


def test_cli_compare_json_without_attribution_preserves_existing_shape(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt", "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "attribution" not in payload["translations"][0]


def test_cli_compare_text_prints_translation_labels(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "John 3:16",
        "[toy] Toy Test Translation",
        "John 3:16 Fixture loved line.",
        "[alt] Alternate Fixture Translation",
        "John 3:16 Alternate loved line.",
    ]


def test_cli_compare_csv_includes_stable_attribution_columns_when_requested(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt", "--csv", "--attribution"])

    assert code == 0
    assert list(csv.reader(io.StringIO(capsys.readouterr().out))) == [
        [
            "reference",
            "translation_id",
            "translation_name",
            "license_url",
            "source_url",
            "verse_reference",
            "text",
        ],
        [
            "John 3:16",
            "toy",
            "Toy Test Translation",
            "https://example.invalid/license",
            "",
            "John 3:16",
            "Fixture loved line.",
        ],
        [
            "John 3:16",
            "alt",
            "Alternate Fixture Translation",
            "https://example.invalid/license",
            "https://mirror.example.invalid/alternate.json",
            "John 3:16",
            "Alternate loved line.",
        ],
    ]


def test_cli_compare_markdown_exports_readable_sections(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)
    seed_markdown_sensitive_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "md", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# John 3:16",
        "",
        "## toy — Toy Test Translation",
        "",
        "- **John 3:16** Fixture loved line.",
        "",
        "## md — \\# Heading \\| Translation",
        "",
        "- **John 3:16** Fixture loved line. \\- accidental list \\| table",
    ]


def test_render_compare_csv_exports_escaped_rows_in_translation_order() -> None:
    output = _render_compare_csv(
        "John 3:16-17",
        [
            PassageResult(
                translation_id="toy",
                translation_name='Toy, "Quoted" Translation',
                normalized_reference="John 3:16-17",
                verses=[
                    VerseResult(reference="John 3:16", text='Fixture, "loved" line.'),
                    VerseResult(reference="John 3:17", text="Fixture sent\nline."),
                ],
            ),
            PassageResult(
                translation_id="alt",
                translation_name="Alternate Fixture Translation",
                normalized_reference="John 3:16-17",
                verses=[VerseResult(reference="John 3:16", text="Alternate loved line.")],
            ),
        ],
    )

    assert list(csv.reader(io.StringIO(output))) == [
        ["reference", "translation_id", "translation_name", "verse_reference", "text"],
        ["John 3:16-17", "toy", 'Toy, "Quoted" Translation', "John 3:16", 'Fixture, "loved" line.'],
        ["John 3:16-17", "toy", 'Toy, "Quoted" Translation', "John 3:17", "Fixture sent\nline."],
        ["John 3:16-17", "alt", "Alternate Fixture Translation", "John 3:16", "Alternate loved line."],
    ]


def test_cli_compare_csv_exports_spreadsheet_rows(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "compare", "John 3:16-17", "alt", "toy", "--csv"])

    assert code == 0
    assert list(csv.reader(io.StringIO(capsys.readouterr().out))) == [
        ["reference", "translation_id", "translation_name", "verse_reference", "text"],
        ["John 3:16-17", "alt", "Alternate Fixture Translation", "John 3:16", "Alternate loved line."],
        ["John 3:16-17", "alt", "Alternate Fixture Translation", "John 3:17", "Fixture sent line."],
        ["John 3:16-17", "toy", "Toy Test Translation", "John 3:16", "Fixture loved line."],
        ["John 3:16-17", "toy", "Toy Test Translation", "John 3:17", "Fixture sent line."],
    ]


def test_cli_compare_rejects_json_and_markdown_together(tmp_path: Path) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt", "--json", "--markdown"])

    assert exc_info.value.code == 2


@pytest.mark.parametrize("other_flag", ["--json", "--markdown"])
def test_cli_compare_rejects_csv_with_other_output_modes(tmp_path: Path, other_flag: str) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt", "--csv", other_flag])

    assert exc_info.value.code == 2


def test_cli_live_markdown_exports_verse_list(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_passage(
        self: BibleApiClient, reference: str, translation: str = "web", *, timeout: float = 30, retries: int = 0
    ) -> dict[str, object]:
        assert reference == "John 3:16-17"
        assert translation == "web"
        return {
            "reference": "John 3:16-17",
            "verses": [
                {"book_name": "John", "chapter": 3, "verse": 16, "text": "For God loved."},
                {"book_name": "John", "chapter": 3, "verse": 17, "text": "For God sent."},
            ],
        }

    monkeypatch.setattr(BibleApiClient, "passage", fake_passage)

    code = main(["live", "John 3:16-17", "--translation", "web", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# John 3:16-17",
        "",
        "- **John 3:16** For God loved.",
        "- **John 3:17** For God sent.",
    ]


def test_cli_live_markdown_escapes_sensitive_text(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_passage(
        self: BibleApiClient, reference: str, translation: str = "web", *, timeout: float = 30, retries: int = 0
    ) -> dict[str, object]:
        return {
            "reference": "# John 3:16",
            "verses": [
                {
                    "book_name": "John",
                    "chapter": 3,
                    "verse": 16,
                    "text": "Text with *stars*\n- accidental list | table",
                }
            ],
        }

    monkeypatch.setattr(BibleApiClient, "passage", fake_passage)

    code = main(["live", "John 3:16", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# \\# John 3:16",
        "",
        "- **John 3:16** Text with \\*stars\\* \\- accidental list \\| table",
    ]


def test_cli_live_markdown_exports_top_level_text_when_no_verses(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_passage(
        self: BibleApiClient, reference: str, translation: str = "web", *, timeout: float = 30, retries: int = 0
    ) -> dict[str, object]:
        return {
            "reference": "John 3:16",
            "text": "  Top-level\n\ntext with\tspacing.  ",
        }

    monkeypatch.setattr(BibleApiClient, "passage", fake_passage)

    code = main(["live", "John 3:16", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# John 3:16",
        "",
        "- **John 3:16** Top-level text with spacing.",
    ]


def test_cli_live_markdown_renders_data_wrapped_passages_with_nested_fragments(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_passage(
        self: BibleApiClient, reference: str, translation: str = "web", *, timeout: float = 30, retries: int = 0
    ) -> dict[str, object]:
        return {
            "data": {
                "reference": "John 3:16-17",
                "translation": "WEB",
                "passages": [
                    {
                        "reference": "John 3:16",
                        "content": [
                            "For God",
                            {"text": "so loved"},
                            ["the world", {"content": "that he gave"}],
                        ],
                    },
                    {
                        "reference": "John 3:17",
                        "verse_text": [
                            {"content": "For God did not send"},
                            ["his Son", {"text": "to condemn"}],
                        ],
                    },
                ],
            }
        }

    monkeypatch.setattr(BibleApiClient, "passage", fake_passage)

    code = main(["live", "John 3:16-17", "--markdown"])

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "# John 3:16-17",
        "",
        "- **John 3:16** For God so loved the world that he gave",
        "- **John 3:17** For God did not send his Son to condemn",
    ]


def test_cli_live_json_outputs_raw_provider_payload_for_data_wrapped_shape(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    provider_payload = {
        "data": {
            "reference": "John 3:16",
            "translation": "WEB",
            "verses": [{"reference": "John 3:16", "content": ["For God", {"text": "loved"}]}],
        }
    }

    def fake_passage(
        self: BibleApiClient, reference: str, translation: str = "web", *, timeout: float = 30, retries: int = 0
    ) -> dict[str, object]:
        return provider_payload

    monkeypatch.setattr(BibleApiClient, "passage", fake_passage)

    code = main(["live", "John 3:16", "--json"])

    assert code == 0
    assert json.loads(capsys.readouterr().out) == provider_payload


def test_render_live_csv_exports_one_row_per_usable_verse() -> None:
    output = _render_live_csv(
        {
            "reference": "John 3:16-17",
            "translation_id": "web",
            "verses": [
                {"book_name": "John", "chapter": 3, "verse": 16, "text": 'For God, "loved".'},
                {"book_name": "John", "chapter": 3, "verse": 17, "text": "For God sent\nhis Son."},
            ],
        },
        "John 3:16-17",
    )

    assert list(csv.reader(io.StringIO(output))) == [
        ["reference", "translation", "verse_reference", "text"],
        ["John 3:16-17", "web", "John 3:16", 'For God, "loved".'],
        ["John 3:16-17", "web", "John 3:17", "For God sent\nhis Son."],
    ]


def test_render_live_csv_exports_top_level_text_when_no_usable_verses() -> None:
    output = _render_live_csv(
        {
            "translation": "web",
            "verses": ["unsupported"],
            "text": "Top-level, fallback text.",
        },
        "John 3:16",
    )

    assert list(csv.reader(io.StringIO(output))) == [
        ["reference", "translation", "verse_reference", "text"],
        ["John 3:16", "web", "John 3:16", "Top-level, fallback text."],
    ]


def test_render_live_csv_renders_data_wrapped_verses_with_alternate_text_keys() -> None:
    output = _render_live_csv(
        {
            "data": {
                "reference": "John 3:16-17",
                "translation": "WEB",
                "verses": [
                    {
                        "book_name": "John",
                        "chapter": 3,
                        "verse": 16,
                        "content": ["For God", {"text": "so loved"}, ["the world"]],
                    },
                    {
                        "book": "John",
                        "chapter": 3,
                        "verse": 17,
                        "verse_text": [{"content": "For God sent"}, ["his Son"]],
                    },
                ],
            }
        },
        "John 3:16-17",
    )

    assert list(csv.reader(io.StringIO(output))) == [
        ["reference", "translation", "verse_reference", "text"],
        ["John 3:16-17", "WEB", "John 3:16", "For God so loved the world"],
        ["John 3:16-17", "WEB", "John 3:17", "For God sent his Son"],
    ]


def test_cli_live_csv_exports_spreadsheet_rows(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_passage(
        self: BibleApiClient, reference: str, translation: str = "web", *, timeout: float = 30, retries: int = 0
    ) -> dict[str, object]:
        assert reference == "John 3:16"
        assert translation == "web"
        return {
            "reference": "John 3:16",
            "translation_id": "web",
            "verses": [
                {"book_name": "John", "chapter": 3, "verse": 16, "text": 'For God, "loved".'},
            ],
        }

    monkeypatch.setattr(BibleApiClient, "passage", fake_passage)

    code = main(["live", "John 3:16", "--translation", "web", "--csv"])

    assert code == 0
    assert list(csv.reader(io.StringIO(capsys.readouterr().out))) == [
        ["reference", "translation", "verse_reference", "text"],
        ["John 3:16", "web", "John 3:16", 'For God, "loved".'],
    ]


def test_cli_live_passes_timeout_and_retries_to_provider(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seen_options: list[tuple[str, str, float, int]] = []

    def fake_passage(
        self: BibleApiClient, reference: str, translation: str = "web", *, timeout: float = 30, retries: int = 0
    ) -> dict[str, object]:
        seen_options.append((reference, translation, timeout, retries))
        return {"reference": "John 3:16", "text": "Example text."}

    monkeypatch.setattr(BibleApiClient, "passage", fake_passage)

    code = main(["live", "John 3:16", "--translation", "web", "--timeout", "2.5", "--retries", "3"])

    assert code == 0
    assert seen_options == [("John 3:16", "web", 2.5, 3)]
    assert capsys.readouterr().out.splitlines() == ["John 3:16", "Example text."]


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("--timeout", "0"),
        ("--timeout", "-1"),
        ("--retries", "-1"),
    ],
)
def test_cli_live_rejects_invalid_timeout_and_retries(flag: str, value: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["live", "John 3:16", flag, value])

    assert exc_info.value.code == 2


def test_cli_live_rejects_json_and_markdown_together() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["live", "John 3:16", "--json", "--markdown"])

    assert exc_info.value.code == 2


@pytest.mark.parametrize("other_flag", ["--json", "--markdown"])
def test_cli_live_rejects_csv_with_other_output_modes(other_flag: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["live", "John 3:16", "--csv", other_flag])

    assert exc_info.value.code == 2
