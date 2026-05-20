from __future__ import annotations

from email.message import Message
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from bible_skill import providers
from bible_skill.providers import BibleApiClient, FreeUseBibleApiClient, ProviderError


class JsonResponse:
    def __init__(self, body: str = '{"ok": true}') -> None:
        self.headers = Message()
        self.headers["Content-Type"] = "application/json; charset=utf-8"
        self._body = body.encode("utf-8")

    def __enter__(self) -> JsonResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


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


def test_get_json_passes_configured_timeout_to_request(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_timeouts: list[float] = []

    def fake_urlopen(*args: object, **kwargs: object) -> JsonResponse:
        seen_timeouts.append(kwargs["timeout"])
        return JsonResponse()

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    providers._get_json("https://provider.example.invalid/passage", timeout=7.5)

    assert seen_timeouts == [7.5]


def test_bible_api_passage_passes_timeout_and_retries_to_request(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_options: list[tuple[float, int]] = []

    def fake_get_json(url: str, *, timeout: float = 30, retries: int = 0) -> dict[str, object]:
        seen_options.append((timeout, retries))
        return {"reference": "John 3:16", "text": "Example text."}

    monkeypatch.setattr(providers, "_get_json", fake_get_json)

    BibleApiClient("https://bible-api.example.invalid").passage("John 3:16", timeout=4, retries=2)

    assert seen_options == [(4, 2)]


def test_get_json_retries_transient_network_failure_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def fake_urlopen(*args: object, **kwargs: object) -> JsonResponse:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise URLError("temporary DNS failure")
        return JsonResponse('{"reference": "John 3:16"}')

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    payload = providers._get_json("https://provider.example.invalid/passage", retries=1)

    assert attempts == 2
    assert payload == {"reference": "John 3:16"}


def test_get_json_retry_exhaustion_preserves_provider_error_details(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def fake_urlopen(*args: object, **kwargs: object) -> object:
        nonlocal attempts
        attempts += 1
        response_headers = Message()
        response_headers["Content-Type"] = "application/json"
        response_headers["Retry-After"] = "90"
        raise HTTPError(
            "https://provider.example.invalid/passage",
            503,
            "provider error",
            response_headers,
            BytesIO(b'{"detail": "Provider maintenance window is active."}'),
        )

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage", retries=1)

    message = str(exc_info.value)
    assert attempts == 2
    assert "HTTP 503 while fetching https://provider.example.invalid/passage" in message
    assert "Provider maintenance window is active." in message
    assert "Retry after 90" in message
    assert exc_info.value.retryable is True


def test_get_json_network_failure_marks_error_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> object:
        raise URLError("temporary DNS failure")

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage")

    assert "Network error while fetching https://provider.example.invalid/passage" in str(exc_info.value)
    assert exc_info.value.retryable is True


def test_get_json_invalid_json_error_is_not_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> JsonResponse:
        return JsonResponse("{")

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage")

    assert str(exc_info.value) == "Invalid JSON from https://provider.example.invalid/passage"
    assert exc_info.value.retryable is False


def test_get_json_does_not_retry_non_retryable_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = 0

    def fake_urlopen(*args: object, **kwargs: object) -> object:
        nonlocal attempts
        attempts += 1
        raise HTTPError(
            "https://provider.example.invalid/passage",
            404,
            "not found",
            Message(),
            BytesIO(b'{"error": "No passage found."}'),
        )

    monkeypatch.setattr(providers, "urlopen", fake_urlopen)

    with pytest.raises(ProviderError) as exc_info:
        providers._get_json("https://provider.example.invalid/passage", retries=3)

    assert attempts == 1
    assert "No passage found." in str(exc_info.value)
    assert exc_info.value.retryable is False


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
