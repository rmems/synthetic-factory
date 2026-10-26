#!/usr/bin/env python3
"""Content identity and self-declared labels for the training audit.

The duplicate key and the label check live here so the record module's
whole-file complexity stays the measurement surface it already was.
"""

from __future__ import annotations

import sys
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


def _content_without_identity(value, path=()):
    """Drop identity stamps and surrounding whitespace from ``value``."""
    if isinstance(value, dict):
        return _mapping_without_identity(value, path)
    if isinstance(value, list):
        return _list_without_identity(value, path)
    if isinstance(value, str):
        return value.strip()
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
    """Canonical JSON of training content, without ids or edge whitespace."""
    return dumps_exact_json(
        _content_without_identity(value), sort_keys=True, ensure_ascii=False
    )


def _text_claim(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _claim_texts(values: tuple[Any, ...]) -> list[str]:
    texts: list[str] = []
    for value in values:
        text = _text_claim(value)
        if text is not None:
            texts.append(text)
    return texts


def _nested_mapping(record: dict[str, Any], key: str) -> dict[str, Any]:
    value = record.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _kind_claims(record: dict[str, Any]) -> list[str]:
    meta = _nested_mapping(record, "meta")
    return _claim_texts((
        record.get("record_kind"), meta.get("kind"), meta.get("record_kind"),
    ))


def _source_kind_claims(record: dict[str, Any]) -> list[str]:
    meta = _nested_mapping(record, "meta")
    provenance = _nested_mapping(record, "provenance")
    return _claim_texts((
        record.get("source_kind"), meta.get("source_kind"), provenance.get("source_kind"),
    ))


def _kind_disagrees(claim: str, kind: str) -> bool:
    return claim in SUPPORTED_RECORD_KINDS and claim != kind


def _label_errors(obj: dict[str, Any]) -> list[str]:
    kind = classify_kind(obj)
    errors = [
        f"DECLARED_KIND_MISMATCH:{claim}!={kind}"
        for claim in _kind_claims(obj)
        if _kind_disagrees(claim, kind)
    ]
    errors.extend(
        f"DECLARED_SOURCE_KIND:{claim}"
        for claim in _source_kind_claims(obj)
        if claim == _HUMAN_VERIFIED_SOURCE or _kind_disagrees(claim, kind)
    )
    return errors


def declared_label_errors(obj: Any) -> list[str]:
    """Refuse a self-declared kind or a human-verified source claim.

    Payload classification stays the authority. A ``meta.kind`` or
    ``record_kind`` that names a different supported kind is a label, not
    evidence, and ``source_kind`` ``human_verified`` is not a factory product.
    """
    if not isinstance(obj, dict):
        return []
    return _label_errors(obj)


if __package__:
    _expose_package_sibling(__name__)
