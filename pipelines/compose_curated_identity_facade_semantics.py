#!/usr/bin/env python3
"""Live compatibility adapters for semantic identity and curated deduplication."""

from __future__ import annotations

import copy
import sys
from typing import Any, Mapping, MutableMapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity_facade_semantics")
    from . import compose_contract as _contract
    from . import compose_curated_source as _source_impl
    from .compose_curated_context import StageDefinition
    from .compose_curated_identity_facade_binding import _facade
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity_facade_semantics"
    )
    import compose_contract as _contract
    import compose_curated_source as _source_impl
    from compose_curated_context import StageDefinition
    from compose_curated_identity_facade_binding import _facade

ACTION_EXCLUDED = _contract.ACTION_EXCLUDED
ACTION_RETAINED = _contract.ACTION_RETAINED
COMPOSE_NAME = _contract.COMPOSE_NAME
COMPOSE_VERSION = _contract.COMPOSE_VERSION
ComposeDecision = _contract.ComposeDecision
ComposeError = _contract.ComposeError
REASON_DUPLICATE_CURATED_RECORD = _contract.REASON_DUPLICATE_CURATED_RECORD


def _identity_owner(record: dict[str, Any], pointer: Any) -> dict[str, Any] | None:
    if pointer == "/":
        return record
    tokens = _facade()._json_pointer_tokens(pointer)
    return _source_impl._descendant_mapping(record, tokens) if tokens is not None else None


def _json_pointer_tokens(pointer: Any) -> list[str] | None:
    return _source_impl._json_pointer_tokens(pointer)


def _pop_json_pointer(record: dict[str, Any], pointer: Any) -> None:
    tokens = _facade()._json_pointer_tokens(pointer)
    if tokens is None:
        return
    owner: Any = record
    for token in tokens[:-1]:
        if not isinstance(owner, dict):
            return
        owner = owner.get(token)
    if isinstance(owner, dict) and tokens[-1]:
        owner.pop(tokens[-1], None)


def _original_id_paths(originals: Any) -> list[str]:
    return _source_impl._original_id_paths(originals)


def _mapped_legacy_id_paths(detail: Mapping[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(detail, Mapping):
        return ()
    facade = _facade()
    paths = facade._original_id_paths(detail.get("original_ids"))
    mappings = detail.get("id_mappings")
    for mapping in mappings if isinstance(mappings, list) else ():
        if isinstance(mapping, dict):
            paths.extend(facade._original_id_paths(mapping.get("original_ids")))
    return tuple(dict.fromkeys(paths))


def _semantic_identity_owners(record: dict[str, Any]) -> list[dict[str, Any]]:
    return _source_impl._semantic_identity_owners(record)


def _identity_stage_detail_of(decision: ComposeDecision) -> dict[str, Any] | None:
    return _source_impl._identity_stage_detail_of(decision)


def _strip_assigned_ids(semantic: dict[str, Any], detail: dict[str, Any] | None) -> None:
    facade = _facade()
    mappings = detail.get("id_mappings") if isinstance(detail, dict) else None
    for mapping in mappings if isinstance(mappings, list) else ():
        if not isinstance(mapping, dict):
            continue
        owner = facade._identity_owner(semantic, mapping.get("owner_path"))
        if owner is not None and owner.get("id") == mapping.get("output_id"):
            owner.pop("id", None)
    for path in facade._mapped_legacy_id_paths(detail):
        facade._pop_json_pointer(semantic, path)


def _strip_provenance_labels(semantic: dict[str, Any]) -> None:
    for owner in _facade()._semantic_identity_owners(semantic):
        meta = owner.get("meta")
        if not isinstance(meta, dict):
            continue
        for label in ("factory", "generator", "generator_version", "run", "round"):
            meta.pop(label, None)


def _strip_sidecar_binding(semantic: dict[str, Any]) -> None:
    return _source_impl._strip_sidecar_binding(semantic)


def _post_transform_semantic_sha256(decision: ComposeDecision) -> str:
    facade = _facade()
    if decision.record is None:
        raise ComposeError("cannot hash a missing curated record")
    semantic = copy.deepcopy(decision.record)
    facade._strip_assigned_ids(semantic, facade._identity_stage_detail_of(decision))
    facade._strip_provenance_labels(semantic)
    facade._strip_sidecar_binding(semantic)
    return facade._canonical_sha256(semantic)


def _deduplicate_curated_record(
    decision: ComposeDecision,
    *,
    source_path: str,
    source_line: int,
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None,
) -> ComposeDecision:
    facade = _facade()
    retained = decision.action == ACTION_RETAINED and decision.record is not None
    if seen_curated_semantics is None or not retained:
        return decision
    digest = facade._post_transform_semantic_sha256(decision)
    first = seen_curated_semantics.get(digest)
    if first is None:
        seen_curated_semantics[digest] = (source_path, source_line)
        return decision
    duplicate = facade._stage(
        StageDefinition("post_transform_dedup", COMPOSE_NAME, COMPOSE_VERSION),
        ACTION_EXCLUDED,
        reason_codes=[REASON_DUPLICATE_CURATED_RECORD],
        semantic_sha256=digest,
        first_source_path=first[0],
        first_source_line=first[1],
    )
    return ComposeDecision(
        ACTION_EXCLUDED,
        None,
        (REASON_DUPLICATE_CURATED_RECORD,),
        (*decision.stages, duplicate),
        None,
        None,
    )


def _excluded_source_line(reason: str, detail: dict[str, Any]) -> ComposeDecision:
    evidence = _facade()._stage(
        StageDefinition("source", COMPOSE_NAME, COMPOSE_VERSION),
        ACTION_EXCLUDED,
        reason_codes=[reason],
        detail=detail,
    )
    return ComposeDecision(ACTION_EXCLUDED, None, (reason,), (evidence,), None, None)


if __package__:
    _expose_package_sibling(__name__)
