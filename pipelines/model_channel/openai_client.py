"""Stdlib OpenAI-compatible chat client for local vLLM and OpenRouter."""
from __future__ import annotations

import http.client
import json
import ssl
from typing import Any, Mapping
from urllib.parse import urlparse

from ._contract import bind_import_twin, load_strict_json

DEFAULT_TIMEOUT_S = 60


class OpenAIClientError(ValueError):
    """The OpenAI-compatible endpoint refused or returned unusable bytes."""


def _split_url(base_url: str) -> tuple[str, str, int, str]:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise OpenAIClientError(f"unsupported OpenAI-compatible URL: {base_url!r}")
    path = parsed.path.rstrip("/") or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.scheme, parsed.hostname, port, path


def _connection(scheme: str, host: str, port: int, timeout: float):
    if scheme == "https":
        context = ssl.create_default_context()
        return http.client.HTTPSConnection(host, port, timeout=timeout, context=context)
    return http.client.HTTPConnection(host, port, timeout=timeout)


def chat_completions(
    base_url: str,
    model: str,
    messages: list[Mapping[str, str]],
    *,
    api_key: str | None = None,
    extra: Mapping[str, Any] | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """POST ``/chat/completions`` and return the decoded JSON object."""
    if not isinstance(model, str) or not model.strip() or model != model.strip():
        raise OpenAIClientError("model must be a non-empty exact tag; no silent rewrite")
    scheme, host, port, prefix = _split_url(base_url)
    payload: dict[str, Any] = {"model": model, "messages": list(messages)}
    if extra:
        payload.update(dict(extra))
    body = json.dumps(payload, allow_nan=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Length": str(len(body)),
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    conn = _connection(scheme, host, port, timeout_s)
    try:
        conn.request("POST", f"{prefix}/chat/completions", body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read()
    finally:
        conn.close()
    if response.status < 200 or response.status >= 300:
        raise OpenAIClientError(
            f"OpenAI-compatible HTTP {response.status}: {raw[:200]!r}"
        )
    try:
        decoded = load_strict_json(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise OpenAIClientError(f"OpenAI-compatible response is not JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise OpenAIClientError("OpenAI-compatible response must be a JSON object")
    return decoded


bind_import_twin(__name__)
