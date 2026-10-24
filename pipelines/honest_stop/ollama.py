"""Local Ollama request templates. This slice refuses to send them."""

from __future__ import annotations

import urllib.request
from collections.abc import Mapping
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin
from .splits import load_family

__all__ = [
    "LiveCallDisabled",
    "digest_from_show",
    "embedding_request",
    "perform",
    "writer_request",
]


class LiveCallDisabled(cv.FamilyError):
    """Raised instead of opening a socket to Ollama."""

    def __init__(self, detail: str) -> None:
        super().__init__("ollama.disabled", detail)


def _url(path: str) -> str:
    return load_family().ollama_url.rstrip("/") + path


def writer_request(prompt: str) -> dict[str, Any]:
    """Optional secondary writer call. The OpenRouter plan is the primary writer."""

    return {
        "method": "POST",
        "url": _url("/api/generate"),
        "body": {"model": cv.SECONDARY_WRITER_MODEL, "prompt": prompt, "stream": False},
    }


def embedding_request(text: str) -> dict[str, Any]:
    """The embedding call used for dedup. Nothing sends it here."""

    return {
        "method": "POST",
        "url": _url("/api/embed"),
        "body": {"model": cv.DEDUP_MODEL, "input": text},
    }


def digest_from_show(document: Mapping[str, Any]) -> str:
    """Read a sha256 digest from an Ollama show document supplied by the caller."""

    digest = document.get("digest") if isinstance(document, Mapping) else None
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise cv.FamilyError("model.digest", "Ollama show document has no sha256 digest")
    body = digest[len("sha256:") :]
    if len(body) != 64 or any(character not in "0123456789abcdef" for character in body):
        raise cv.FamilyError("model.digest", "Ollama show document has no sha256 digest")
    return digest


def transport():
    """The stdlib client a later slice would call. :func:`perform` does not call it."""

    return urllib.request.urlopen


def perform(request: Mapping[str, Any]) -> None:
    """Bind the transport, then refuse. No socket is opened."""

    _ = transport()
    method = request.get("method", "")
    url = request.get("url", "")
    raise LiveCallDisabled(f"refusing {method} {url}")


bind_import_twin(__name__)
