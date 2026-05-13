from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


_HTTP_ERROR_DETAIL_LIMIT = 240
_HTTP_ERROR_MESSAGE_FIELDS = ("error", "message", "detail", "reason")


class FreeUseBibleApiClient:
    def __init__(self, base_url: str = "https://bible.helloao.org/api") -> None:
        self.base_url = base_url.rstrip("/")
        self.last_source_url = ""

    def translations(self) -> list[dict[str, Any]]:
        payload = _get_json(f"{self.base_url}/available_translations.json")
        if isinstance(payload, list):
            return payload
        for key in ("translations", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
        raise ProviderError("Translation list response has an unsupported shape.")

    def download_translation(self, translation_id: str) -> dict[str, Any]:
        self.last_source_url = f"{self.base_url}/{quote(translation_id)}/complete.json"
        payload = _get_json(self.last_source_url)
        if not isinstance(payload, dict):
            raise ProviderError("Downloaded translation response has an unsupported shape.")
        metadata = dict(payload.get("metadata") or payload.get("translation") or {})
        metadata.setdefault("id", translation_id)
        metadata.setdefault("source_url", self.last_source_url)
        if "license_url" not in metadata:
            metadata["license_url"] = metadata.get("licenseUrl", "")
        payload = dict(payload)
        payload["metadata"] = metadata
        payload["source_url"] = self.last_source_url
        return payload


class BibleApiClient:
    def __init__(self, base_url: str = "https://bible-api.com") -> None:
        self.base_url = base_url.rstrip("/")

    def passage(self, reference: str, translation: str = "web") -> dict[str, Any]:
        query = urlencode({"translation": translation})
        url = f"{self.base_url}/{quote(reference)}?{query}"
        payload = _get_json(url)
        if not isinstance(payload, dict):
            raise ProviderError("Live passage response has an unsupported shape.")
        if payload.get("error"):
            raise ProviderError(str(payload["error"]))
        return payload


def _get_json(url: str) -> Any:
    if urlparse(url).scheme not in {"https", "http"}:
        raise ProviderError(f"Unsupported URL scheme for {url}")
    request = Request(url, headers={"User-Agent": "bible-skill/0.1"})  # noqa: S310
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except HTTPError as exc:
        raise ProviderError(_format_http_error(exc, url)) from exc
    except URLError as exc:
        raise ProviderError(f"Network error while fetching {url}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Invalid JSON from {url}") from exc


def _format_http_error(exc: HTTPError, url: str) -> str:
    message = f"HTTP {exc.code} while fetching {url}"
    detail = _http_error_detail(exc)
    if detail:
        message = f"{message}: {detail}"
    retry_after = _normalized_text(exc.headers.get("Retry-After", ""))
    if retry_after:
        message = f"{message}. Retry after {retry_after}"
    return message


def _http_error_detail(exc: HTTPError) -> str:
    body = exc.read()
    if not body:
        return ""
    charset = exc.headers.get_content_charset() or "utf-8"
    text = body.decode(charset, errors="replace")
    json_detail = _json_error_detail(text)
    if json_detail:
        return json_detail
    return _truncate_error_detail(_normalized_text(text))


def _json_error_detail(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    for field in _HTTP_ERROR_MESSAGE_FIELDS:
        detail = _readable_json_error_value(payload.get(field))
        if detail:
            return detail
    return ""


def _readable_json_error_value(value: Any) -> str:
    if isinstance(value, str):
        return _truncate_error_detail(_normalized_text(value))
    if isinstance(value, dict):
        for field in _HTTP_ERROR_MESSAGE_FIELDS:
            detail = _readable_json_error_value(value.get(field))
            if detail:
                return detail
    return ""


def _normalized_text(text: str) -> str:
    return " ".join(text.split())


def _truncate_error_detail(text: str) -> str:
    if len(text) <= _HTTP_ERROR_DETAIL_LIMIT:
        return text
    return f"{text[: _HTTP_ERROR_DETAIL_LIMIT - 3].rstrip()}..."
