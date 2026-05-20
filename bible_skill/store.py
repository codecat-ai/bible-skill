from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from bible_skill.books import BY_ID
from bible_skill.query import normalize_translation


class DownloadProvider(Protocol):
    def download_translation(self, translation_id: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class InstalledTranslation:
    translation_id: str
    name: str
    language: str
    license_url: str
    fetched_at: str
    source_url: str
    book_count: int
    chapter_count: int
    verse_count: int

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class ValidationResult:
    translation_id: str
    ok: bool
    checksum: str
    issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class Store:
    def __init__(self, data_dir: Path | str | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self.translations_dir = self.data_dir / "translations"

    def save_translation(self, translation_id: str, data: dict[str, Any], source_url: str = "") -> InstalledTranslation:
        target = self._translation_dir(translation_id)
        target.mkdir(parents=True, exist_ok=True)
        metadata = dict(data.get("metadata") or {})
        metadata.setdefault("id", translation_id)
        metadata.setdefault("fetched_at", datetime.now(UTC).replace(microsecond=0).isoformat())
        metadata.setdefault("source_url", source_url)
        data = dict(data)
        data["metadata"] = metadata
        metadata["checksum"] = self.translation_checksum(data)
        translation_json = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False) + "\n"
        (target / "translation.json").write_text(translation_json, encoding="utf-8")
        (target / "metadata.json").write_text(metadata_json, encoding="utf-8")
        return self._record_for(translation_id)

    def download(self, translation_id: str, provider: DownloadProvider, force: bool = False) -> InstalledTranslation:
        if self.has_translation(translation_id) and not force:
            return self._record_for(translation_id)
        data = provider.download_translation(translation_id)
        source_url = str(data.get("source_url") or getattr(provider, "last_source_url", ""))
        return self.save_translation(translation_id, data, source_url=source_url)

    def installed(self) -> list[InstalledTranslation]:
        if not self.translations_dir.exists():
            return []
        records = []
        for path in sorted(self.translations_dir.iterdir()):
            if path.is_dir() and (path / "translation.json").exists():
                records.append(self._record_for(path.name))
        return records

    def cached_translation_ids(self) -> list[str]:
        if not self.translations_dir.exists():
            return []
        return [
            path.name
            for path in sorted(self.translations_dir.iterdir())
            if path.is_dir() and (path / "translation.json").exists()
        ]

    def load_translation(self, translation_id: str) -> dict[str, Any]:
        path = self._translation_dir(translation_id) / "translation.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing local translation: {translation_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def has_translation(self, translation_id: str) -> bool:
        return (self._translation_dir(translation_id) / "translation.json").exists()

    def translation_checksum(self, translation: dict[str, Any]) -> str:
        normalized = normalize_translation(translation)
        metadata = normalized["metadata"]
        payload = {
            "metadata": {
                key: metadata.get(key, "")
                for key in ("id", "name", "language", "license", "license_url")
                if key in metadata
            },
            "books": {
                book_id: {
                    str(chapter): {str(verse): text for verse, text in sorted(verses.items())}
                    for chapter, verses in sorted(chapters.items())
                }
                for book_id, chapters in sorted(normalized["books"].items())
            },
        }
        digest_input = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"sha256:{hashlib.sha256(digest_input.encode('utf-8')).hexdigest()}"

    def validate_translation(self, translation_id: str) -> ValidationResult:
        path = self._translation_dir(translation_id) / "translation.json"
        if not path.exists():
            return ValidationResult(
                translation_id=translation_id,
                ok=False,
                checksum="",
                issues=["translation cache is missing"],
            )

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return ValidationResult(
                translation_id=translation_id,
                ok=False,
                checksum="",
                issues=[f"translation.json is invalid JSON: {exc.msg}"],
            )
        if not isinstance(data, dict):
            return ValidationResult(
                translation_id=translation_id,
                ok=False,
                checksum="",
                issues=["translation.json root must be an object"],
            )

        issues = _schema_issues(data)
        checksum = self.translation_checksum(data)
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        stored_checksum = metadata.get("checksum") if isinstance(metadata, dict) else None
        if not stored_checksum:
            issues.append("metadata.checksum is required")
        elif stored_checksum != checksum:
            issues.append("metadata.checksum does not match translation content")
        issues.extend(_sidecar_metadata_issues(path.with_name("metadata.json"), metadata, checksum))

        normalized = normalize_translation(data)
        result_id = str(normalized["metadata"].get("id") or translation_id)
        return ValidationResult(translation_id=result_id, ok=not issues, checksum=checksum, issues=issues)

    def cache_manifest(self, generated_at: str | datetime | None = None) -> dict[str, Any]:
        timestamp = generated_at or datetime.now(UTC).replace(microsecond=0)
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        return {
            "schema_version": 1,
            "generated_at": timestamp,
            "data_dir": str(self.data_dir),
            "translations": [self._manifest_entry_for(path.name) for path in self._translation_dirs()],
        }

    def _translation_dir(self, translation_id: str) -> Path:
        return self.translations_dir / translation_id.lower()

    def _translation_dirs(self) -> list[Path]:
        if not self.translations_dir.exists():
            return []
        return [path for path in sorted(self.translations_dir.iterdir()) if path.is_dir()]

    def _record_for(self, translation_id: str) -> InstalledTranslation:
        data = self.load_translation(translation_id)
        normalized = normalize_translation(data)
        metadata = normalized["metadata"]
        chapter_count = sum(len(chapters) for chapters in normalized["books"].values())
        verse_count = sum(len(verses) for chapters in normalized["books"].values() for verses in chapters.values())
        return InstalledTranslation(
            translation_id=metadata.get("id", translation_id),
            name=metadata.get("name", metadata.get("id", translation_id)),
            language=metadata.get("language", ""),
            license_url=metadata.get("license_url", metadata.get("licenseUrl", "")),
            fetched_at=metadata.get("fetched_at", ""),
            source_url=metadata.get("source_url", ""),
            book_count=len(normalized["books"]),
            chapter_count=chapter_count,
            verse_count=verse_count,
        )

    def _manifest_entry_for(self, translation_id: str) -> dict[str, Any]:
        path = self._translation_dir(translation_id) / "translation.json"
        data: dict[str, Any] = {}
        issues: list[str] = []
        try:
            validation = self.validate_translation(translation_id)
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            validation = ValidationResult(
                translation_id=translation_id,
                ok=False,
                checksum="",
                issues=[f"translation cache validation failed: {exc}"],
            )
        try:
            if path.exists():
                parsed = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    data = parsed
        except json.JSONDecodeError:
            pass
        except OSError as exc:
            issues.append(f"translation.json could not be read: {exc}")

        if issues:
            validation = ValidationResult(
                translation_id=validation.translation_id,
                ok=False,
                checksum=validation.checksum,
                issues=[*validation.issues, *issues],
            )

        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        counts = _translation_counts(data)
        return {
            "id": str(metadata.get("id") or validation.translation_id or translation_id),
            "name": str(metadata.get("name") or ""),
            "language": str(metadata.get("language") or ""),
            "license_url": str(metadata.get("license_url") or metadata.get("licenseUrl") or ""),
            "source_url": str(metadata.get("source_url") or ""),
            "book_count": counts["book_count"],
            "chapter_count": counts["chapter_count"],
            "verse_count": counts["verse_count"],
            "checksum": validation.checksum,
            "relative_path": (Path("translations") / translation_id / "translation.json").as_posix(),
            "validation_ok": validation.ok,
            "issues": validation.issues,
        }


def default_data_dir() -> Path:
    root = os.environ.get("BIBLE_SKILL_DATA_DIR")
    if root:
        return Path(root)
    return Path.home() / ".local" / "share" / "bible-skill"


def _schema_issues(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return ["metadata must be an object"]

    for field in ("id", "name", "language", "license_url", "fetched_at", "source_url"):
        if field not in metadata:
            issues.append(f"metadata.{field} is required")
        elif not isinstance(metadata[field], str):
            issues.append(f"metadata.{field} must be a string")
        elif field != "source_url" and not metadata[field].strip():
            issues.append(f"metadata.{field} must be non-empty")

    books = data.get("books")
    if not isinstance(books, list) or not books:
        issues.append("books must be a non-empty list")
        return issues

    for book_index, book in enumerate(books):
        book_path = f"books[{book_index}]"
        if not isinstance(book, dict):
            issues.append(f"{book_path} must be an object")
            continue
        _require_non_empty_string(book, "id", f"{book_path}.id", issues)
        _require_non_empty_string(book, "name", f"{book_path}.name", issues)
        if isinstance(book.get("id"), str) and book["id"].upper() not in BY_ID:
            issues.append(f"{book_path}.id must be a known USFM book id")
        chapters = book.get("chapters")
        if not isinstance(chapters, list) or not chapters:
            issues.append(f"{book_path}.chapters must be a non-empty list")
            continue
        for chapter_index, chapter in enumerate(chapters):
            chapter_path = f"{book_path}.chapters[{chapter_index}]"
            if not isinstance(chapter, dict):
                issues.append(f"{chapter_path} must be an object")
                continue
            _require_positive_int(chapter, "number", f"{chapter_path}.number", issues)
            verses = chapter.get("verses")
            if not isinstance(verses, list) or not verses:
                issues.append(f"{chapter_path}.verses must be a non-empty list")
                continue
            for verse_index, verse in enumerate(verses):
                verse_path = f"{chapter_path}.verses[{verse_index}]"
                if not isinstance(verse, dict):
                    issues.append(f"{verse_path} must be an object")
                    continue
                _require_positive_int(verse, "number", f"{verse_path}.number", issues)
                _require_non_empty_string(verse, "text", f"{verse_path}.text", issues)
    return issues


def _sidecar_metadata_issues(path: Path, translation_metadata: dict[str, Any], checksum: str) -> list[str]:
    if not path.exists():
        return ["metadata.json is missing"]

    try:
        sidecar = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"metadata.json is invalid JSON: {exc.msg}"]
    except OSError as exc:
        return [f"metadata.json could not be read: {exc}"]
    if not isinstance(sidecar, dict):
        return ["metadata.json root must be an object"]

    issues: list[str] = []
    expected = {
        field: translation_metadata.get(field)
        for field in ("id", "name", "language", "license_url", "fetched_at", "source_url", "checksum")
    }
    for field, expected_value in expected.items():
        if field not in sidecar:
            issues.append(f"metadata.json.{field} is required")
        elif sidecar[field] != expected_value:
            issues.append(f"metadata.json.{field} does not match translation.json metadata")

    if "checksum" in sidecar and sidecar.get("checksum") != checksum:
        issues.append("metadata.json.checksum does not match translation content")
    return issues


def _translation_counts(data: dict[str, Any]) -> dict[str, int]:
    try:
        normalized = normalize_translation(data)
    except (TypeError, ValueError, KeyError, AttributeError):
        return {"book_count": 0, "chapter_count": 0, "verse_count": 0}
    return {
        "book_count": len(normalized["books"]),
        "chapter_count": sum(len(chapters) for chapters in normalized["books"].values()),
        "verse_count": sum(len(verses) for chapters in normalized["books"].values() for verses in chapters.values()),
    }


def _require_non_empty_string(data: dict[str, Any], key: str, path: str, issues: list[str]) -> None:
    value = data.get(key)
    if key not in data:
        issues.append(f"{path} is required")
    elif not isinstance(value, str):
        issues.append(f"{path} must be a string")
    elif not value.strip():
        issues.append(f"{path} must be non-empty")


def _require_positive_int(data: dict[str, Any], key: str, path: str, issues: list[str]) -> None:
    value = data.get(key)
    if key not in data:
        issues.append(f"{path} is required")
    elif not isinstance(value, int) or value < 1:
        issues.append(f"{path} must be a positive integer")
