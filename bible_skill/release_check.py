from __future__ import annotations

import re
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Any

README_FILES = ("README.md", "README-zh.md", "README-ja.md")
TOP_LEVEL_FILES = (*README_FILES, "LICENSE")
REGISTRY_CLAIM_PATTERNS = (
    re.compile(r"\bpip\s+install\s+bible-skill\b", re.IGNORECASE),
    re.compile(r"\bpython\s+-m\s+pip\s+install\s+bible-skill\b", re.IGNORECASE),
    re.compile(r"\buvx\s+bible-skill\b", re.IGNORECASE),
)
REGISTRY_DISCLAIMER_PATTERNS = (
    re.compile(r"\bdo not\b", re.IGNORECASE),
    re.compile(r"\bnot published\b", re.IGNORECASE),
    re.compile(r"\bno registry\b", re.IGNORECASE),
    re.compile(r"\bno package-registry\b", re.IGNORECASE),
    re.compile(r"\bsource checkout only\b", re.IGNORECASE),
    re.compile(r"\bnot a package-registry install path\b", re.IGNORECASE),
    re.compile("不要使用"),
    re.compile("没有注册表发布版本"),
    re.compile("使わないでください"),
    re.compile("公開版はまだありません"),
)
MIT_PHRASES = (
    "MIT License",
    "Permission is hereby granted, free of charge",
    'THE SOFTWARE IS PROVIDED "AS IS"',
)


def check_release_readiness(root: str | Path = ".", dist_dir: str | Path | None = None) -> dict[str, Any]:
    root_path = Path(root).resolve()
    checks: list[dict[str, Any]] = []
    project: dict[str, str] = {}

    pyproject = _load_pyproject(root_path, checks)
    project_table = pyproject.get("project") if isinstance(pyproject.get("project"), dict) else {}
    if isinstance(project_table, dict):
        project = {
            "name": str(project_table.get("name", "")),
            "version": str(project_table.get("version", "")),
        }
        _check_value(checks, "pyproject.project.name", project["name"] == "bible-skill", "project.name is bible-skill")
        _check_value(checks, "pyproject.project.version", bool(project["version"]), "project.version is present")
        _check_value(
            checks,
            "pyproject.project.readme",
            project_table.get("readme") == "README.md",
            "project.readme is README.md",
        )
        _check_value(
            checks,
            "pyproject.project.license",
            _project_license(project_table.get("license")) == "MIT",
            "project.license is MIT",
        )

    for filename in TOP_LEVEL_FILES:
        _check_value(checks, f"file.{filename}", (root_path / filename).is_file(), f"{filename} is present")

    _check_mit_license(root_path, checks)
    _check_readme_registry_claims(root_path, checks)
    _check_artifacts(root_path, dist_dir, project, checks)

    issues = [check["message"] for check in checks if not check["ok"]]
    return {
        "ok": not issues,
        "root": str(root_path),
        "project": project,
        "checks": checks,
        "issues": issues,
    }


def render_release_check_text(result: dict[str, Any]) -> str:
    lines = [f"Release readiness for {result['root']}"]
    project = result.get("project") or {}
    if project.get("name") or project.get("version"):
        lines.append(f"Project: {project.get('name', '')} {project.get('version', '')}".strip())
    lines.append(f"Status: {'ok' if result['ok'] else 'failed'}")
    for check in result["checks"]:
        status = "ok" if check["ok"] else "fail"
        lines.append(f"{status}\t{check['id']}\t{check['message']}")
    return "\n".join(lines)


def _load_pyproject(root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.is_file():
        _add_check(checks, "pyproject", False, "pyproject.toml is missing")
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        _add_check(checks, "pyproject", False, f"pyproject.toml is invalid TOML: {exc.msg}")
        return {}
    _add_check(checks, "pyproject", True, "pyproject.toml is readable")
    if not isinstance(data.get("project"), dict):
        _add_check(checks, "pyproject.project", False, "pyproject.toml [project] table is missing")
    return data


def _project_license(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = value.get("text")
        return text if isinstance(text, str) else ""
    return ""


def _check_mit_license(root: Path, checks: list[dict[str, Any]]) -> None:
    path = root / "LICENSE"
    if not path.is_file():
        _add_check(checks, "license.mit-text", False, "LICENSE is missing")
        return
    text = path.read_text(encoding="utf-8")
    missing = [phrase for phrase in MIT_PHRASES if phrase not in text]
    if missing:
        _add_check(checks, "license.mit-text", False, "LICENSE does not contain standard MIT license text")
    else:
        _add_check(checks, "license.mit-text", True, "LICENSE contains standard MIT license text")


def _check_readme_registry_claims(root: Path, checks: list[dict[str, Any]]) -> None:
    issues: list[str] = []
    for filename in README_FILES:
        path = root / filename
        if not path.is_file():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _contains_registry_install_claim(line):
                issues.append(f"{filename} contains unverified registry install claim on line {line_number}")
    if issues:
        for issue in issues:
            _add_check(checks, "readme.registry-claims", False, issue)
    else:
        _add_check(checks, "readme.registry-claims", True, "README variants do not make registry install claims")


def _contains_registry_install_claim(line: str) -> bool:
    if not any(pattern.search(line) for pattern in REGISTRY_CLAIM_PATTERNS):
        return False
    return not any(pattern.search(line) for pattern in REGISTRY_DISCLAIMER_PATTERNS)


def _check_artifacts(
    root: Path, dist_dir: str | Path | None, project: dict[str, str], checks: list[dict[str, Any]]
) -> None:
    explicit = dist_dir is not None
    dist_path = Path(dist_dir).resolve() if dist_dir is not None else root / "dist"
    if not dist_path.exists():
        if explicit:
            _add_check(checks, "artifact.metadata", False, f"dist directory is missing: {dist_path}")
        return
    artifacts = sorted([*dist_path.glob("*.whl"), *dist_path.glob("*.tar.gz")])
    if not artifacts:
        _add_check(
            checks,
            "artifact.metadata",
            False,
            f"dist directory contains no wheel or sdist artifacts: {dist_path}",
        )
        return
    for artifact in artifacts:
        metadata = _artifact_metadata(artifact)
        if not metadata:
            _add_check(checks, "artifact.metadata", False, f"{artifact.name} has no readable package metadata")
            continue
        _check_artifact_field(checks, artifact, "name", metadata.get("Name", ""), project.get("name", ""))
        _check_artifact_field(checks, artifact, "version", metadata.get("Version", ""), project.get("version", ""))


def _artifact_metadata(path: Path) -> dict[str, str]:
    try:
        if path.suffix == ".whl":
            return _wheel_metadata(path)
        if path.name.endswith(".tar.gz"):
            return _sdist_metadata(path)
    except (OSError, KeyError, tarfile.TarError, zipfile.BadZipFile, UnicodeDecodeError):
        return {}
    return {}


def _wheel_metadata(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        return dict(Parser().parsestr(archive.read(metadata_name).decode("utf-8")).items())


def _sdist_metadata(path: Path) -> dict[str, str]:
    with tarfile.open(path, "r:gz") as archive:
        member = next(member for member in archive.getmembers() if member.name.endswith("/PKG-INFO"))
        extracted = archive.extractfile(member)
        if extracted is None:
            return {}
        return dict(Parser().parsestr(extracted.read().decode("utf-8")).items())


def _check_artifact_field(checks: list[dict[str, Any]], artifact: Path, field: str, actual: str, expected: str) -> None:
    if not expected:
        _add_check(
            checks,
            "artifact.metadata",
            False,
            f"cannot compare {artifact.name} metadata without pyproject {field}",
        )
    elif actual != expected:
        _add_check(
            checks,
            "artifact.metadata",
            False,
            f"{artifact.name} artifact {field} {actual} does not match pyproject {field} {expected}",
        )
    else:
        _add_check(checks, "artifact.metadata", True, f"{artifact.name} artifact {field} matches pyproject")


def _check_value(checks: list[dict[str, Any]], check_id: str, ok: bool, ok_message: str) -> None:
    message = ok_message if ok else _failure_message(check_id)
    _add_check(checks, check_id, ok, message)


def _failure_message(check_id: str) -> str:
    messages = {
        "pyproject.project.name": "pyproject project.name must be bible-skill",
        "pyproject.project.version": "pyproject project.version is missing",
        "pyproject.project.readme": "pyproject project.readme must be README.md",
        "pyproject.project.license": "pyproject project.license must be MIT",
    }
    if check_id in messages:
        return messages[check_id]
    if check_id.startswith("file."):
        return f"{check_id.removeprefix('file.')} is missing"
    return f"{check_id} failed"


def _add_check(checks: list[dict[str, Any]], check_id: str, ok: bool, message: str) -> None:
    checks.append({"id": check_id, "ok": ok, "message": message})
