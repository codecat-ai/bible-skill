from __future__ import annotations

from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

import pytest

from bible_skill import providers
from bible_skill.providers import FreeUseBibleApiClient, ProviderError


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


def raise_http_error(
    monkeypatch: pytest.MonkeyPatch, *, code: int, body: str, headers: dict[str, str] | None = None
) -> None:
    response_headers = Message()
    for key, value in (headers or {}).items():
        response_headers[key] = value

    def fake_urlopen(*args: object, **kwargs: object) -> object:
        raise HTTPError(
            "https://provider.example.invalid/passage",
            code,
            "provider error",
            response_headers,
            BytesIO(body.encode("utf-8")),
        )

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)


def test_http_error_uses_json_error_message_and_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    raise_http_error(
        monkeypatch,
        code=429,
        body='{"error": "Too many requests for this translation."}',
        headers={"Content-Type": "application/json", "Retry-After": "60"},
    )

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage")

    message = str(exc_info.value)
    assert "HTTP 429 while fetching https://provider.example.invalid/passage" in message
    assert "Too many requests for this translation." in message
    assert "Retry after 60" in message


def test_http_error_uses_other_json_message_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    raise_http_error(
        monkeypatch,
        code=503,
        body='{"detail": "Provider maintenance window is active."}',
    )

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage")

    assert str(exc_info.value) == (
        "HTTP 503 while fetching https://provider.example.invalid/passage: Provider maintenance window is active."
    )


def test_http_error_includes_normalized_plain_text_body(monkeypatch: pytest.MonkeyPatch) -> None:
    raise_http_error(
        monkeypatch,
        code=502,
        body="  temporary\n\n upstream\t failure  ",
        headers={"Content-Type": "text/plain"},
    )

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage")

    assert str(exc_info.value) == (
        "HTTP 502 while fetching https://provider.example.invalid/passage: temporary upstream failure"
    )


def test_http_error_truncates_long_provider_body(monkeypatch: pytest.MonkeyPatch) -> None:
    raise_http_error(monkeypatch, code=500, body=f"Failure details {'word ' * 120}")

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage")

    message = str(exc_info.value)
    assert message.startswith("HTTP 500 while fetching https://provider.example.invalid/passage: Failure details")
    assert len(message) < 340
    assert message.endswith("...")
