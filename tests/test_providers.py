from __future__ import annotations

import pytest

from bible_skill import providers
from bible_skill.providers import FreeUseBibleApiClient


def test_free_use_download_uses_documented_complete_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_urls: list[str] = []

    def fake_get_json(url: str) -> dict:
        seen_urls.append(url)
        return {"translation": {"id": "BSB", "name": "Berean Standard Bible"}, "books": []}

    monkeypatch.setattr(providers, "_get_json", fake_get_json)
    client = FreeUseBibleApiClient("https://bible.helloao.org/api")

    payload = client.download_translation("BSB")

    assert seen_urls == ["https://bible.helloao.org/api/BSB/complete.json"]
    assert payload["metadata"]["id"] == "BSB"
    assert payload["metadata"]["source_url"] == seen_urls[0]
