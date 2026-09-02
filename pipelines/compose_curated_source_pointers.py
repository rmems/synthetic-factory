#!/usr/bin/env python3
"""JSON Pointer traversal and identity-owner resolution inside curated records."""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_source_pointers")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_source_pointers"
    )


def identity_owner(record: dict[str, Any], pointer: Any) -> dict[str, Any] | None:
    """Resolve an identity manifest owner pointer within one curated record."""

    if pointer == "/":
        return record
    tokens = json_pointer_tokens(pointer)
    if tokens is None:
        return None
    return descendant_mapping(record, tokens)


def descendant_mapping(
    record: dict[str, Any], tokens: list[str]
) -> dict[str, Any] | None:
    """Traverse decoded pointer tokens and return only mapping owners."""

    owner: Any = record
    for token in tokens:
        if not isinstance(owner, dict):
            return None
        owner = owner.get(token)
    return owner if isinstance(owner, dict) else None


def is_child_json_pointer(pointer: Any) -> bool:
    """Whether a value identifies a non-root JSON Pointer path."""

    return isinstance(pointer, str) and pointer.startswith("/") and pointer != "/"


def json_pointer_tokens(pointer: Any) -> list[str] | None:
    """Decode a non-root JSON Pointer into unescaped path tokens."""

    if not is_child_json_pointer(pointer):
        return None
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def pop_json_pointer(record: dict[str, Any], pointer: Any) -> None:
    """Drop one JSON-pointer field from a copied record when it exists."""

    tokens = json_pointer_tokens(pointer)
    if tokens is None:
        return
    owner: Any = record
    for token in tokens[:-1]:
        if not isinstance(owner, dict):
            return
        owner = owner.get(token)
    if isinstance(owner, dict) and tokens[-1]:
        owner.pop(tokens[-1], None)


def original_id_paths(originals: Any) -> list[str]:
    """Return every valid path carried by original-id entries."""

    if not isinstance(originals, list):
        return []
    return [
        item["path"]
        for item in originals
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]


def mapped_legacy_id_paths(detail: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Collect all identity-mapped legacy identifier paths."""

    if not isinstance(detail, Mapping):
        return ()
    paths = original_id_paths(detail.get("original_ids"))
    mappings = detail.get("id_mappings")
    if isinstance(mappings, list):
        for mapping in mappings:
            if isinstance(mapping, dict):
                paths.extend(original_id_paths(mapping.get("original_ids")))
    return tuple(dict.fromkeys(paths))


if __package__:
    _expose_package_sibling(__name__)
