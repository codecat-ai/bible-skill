from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


_HTTP_ERROR_DETAIL_LIMIT = 240
_HTTP_ERROR_MESSAGE_FIELDS = ("error", "message", "detail", "reason")
_DEFAULT_HTTP_TIMEOUT = 30.0
_RETRYABLE_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_LIVE_TEXT_FIELDS = ("text", "content", "verse_text")
_LIVE_VERSE_LIST_FIELDS = ("verses", "passages")


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

    def passage(
        self, reference: str, translation: str = "web", *, timeout: float = _DEFAULT_HTTP_TIMEOUT, retries: int = 0
    ) -> dict[str, Any]:
        query = urlencode({"translation": translation})
        url = f"{self.base_url}/{quote(reference)}?{query}"
        payload = _get_json(url, timeout=timeout, retries=retries)
        if not isinstance(payload, dict):
            _raise_live_schema_error(["malformed payload: expected object"])
        if payload.get("error"):
            raise ProviderError(str(payload["error"]))
        _validate_live_passage_schema(payload)
        return payload


def _get_json(url: str, *, timeout: float = _DEFAULT_HTTP_TIMEOUT, retries: int = 0) -> Any:
    if urlparse(url).scheme not in {"https", "http"}:
        raise ProviderError(f"Unsupported URL scheme for {url}")
    request = Request(url, headers={"User-Agent": "bible-skill/0.1"})  # noqa: S310
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset))
        except HTTPError as exc:
            retryable = _is_retryable_http_error(exc)
            if attempt < retries and retryable:
                continue
            raise ProviderError(_format_http_error(exc, url), retryable=retryable) from exc
        except URLError as exc:
            if attempt < retries:
                continue
            raise ProviderError(f"Network error while fetching {url}: {exc.reason}", retryable=True) from exc
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Invalid JSON from {url}") from exc

    raise ProviderError(f"Network error while fetching {url}: retry attempts exhausted", retryable=True)


def _validate_live_passage_schema(payload: dict[str, Any]) -> None:
    issues: list[str] = []
    body = payload
    if "data" in payload:
        data = payload["data"]
        if not isinstance(data, dict):
            issues.append("malformed `data`: expected object")
            _raise_live_schema_error(issues)
        body = data

    if not _has_non_empty_value(body.get("reference")):
        issues.append("missing `reference`: expected `reference` field")

    verse_list_field = _live_verse_list_field(body)
    if verse_list_field:
        _validate_live_verse_list(body[verse_list_field], verse_list_field, issues)
    elif not _has_text_value(body):
        issues.append("missing text-bearing field: expected `text`, `content`, or `verse_text`")

    if issues:
        _raise_live_schema_error(issues)


def _live_verse_list_field(body: dict[str, Any]) -> str:
    for field in _LIVE_VERSE_LIST_FIELDS:
        if field in body:
            return field
    return ""


def _validate_live_verse_list(value: Any, field: str, issues: list[str]) -> None:
    if not isinstance(value, list):
        issues.append(f"malformed `{field}`: expected list")
        return
    if not value:
        issues.append(f"malformed `{field}`: expected non-empty list")
        return
    for index, verse in enumerate(value):
        path = f"`{field}[{index}]`"
        if not isinstance(verse, dict):
            issues.append(f"malformed verse entry at {path}: expected object")
        elif not _has_text_value(verse):
            issues.append(f"missing verse text at {path}: expected `text`, `content`, or `verse_text`")


def _has_text_value(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return any(field in value and _text_fragment_has_text(value[field]) for field in _LIVE_TEXT_FIELDS)


def _text_fragment_has_text(value: Any) -> bool:
    if isinstance(value, dict):
        return _has_text_value(value)
    if isinstance(value, list):
        return any(_text_fragment_has_text(item) for item in value)
    return _has_non_empty_value(value)


def _has_non_empty_value(value: Any) -> bool:
    return value is not None and bool(str(value).strip())


def _raise_live_schema_error(issues: list[str]) -> None:
    expected = (
        "expected live passage fields: `reference`; either top-level `text`, `content`, or `verse_text`, "
        "or a `verses`/`passages` list whose entries contain `text`, `content`, or `verse_text`"
    )
    raise ProviderError(f"unsupported live passage schema: {'; '.join(issues)}. {expected}")


def _is_retryable_http_error(exc: HTTPError) -> bool:
    return exc.code in _RETRYABLE_HTTP_STATUS_CODES


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
