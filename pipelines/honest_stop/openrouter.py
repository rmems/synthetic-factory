"""OpenRouter chat templates for the primary honest-stop writer.

:func:`writer_request` builds a request and reads no credentials.
:func:`perform` reads ``OPENROUTER_API_KEY`` at send time. Dry-run never calls it.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json, load_strict_json
from .splits import load_family

__all__ = [
    "Choice",
    "perform",
    "request_params",
    "require_effort",
    "snapshot_of",
    "transport",
    "writer_request",
]


@dataclass(frozen=True)
class Choice:
    """One planned writer call: exact model id, reasoning effort, and seed."""

    model: str
    effort: str
    seed: int
    secondary: bool = False


def _text(model: object) -> str:
    if isinstance(model, str) and model.strip():
        return model
    raise cv.FamilyError("openrouter.model", "unsupported writer model")


def _suffix(model: str) -> str | None:
    prefix = cv.WRITER_MODEL + "-"
    if model.startswith(prefix):
        return model[len(prefix) :]
    return None


def _dated(suffix: str) -> bool:
    if not suffix.isdigit():
        return False
    return len(suffix) in {4, 8}


def snapshot_of(model: object) -> str | None:
    """Return the dated suffix, or None for the floating default id."""

    text = _text(model)
    if text == cv.WRITER_MODEL:
        return None
    suffix = _suffix(text)
    if suffix is not None and _dated(suffix):
        return suffix
    raise cv.FamilyError("openrouter.model", "unsupported writer model")


def require_effort(effort: object) -> str:
    """Accept an OpenRouter reasoning effort. The family default is high."""

    if isinstance(effort, str) and effort in cv.REASONING_EFFORTS:
        return effort
    raise cv.FamilyError("openrouter.effort", "unsupported reasoning effort")


def _seed(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise cv.FamilyError("seed", "seed must be a non-negative integer")
    if value < 0:
        raise cv.FamilyError("seed", "seed must be a non-negative integer")
    return value


def request_params(choice: Choice) -> dict[str, Any]:
    """Stable body fields recorded on the plan actor. The key is not a field."""

    snapshot_of(choice.model)
    return {
        "model": choice.model,
        "reasoning": {"effort": require_effort(choice.effort)},
        "seed": _seed(choice.seed),
        "stream": False,
    }


def _endpoint() -> str:
    return load_family().writer.openrouter_url


def _body(prompt: str, choice: Choice) -> dict[str, Any]:
    body = dict(request_params(choice))
    body["messages"] = [{"role": "user", "content": prompt}]
    return body


def writer_request(prompt: str, choice: Choice) -> dict[str, Any]:
    """POST body for one chat completion. Headers are added only by :func:`perform`."""

    return {"method": "POST", "url": _endpoint(), "body": _body(prompt, choice)}


def _https(url: str) -> bool:
    if not url.startswith("https://"):
        return False
    if "@" in url:
        return False
    return True


def _url_of(request: Mapping[str, Any]) -> str:
    url = request.get("url")
    if isinstance(url, str) and _https(url):
        return url
    raise cv.FamilyError("openrouter.request", "writer request URL is not https")


def _body_of(request: Mapping[str, Any]) -> dict:
    body = request.get("body")
    if isinstance(body, dict):
        return body
    raise cv.FamilyError("openrouter.request", "writer request body must be an object")


def _require_post(request: Mapping[str, Any]) -> tuple[str, dict]:
    if request.get("method") != "POST":
        raise cv.FamilyError("openrouter.request", "writer request must be POST")
    return _url_of(request), _body_of(request)


def _api_key() -> str:
    provided = os.environ.get(cv.OPENROUTER_API_KEY_ENV)
    if isinstance(provided, str) and provided.strip():
        return provided
    name = cv.OPENROUTER_API_KEY_ENV
    raise cv.FamilyError("openrouter.key", f"{name} is not set")


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": "Bearer " + _api_key(),
        "Content-Type": "application/json",
    }


def _authorized(url: str, body: dict) -> urllib.request.Request:
    payload = dumps_exact_json(body).encode("utf-8")
    headers = _headers()
    unredirected = headers.pop("Authorization")
    http = urllib.request.Request(url, data=payload, method="POST", headers=headers)
    http.add_unredirected_header("Authorization", unredirected)
    return http


def transport():
    """The stdlib opener :func:`perform` calls. Tests replace this lookup."""

    return urllib.request.urlopen


def _consume(http: urllib.request.Request) -> bytes:
    with transport()(http, timeout=cv.OPENROUTER_TIMEOUT_S) as response:
        return response.read()


def _send(http: urllib.request.Request) -> bytes:
    try:
        return _consume(http)
    except urllib.error.HTTPError:
        raise cv.FamilyError("openrouter.http", "OpenRouter rejected the request") from None
    except urllib.error.URLError, OSError:
        raise cv.FamilyError("openrouter.transport", "OpenRouter request failed") from None


def _parsed(payload: bytes) -> object:
    try:
        return load_strict_json(payload.decode("utf-8"))
    except ValueError, RecursionError:
        raise cv.FamilyError("openrouter.response", "OpenRouter response was not JSON") from None


def _decode(payload: bytes) -> dict[str, Any]:
    parsed = _parsed(payload)
    if isinstance(parsed, dict):
        return parsed
    raise cv.FamilyError("openrouter.response", "OpenRouter response was not an object")


def perform(request: Mapping[str, Any]) -> dict[str, Any]:
    """POST one prepared request. The credential is read here and is not returned."""

    if not isinstance(request, Mapping):
        raise cv.FamilyError("openrouter.request", "writer request must be an object")
    url, body = _require_post(request)
    return _decode(_send(_authorized(url, body)))


bind_import_twin(__name__)
