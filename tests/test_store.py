from __future__ import annotations

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
