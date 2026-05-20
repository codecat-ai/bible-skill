from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from bible_skill.cli import main


def write_ready_checkout(path: Path) -> None:
    (path / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "bible-skill"',
                'version = "0.1.0"',
                'readme = "README.md"',
                'license = "MIT"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    for readme in ("README.md", "README-zh.md", "README-ja.md"):
        (path / readme).write_text(
            "Bible Skill\n\n"
            "This package is not published to a package registry yet. "
            "Use it from a source checkout only.\n\n"
            "Do not use `pip install bible-skill`, `uvx bible-skill`, or similar registry commands.\n",
            encoding="utf-8",
        )
    (path / "LICENSE").write_text(
        "MIT License\n\n"
        "Copyright (c) 2026 Bible Skill contributors\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        'of this software and associated documentation files (the "Software"), to deal\n'
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n'
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n",
        encoding="utf-8",
    )


def write_wheel(path: Path, *, name: str = "bible-skill", version: str = "0.1.0") -> Path:
    dist = path / "dist"
    dist.mkdir()
    wheel = dist / f"{name.replace('-', '_')}-{version}-py3-none-any.whl"
    dist_info = f"{name.replace('-', '_')}-{version}.dist-info"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(f"{dist_info}/METADATA", f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n")
        archive.writestr(f"{dist_info}/WHEEL", "Wheel-Version: 1.0\n")
    return wheel


def test_release_check_json_passes_for_source_checkout_fixture(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_ready_checkout(tmp_path)

    code = main(["release", "check", "--root", str(tmp_path), "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert code == 0
    assert payload["ok"] is True
    assert payload["project"] == {"name": "bible-skill", "version": "0.1.0"}
    assert payload["issues"] == []
    assert {check["id"] for check in payload["checks"]} >= {
        "pyproject.project.name",
        "pyproject.project.version",
        "pyproject.project.readme",
        "pyproject.project.license",
        "readme.registry-claims",
        "license.mit-text",
    }


def test_release_check_reports_missing_top_level_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_ready_checkout(tmp_path)
    (tmp_path / "README-ja.md").unlink()
    (tmp_path / "LICENSE").unlink()

    code = main(["release", "check", "--root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
    assert "README-ja.md is missing" in payload["issues"]
    assert "LICENSE is missing" in payload["issues"]


@pytest.mark.parametrize(
    "claim",
    [
        "Install with `pip install bible-skill`.",
        "Run `uvx bible-skill --help` from any directory.",
        "Use `python -m pip install bible-skill` for the released package.",
    ],
)
def test_release_check_rejects_misleading_registry_install_claims(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], claim: str
) -> None:
    write_ready_checkout(tmp_path)
    (tmp_path / "README.md").write_text(f"Bible Skill\n\n{claim}\n", encoding="utf-8")

    code = main(["release", "check", "--root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
    assert any("README.md contains unverified registry install claim" in issue for issue in payload["issues"])


@pytest.mark.parametrize(
    "warning",
    [
        "不要使用 `pip install bible-skill`、`uvx bible-skill` 或类似注册表安装命令；目前还没有注册表发布版本。",
        (
            "`pip install bible-skill`、`uvx bible-skill`、または同様のレジストリ用コマンドは"
            "使わないでください。レジストリ公開版はまだありません。"
        ),
    ],
)
def test_release_check_allows_translated_registry_install_warnings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], warning: str
) -> None:
    write_ready_checkout(tmp_path)
    (tmp_path / "README.md").write_text(f"Bible Skill\n\n{warning}\n", encoding="utf-8")

    code = main(["release", "check", "--root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True


def test_release_check_detects_detected_wheel_metadata_version_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_ready_checkout(tmp_path)
    write_wheel(tmp_path, version="9.9.9")

    code = main(["release", "check", "--root", str(tmp_path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
    assert any("artifact version 9.9.9 does not match pyproject version 0.1.0" in issue for issue in payload["issues"])


def test_release_check_text_output_is_human_readable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_ready_checkout(tmp_path)
    write_wheel(tmp_path)

    code = main(["release", "check", "--root", str(tmp_path)])

    output = capsys.readouterr().out.splitlines()
    assert code == 0
    assert output[0] == f"Release readiness for {tmp_path}"
    assert "Project: bible-skill 0.1.0" in output
    assert any(line.startswith("ok\tpyproject.project.name") for line in output)
    assert any(line.startswith("ok\tartifact.metadata") for line in output)


def test_release_check_help_is_wired(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["release", "check", "--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "Check source checkout release readiness without publishing." in output
    assert "--dist-dir" in output
