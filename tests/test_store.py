from __future__ import annotations

import json
from pathlib import Path

from bible_skill.store import Store
from tests.fixtures import tiny_translation


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def download_translation(self, translation_id: str) -> dict:
        self.calls.append(translation_id)
        data = tiny_translation()
        data["metadata"]["id"] = translation_id
        return data


def test_store_saves_and_lists_installed_translation(tmp_path: Path) -> None:
    store = Store(tmp_path)
    provider = FakeProvider()

    record = store.download("toy", provider)

    assert record.translation_id == "toy"
    assert provider.calls == ["toy"]
    installed = store.installed()
    assert len(installed) == 1
    assert installed[0].book_count == 3
    assert installed[0].chapter_count == 4
    assert installed[0].verse_count == 8
    assert store.load_translation("toy")["metadata"]["id"] == "toy"


def test_download_skips_existing_unless_forced(tmp_path: Path) -> None:
    store = Store(tmp_path)
    provider = FakeProvider()

    store.download("toy", provider)
    store.download("toy", provider)
    store.download("toy", provider, force=True)

    assert provider.calls == ["toy", "toy"]


def test_store_saves_translation_with_stable_checksum(tmp_path: Path) -> None:
    store = Store(tmp_path)

    store.save_translation("toy", tiny_translation())
    first = store.load_translation("toy")
    first_checksum = first["metadata"]["checksum"]
    first["metadata"]["fetched_at"] = "2099-01-01T00:00:00+00:00"
    second_checksum = store.translation_checksum(first)

    assert first_checksum.startswith("sha256:")
    assert len(first_checksum) == 71
    assert second_checksum == first_checksum


def test_store_validates_installed_translation_cache(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())

    result = store.validate_translation("toy")

    assert result.translation_id == "toy"
    assert result.ok is True
    assert result.checksum == store.load_translation("toy")["metadata"]["checksum"]
    assert result.issues == []


def test_store_validation_reports_missing_required_metadata(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    path = tmp_path / "translations" / "toy" / "translation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["metadata"]["name"]
    data["metadata"]["checksum"] = store.translation_checksum(data)
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.validate_translation("toy")

    assert result.ok is False
    assert "metadata.name is required" in result.issues


def test_store_validation_reports_invalid_verse_structure(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    path = tmp_path / "translations" / "toy" / "translation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["books"][0]["chapters"][0]["verses"][0]["text"] = "   "
    data["metadata"]["checksum"] = store.translation_checksum(data)
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.validate_translation("toy")

    assert result.ok is False
    assert "books[0].chapters[0].verses[0].text must be non-empty" in result.issues


def test_store_validation_reports_checksum_mismatch(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    path = tmp_path / "translations" / "toy" / "translation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["books"][1]["chapters"][0]["verses"][0]["text"] = "Corrupted line."
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.validate_translation("toy")

    assert result.ok is False
    assert result.checksum == store.translation_checksum(data)
    assert "metadata.checksum does not match translation content" in result.issues


def test_store_validation_reports_missing_sidecar_metadata(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    (tmp_path / "translations" / "toy" / "metadata.json").unlink()

    result = store.validate_translation("toy")

    assert result.ok is False
    assert "metadata.json is missing" in result.issues


def test_store_validation_reports_invalid_sidecar_metadata_json(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    (tmp_path / "translations" / "toy" / "metadata.json").write_text("{", encoding="utf-8")

    result = store.validate_translation("toy")

    assert result.ok is False
    assert "metadata.json is invalid JSON: Expecting property name enclosed in double quotes" in result.issues


def test_store_validation_reports_sidecar_metadata_root_type(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    (tmp_path / "translations" / "toy" / "metadata.json").write_text("[]", encoding="utf-8")

    result = store.validate_translation("toy")

    assert result.ok is False
    assert "metadata.json root must be an object" in result.issues


def test_store_validation_reports_sidecar_metadata_checksum_drift(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    path = tmp_path / "translations" / "toy" / "translation.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["books"][1]["chapters"][0]["verses"][0]["text"] = "Corrupted line."
    data["metadata"]["checksum"] = store.translation_checksum(data)
    path.write_text(json.dumps(data), encoding="utf-8")

    result = store.validate_translation("toy")

    assert result.ok is False
    assert "metadata.json.checksum does not match translation content" in result.issues
    assert "metadata.json.checksum does not match translation.json metadata" in result.issues


def test_store_validation_reports_sidecar_metadata_field_mismatches(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    path = tmp_path / "translations" / "toy" / "metadata.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    for field in ("id", "name", "language", "license_url", "fetched_at", "source_url", "checksum"):
        metadata[field] = f"wrong-{field}"
    path.write_text(json.dumps(metadata), encoding="utf-8")

    result = store.validate_translation("toy")

    assert result.ok is False
    for field in ("id", "name", "language", "license_url", "fetched_at", "source_url", "checksum"):
        assert f"metadata.json.{field} does not match translation.json metadata" in result.issues


def test_store_validation_reports_missing_requested_translation(tmp_path: Path) -> None:
    result = Store(tmp_path).validate_translation("missing")

    assert result.translation_id == "missing"
    assert result.ok is False
    assert result.checksum == ""
    assert result.issues == ["translation cache is missing"]


def test_store_cache_manifest_reports_portable_translation_entries(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())

    manifest = store.cache_manifest(generated_at="2026-05-20T00:00:00+00:00")

    assert manifest == {
        "schema_version": 1,
        "generated_at": "2026-05-20T00:00:00+00:00",
        "data_dir": str(tmp_path),
        "translations": [
            {
                "id": "toy",
                "name": "Toy Test Translation",
                "language": "en",
                "license_url": "https://example.invalid/license",
                "source_url": "",
                "book_count": 3,
                "chapter_count": 4,
                "verse_count": 8,
                "checksum": store.load_translation("toy")["metadata"]["checksum"],
                "relative_path": "translations/toy/translation.json",
                "validation_ok": True,
                "issues": [],
            }
        ],
    }


def test_store_cache_manifest_reports_corrupt_entries_without_crashing(tmp_path: Path) -> None:
    broken = tmp_path / "translations" / "broken"
    missing = tmp_path / "translations" / "missing"
    broken.mkdir(parents=True)
    missing.mkdir(parents=True)
    (broken / "translation.json").write_text("{", encoding="utf-8")

    manifest = Store(tmp_path).cache_manifest(generated_at="2026-05-20T00:00:00+00:00")

    assert manifest["translations"] == [
        {
            "id": "broken",
            "name": "",
            "language": "",
            "license_url": "",
            "source_url": "",
            "book_count": 0,
            "chapter_count": 0,
            "verse_count": 0,
            "checksum": "",
            "relative_path": "translations/broken/translation.json",
            "validation_ok": False,
            "issues": ["translation.json is invalid JSON: Expecting property name enclosed in double quotes"],
        },
        {
            "id": "missing",
            "name": "",
            "language": "",
            "license_url": "",
            "source_url": "",
            "book_count": 0,
            "chapter_count": 0,
            "verse_count": 0,
            "checksum": "",
            "relative_path": "translations/missing/translation.json",
            "validation_ok": False,
            "issues": ["translation cache is missing"],
        },
    ]


def test_store_cache_manifest_reports_malformed_sidecar_metadata_without_crashing(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    (tmp_path / "translations" / "toy" / "metadata.json").write_text("{", encoding="utf-8")

    manifest = store.cache_manifest(generated_at="2026-05-20T00:00:00+00:00")

    assert manifest["translations"][0]["id"] == "toy"
    assert manifest["translations"][0]["validation_ok"] is False
    assert manifest["translations"][0]["issues"] == [
        "metadata.json is invalid JSON: Expecting property name enclosed in double quotes"
    ]


def test_store_prunes_only_invalid_cache_directories_when_confirmed(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.save_translation("toy", tiny_translation())
    broken = tmp_path / "translations" / "broken"
    broken.mkdir(parents=True)
    (broken / "translation.json").write_text("{", encoding="utf-8")

    result = store.prune_invalid_cache_entries(translation_ids=[], dry_run=False)

    assert result["removed"] == ["broken"]
    assert result["kept"] == ["toy"]
    assert result["issues"] == [
        {
            "translation_id": "broken",
            "issues": ["translation.json is invalid JSON: Expecting property name enclosed in double quotes"],
        }
    ]
    assert not broken.exists()
    assert (tmp_path / "translations" / "toy").exists()
