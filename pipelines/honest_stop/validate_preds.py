"""Small predicates shared by the honest-stop record checks."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ._contract import bind_import_twin

__all__ = ["digest_ok", "exact_keys", "nonneg_int", "text_ok", "timestamp_ok"]

_DIGEST_PREFIX = "sha256:"
_DIGEST_WIDTH = 64
_HEX = "0123456789abcdef"
_UTC_SUFFIX = "+00:00"


def text_ok(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonneg_int(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, int):
        return False
    return value >= 0


def exact_keys(value: Any, keys: tuple[str, ...]) -> bool:
    return isinstance(value, dict) and set(value) == set(keys)


def _hex_body(body: str) -> bool:
    if len(body) != _DIGEST_WIDTH:
        return False
    if body != body.lower():
        return False
    return all(character in _HEX for character in body)


def digest_ok(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if not value.startswith(_DIGEST_PREFIX):
        return False
    return _hex_body(value[len(_DIGEST_PREFIX) :])


def _parsed_clock(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def _zulu(parsed: datetime) -> str:
    rendered = parsed.isoformat()
    if rendered.endswith(_UTC_SUFFIX):
        return rendered[: -len(_UTC_SUFFIX)] + "Z"
    return rendered


def timestamp_ok(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = _parsed_clock(value)
    if parsed is None:
        return False
    return _zulu(parsed) == value


bind_import_twin(__name__)
