from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

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

    def load_translation(self, translation_id: str) -> dict[str, Any]:
        path = self._translation_dir(translation_id) / "translation.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing local translation: {translation_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def has_translation(self, translation_id: str) -> bool:
        return (self._translation_dir(translation_id) / "translation.json").exists()

    def _translation_dir(self, translation_id: str) -> Path:
        return self.translations_dir / translation_id.lower()

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


def default_data_dir() -> Path:
    root = os.environ.get("BIBLE_SKILL_DATA_DIR")
    if root:
        return Path(root)
    return Path.home() / ".local" / "share" / "bible-skill"
