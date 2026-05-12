from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


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
        raise ProviderError(f"HTTP {exc.code} while fetching {url}") from exc
    except URLError as exc:
        raise ProviderError(f"Network error while fetching {url}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Invalid JSON from {url}") from exc
