from __future__ import annotations

import json
from pathlib import Path

import pytest

from bible_skill.cli import main
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


def test_cli_query_rejects_json_and_usfm_together(tmp_path: Path) -> None:
    seed_translation(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--json", "--usfm"])

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


def test_cli_compare_rejects_json_and_markdown_together(tmp_path: Path) -> None:
    seed_translation(tmp_path)
    seed_second_translation(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--data-dir", str(tmp_path), "compare", "John 3:16", "toy", "alt", "--json", "--markdown"])

    assert exc_info.value.code == 2
