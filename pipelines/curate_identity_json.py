#!/usr/bin/env python3
"""Canonical-JSON, strict decoding, and exact-bytes primitives for identity curation.

Split out of ``curate_identity.py`` (CodeScene: Lines of Code in a Single File)
by responsibility; every name is re-exported from ``curate_identity`` so
existing ``curate_identity.X`` call sites and test seams resolve unchanged.

The error vocabulary lives here because the serializer raises it: a value
that is not canonical JSON data is an ``IdentityCurationError`` and a replay
mismatch is an ``IdentityTreeError``.  Procedural (code-repair) payloads keep
their exact source decimal tokens through ``exact_json``; every other record
is serialized byte-stably by the standard encoder.  Nothing here re-serializes
an exact payload through ``json.dumps``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_json")
    from .exact_json import ExactJSONFloat, dumps_exact_json
    from .record_kind import classify_kind
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_json"
    )
    from exact_json import ExactJSONFloat, dumps_exact_json
    from record_kind import classify_kind


class IdentityCurationError(ValueError):
    """Base class for caller-contract and batch-integrity failures."""


class CanonicalIdCollision(IdentityCurationError):
    """Raised when two retained source records resolve to one canonical ID."""


class IdentityTreeError(IdentityCurationError):
    """Raised when a cleaned tree is missing or mismatched identity sidecars."""


def _reject_unpaired_surrogates(value: Any, path: str = "$") -> None:
    """Reject strings that cannot be represented as Unicode scalar-value text."""

    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ValueError(f"unpaired UTF-16 surrogate in JSON string at {path}")
        return
    if isinstance(value, Mapping):
        for index, (key, item) in enumerate(value.items()):
            if isinstance(key, str):
                _reject_unpaired_surrogates(key, f"{path}.<member-name:{index}>")
            _reject_unpaired_surrogates(item, f"{path}[{index}]")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unpaired_surrogates(item, f"{path}[{index}]")


def canonical_json(value: Any) -> str:
    """Serialize JSON data byte-stably for hashes, tests, and output sidecars."""

    try:
        _reject_unpaired_surrogates(value)
        payload = dumps_exact_json(value) if classify_kind(value) == "code_repair" else json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        # Keep the public serializer's promise byte-stable: callers must never
        # receive text that fails only when a downstream hash or writer encodes it.
        payload.encode("utf-8")
        return payload
    except (TypeError, ValueError) as exc:
        raise IdentityCurationError(f"record is not canonical JSON data: {exc}") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int/float equivalence."""

    return canonical_json(left) == canonical_json(right)


def _require_canonical_json_equal(actual: Any, expected: Any, where: str) -> None:
    try:
        equal = _canonical_json_equal(actual, expected)
    except IdentityCurationError as exc:
        raise IdentityTreeError(f"{where} is not canonical JSON data: {exc}") from exc
    if not equal:
        raise IdentityTreeError(f"{where} does not match the hash-verified source replay")


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant {value}")


def parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {value}")
    return parsed


def reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _strict_json_loads(payload: str, *, exact: bool = False) -> Any:
    """Decode strict JSON; procedural records retain exact source decimal tokens."""

    value = json.loads(
        payload,
        object_pairs_hook=reject_duplicate_object_keys,
        parse_constant=_reject_json_constant,
        parse_float=ExactJSONFloat if exact else parse_finite_json_float,
    )
    if not exact and classify_kind(value) == "code_repair":
        return _strict_json_loads(payload, exact=True)
    _reject_unpaired_surrogates(value)
    return value


def _is_json_whitespace(value: str) -> bool:
    """Return whether non-empty text contains only RFC 8259 JSON whitespace."""

    return bool(value) and all(character in " \t\r\n" for character in value)


def _reject_training_ready_true(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        if value.get("training_ready"):
            raise IdentityCurationError(f"{path} must not contain training_ready: true")
        for key, item in value.items():
            _reject_training_ready_true(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_training_ready_true(item, f"{path}[{index}]")


if __package__:
    _expose_package_sibling(__name__)
