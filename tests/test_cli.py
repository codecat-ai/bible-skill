from __future__ import annotations

import json
from pathlib import Path

import pytest

from bible_skill.cli import main
from bible_skill.store import Store
from tests.fixtures import tiny_translation


def seed_translation(path: Path) -> None:
    Store(path).save_translation("toy", tiny_translation())


def test_cli_query_json_outputs_machine_readable_passage(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seed_translation(tmp_path)

    code = main(["--data-dir", str(tmp_path), "query", "toy", "John 3:16", "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["translation_id"] == "toy"
    assert payload["reference"] == "John 3:16"
    assert payload["verses"] == [{"reference": "John 3:16", "text": "Fixture loved line."}]


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
