#!/usr/bin/env python3
"""Content identity and self-declared labels for the training audit.

The duplicate key and the label check live here so the record module's
whole-file complexity stays the measurement surface it already was.
"""

from __future__ import annotations

import sys
import unicodedata
from typing import Any

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("training_audit_content")
    from .exact_json import dumps_exact_json
    from .record_kind import SUPPORTED_RECORD_KINDS, classify_kind
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "training_audit_content"
    )
    from exact_json import dumps_exact_json
    from record_kind import SUPPORTED_RECORD_KINDS, classify_kind


# Identity stamps and the reward sidecar id are bookkeeping. A nested ``id``
# that is not one of these paths is content and stays in the hash.
_STAMPED_ID_PATHS = frozenset({
    ("id",),
    ("chosen", "id"),
    ("rejected", "id"),
    ("language_view", "trajectory", "id"),
})
_HUMAN_VERIFIED_SOURCE = "human_verified"
_MISSING = object()
_NON_STRING_CLAIM = "non-string"

# Kind labels. Preference-arm ``chosen`` / ``rejected`` sides are out of scope.
_KIND_CLAIM_PATHS = (
    ("record_kind",),
    ("meta", "kind"),
    ("meta", "record_kind"),
)
# Source-kind labels, including ``meta.provenance``. Preference-arm sides are
# out of scope.
_SOURCE_KIND_CLAIM_PATHS = (
    ("source_kind",),
    ("meta", "source_kind"),
    ("provenance", "source_kind"),
    ("meta", "provenance", "source_kind"),
)


def _content_without_identity(value, path=()):
    """Drop identity stamps from ``value``; content whitespace is kept."""
    if isinstance(value, dict):
        return _mapping_without_identity(value, path)
    if isinstance(value, list):
        return _list_without_identity(value, path)
    return value


def _mapping_without_identity(value, path):
    cleaned = {}
    for key, child in value.items():
        child_path = path + (key,)
        if key == "source_sidecar_id" or child_path in _STAMPED_ID_PATHS:
            continue
        cleaned[key] = _content_without_identity(child, child_path)
    return cleaned


def _list_without_identity(value, path):
    """An index keeps a list element's ``id`` off the stamped owner paths."""
    return [
        _content_without_identity(child, path + (str(index),))
        for index, child in enumerate(value)
    ]


def content_identity_blob(value):
    """Canonical JSON of training content, without identity stamps.

    Surrounding whitespace in content strings is kept, so an indented patch
    line is not the same record as the flush version. That revises #535.
    """
    return dumps_exact_json(
        _content_without_identity(value), sort_keys=True, ensure_ascii=False
    )


def _lookup(record: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = record
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return _MISSING
        current = current[key]
    return current


def _mapped_claim_char(char: str) -> str:
    if unicodedata.category(char) == "Cf":
        return ""
    if char == "-" or char.isspace():
        return "_"
    return char


def _normalize_claim(text: str) -> str:
    """NFKC, casefold, drop format chars, and read ``-`` / spaces as ``_``."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return "".join(_mapped_claim_char(char) for char in folded).strip("_")


def _claim_at(record: dict[str, Any], path: tuple[str, ...]) -> str | None:
    value = _lookup(record, path)
    if value is _MISSING:
        return None
    if not isinstance(value, str):
        return _NON_STRING_CLAIM
    return _normalize_claim(value)


def _kind_claims(record: dict[str, Any]) -> list[str]:
    return [
        claim
        for claim in (_claim_at(record, path) for path in _KIND_CLAIM_PATHS)
        if claim
    ]


def _source_kind_claims(record: dict[str, Any]) -> list[str]:
    return [
        claim
        for claim in (_claim_at(record, path) for path in _SOURCE_KIND_CLAIM_PATHS)
        if claim
    ]


def _kind_disagrees(claim: str, kind: str) -> bool:
    return claim in SUPPORTED_RECORD_KINDS and claim != kind


def _label_errors(obj: dict[str, Any]) -> list[str]:
    kind = classify_kind(obj)
    errors = [
        f"DECLARED_KIND_MISMATCH:{claim}!={kind}"
        for claim in _kind_claims(obj)
        if claim == _NON_STRING_CLAIM or _kind_disagrees(claim, kind)
    ]
    errors.extend(
        f"DECLARED_SOURCE_KIND:{claim}"
        for claim in _source_kind_claims(obj)
        if (
            claim in {_HUMAN_VERIFIED_SOURCE, _NON_STRING_CLAIM}
            or _kind_disagrees(claim, kind)
        )
    )
    return errors


def declared_label_errors(obj: Any) -> list[str]:
    """Refuse a self-declared kind or a human-verified source claim.

    Payload classification stays the authority. Claims are compared after
    NFKC, casefold, dropping format characters, and reading ``-`` and spaces
    as ``_``. A non-string value at a claim path is refused.

    Kind paths: ``record_kind``, ``meta.kind``, ``meta.record_kind``.
    Source-kind paths: ``source_kind``, ``meta.source_kind``,
    ``provenance.source_kind``, ``meta.provenance.source_kind``.
    Preference-arm ``chosen`` / ``rejected`` labels are out of scope.
    """
    if not isinstance(obj, dict):
        return []
    return _label_errors(obj)


if __package__:
    _expose_package_sibling(__name__)
