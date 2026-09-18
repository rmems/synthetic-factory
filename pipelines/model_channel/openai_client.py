"""Stdlib OpenAI-compatible chat client for local vLLM and OpenRouter."""
from __future__ import annotations

import http.client
import json
import ssl
from dataclasses import dataclass
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


@dataclass(frozen=True, kw_only=True)
class ClientOptions:
    api_key: str | None = None
    extra: Mapping[str, Any] | None = None
    timeout_s: float = DEFAULT_TIMEOUT_S


def _request_body(model: str, messages: list[Mapping[str, str]], extra: Mapping | None) -> bytes:
    payload = {"model": model, "messages": list(messages)}
    if extra:
        payload.update(extra)
    return json.dumps(payload, allow_nan=False).encode("utf-8")


def _request_headers(body: bytes, api_key: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Length": str(len(body)),
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _read_response(conn, path: str, body: bytes, headers: dict) -> bytes:
    try:
        conn.request("POST", path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        if not 200 <= response.status < 300:
            raise OpenAIClientError(f"OpenAI-compatible HTTP {response.status}: {raw[:200]!r}")
        return raw
    finally:
        conn.close()


def _decode_response(raw: bytes) -> dict[str, Any]:
    try:
        decoded = load_strict_json(raw.decode("utf-8"))
    except ValueError as exc:
        raise OpenAIClientError(f"OpenAI-compatible response is not JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise OpenAIClientError("OpenAI-compatible response must be a JSON object")
    return decoded


def _require_model(model: str) -> None:
    if not isinstance(model, str) or not model.strip():
        raise OpenAIClientError("model must be a non-empty exact tag; no silent rewrite")
    if model != model.strip():
        raise OpenAIClientError("model must be a non-empty exact tag; no silent rewrite")


def chat_completions(base_url: str, model: str, messages: list[Mapping[str, str]], **kwargs) -> dict[str, Any]:
    """POST chat completions with keyword options described by ClientOptions."""
    options = ClientOptions(**kwargs)
    _require_model(model)
    scheme, host, port, prefix = _split_url(base_url)
    body = _request_body(model, messages, options.extra)
    headers = _request_headers(body, options.api_key)
    conn = _connection(scheme, host, port, options.timeout_s)
    return _decode_response(_read_response(conn, f"{prefix}/chat/completions", body, headers))


bind_import_twin(__name__)
