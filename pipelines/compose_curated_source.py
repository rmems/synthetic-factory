#!/usr/bin/env python3
"""Source-line decoding, semantic deduplication, and transform declaration."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping

if __package__:
    from . import _expose_package_sibling, _local_sibling_module, _require_local_sibling

    if _local_sibling_module("compose_curated_source", allow_initializing=True):
        import compose_curated_source as _direct_compose_curated_source

        _require_local_sibling(_direct_compose_curated_source, "compose_curated_source")
        del _direct_compose_curated_source
    from . import (
        curate_agentic,
        curate_bridge,
        curate_coding,
        curate_identity,
        curate_preferences,
        curate_rewards,
    )
    from .check_records import reject_json_constant
    from .compose_contract import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ComposeDecision,
        ComposeError,
        REASON_DUPLICATE_CURATED_RECORD,
        REASON_DUPLICATE_SOURCE_RECORD,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
        _canonical_sha256,
        sha256_hex,
    )
    from .compose_curated_context import (
        RecordContext,
        SourceCoordinates,
        StageDefinition,
        stage,
    )
    from .compose_curated_identity import calibration_for
    from .compose_curated_record import compose_record
    from .curate_identity import _reject_duplicate_object_keys
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_source"
    )
    import curate_agentic
    import curate_bridge
    import curate_coding
    import curate_identity
    import curate_preferences
    import curate_rewards
    from check_records import reject_json_constant
    from compose_contract import (
        ACTION_EXCLUDED,
        ACTION_RETAINED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ComposeDecision,
        ComposeError,
        REASON_DUPLICATE_CURATED_RECORD,
        REASON_DUPLICATE_SOURCE_RECORD,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
        _canonical_sha256,
        sha256_hex,
    )
    from compose_curated_context import (
        RecordContext,
        SourceCoordinates,
        StageDefinition,
        stage,
    )
    from compose_curated_identity import calibration_for
    from compose_curated_record import compose_record
    from curate_identity import _reject_duplicate_object_keys


SOURCE_STAGE = StageDefinition("source", COMPOSE_NAME, COMPOSE_VERSION)
DEDUP_STAGE = StageDefinition("post_transform_dedup", COMPOSE_NAME, COMPOSE_VERSION)


@dataclass(frozen=True)
class SourceLineContext:
    """Stable run inputs and shared semantic indexes for one physical line."""

    source_path: str
    source_line: int
    source_file_sha256: str
    calibration_catalog: Mapping[str, Any] | None = None
    seen_source_semantics: MutableMapping[str, tuple[str, int]] | None = None
    seen_curated_semantics: MutableMapping[str, tuple[str, int]] | None = None
    trajectory_preferences: Any = None
    canonical_sha256: Any = _canonical_sha256
    record_composer: Callable[[Any, RecordContext], ComposeDecision] = compose_record
    calibration_lookup: Callable[[Mapping[str, Any], Mapping[str, Any] | None], Any] = (
        calibration_for
    )
    duplicate_key_rejector: Callable[[list[tuple[str, Any]]], dict[str, Any]] = (
        _reject_duplicate_object_keys
    )
    constant_rejector: Callable[[str], Any] = reject_json_constant
    excluded_source_line: Callable[[str, dict[str, Any]], ComposeDecision] | None = None
    deduplicate_curated_record: Callable[..., ComposeDecision] | None = None


def _identity_owner(record: dict[str, Any], pointer: Any) -> dict[str, Any] | None:
    """Resolve an identity manifest owner pointer within one curated record."""

    if pointer == "/":
        return record
    tokens = _json_pointer_tokens(pointer)
    if tokens is None:
        return None
    return _descendant_mapping(record, tokens)


def _descendant_mapping(
    record: dict[str, Any], tokens: list[str]
) -> dict[str, Any] | None:
    """Traverse decoded pointer tokens and return only mapping owners."""

    owner: Any = record
    for token in tokens:
        if not isinstance(owner, dict):
            return None
        owner = owner.get(token)
    return owner if isinstance(owner, dict) else None


def _is_child_json_pointer(pointer: Any) -> bool:
    """Whether a value identifies a non-root JSON Pointer path."""

    return isinstance(pointer, str) and pointer.startswith("/") and pointer != "/"


def _json_pointer_tokens(pointer: Any) -> list[str] | None:
    """Decode a non-root JSON Pointer into unescaped path tokens."""

    if not _is_child_json_pointer(pointer):
        return None
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer[1:].split("/")
    ]


def _pop_json_pointer(record: dict[str, Any], pointer: Any) -> None:
    """Drop one JSON-pointer field from a copied record when it exists."""

    tokens = _json_pointer_tokens(pointer)
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
    """Return every valid path carried by original-id entries."""

    if not isinstance(originals, list):
        return []
    return [
        item["path"]
        for item in originals
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]


def _mapped_legacy_id_paths(detail: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Collect all identity-mapped legacy identifier paths."""

    if not isinstance(detail, Mapping):
        return ()
    paths = _original_id_paths(detail.get("original_ids"))
    mappings = detail.get("id_mappings")
    if isinstance(mappings, list):
        for mapping in mappings:
            if isinstance(mapping, dict):
                paths.extend(_original_id_paths(mapping.get("original_ids")))
    return tuple(dict.fromkeys(paths))


def _semantic_identity_owners(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every owner whose production labels are not training content."""

    owners = [record]
    for side in ("chosen", "rejected"):
        owner = record.get(side)
        if isinstance(owner, dict):
            owners.append(owner)
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, Mapping) else None
    if isinstance(trajectory, dict):
        owners.append(trajectory)
    return owners


def _identity_stage_detail_of(decision: ComposeDecision) -> dict[str, Any] | None:
    """Return the recorded identity-stage detail mapping."""

    identity_stage = next(
        (item for item in decision.stages if item.get("lane") == "identity"), None
    )
    detail = identity_stage.get("detail") if isinstance(identity_stage, dict) else None
    return detail if isinstance(detail, dict) else None


def _strip_assigned_ids(semantic: dict[str, Any], detail: dict[str, Any] | None) -> None:
    """Drop coordinate-derived identifiers assigned by identity curation."""

    mappings = detail.get("id_mappings") if isinstance(detail, dict) else None
    for mapping in mappings if isinstance(mappings, list) else ():
        if not isinstance(mapping, dict):
            continue
        owner = _identity_owner(semantic, mapping.get("owner_path"))
        if owner is not None and owner.get("id") == mapping.get("output_id"):
            owner.pop("id", None)
    for path in _mapped_legacy_id_paths(detail):
        _pop_json_pointer(semantic, path)


def _strip_provenance_labels(semantic: dict[str, Any]) -> None:
    """Drop pipeline provenance labels from every semantic identity owner."""

    labels = ("factory", "generator", "generator_version", "run", "round")
    for owner in _semantic_identity_owners(semantic):
        meta = owner.get("meta")
        if not isinstance(meta, dict):
            continue
        for label in labels:
            meta.pop(label, None)


def _strip_sidecar_binding(semantic: dict[str, Any]) -> None:
    """Drop source-coordinate bindings while retaining reward semantics."""

    annotation = semantic.get(curate_rewards.ANNOTATION_FIELD)
    if not isinstance(annotation, dict):
        return
    annotation.pop("source_sidecar_id", None)
    magnitude = annotation.get("magnitude")
    values = magnitude.get("values") if isinstance(magnitude, dict) else None
    for value in values if isinstance(values, list) else ():
        if isinstance(value, dict):
            value.pop("calibration_source", None)


def _post_transform_semantic_sha256(
    decision: ComposeDecision, context: SourceLineContext
) -> str:
    """Hash training content without coordinate-derived bindings."""

    if decision.record is None:
        raise ComposeError("cannot hash a missing curated record")
    semantic = copy.deepcopy(decision.record)
    _strip_assigned_ids(semantic, _identity_stage_detail_of(decision))
    _strip_provenance_labels(semantic)
    _strip_sidecar_binding(semantic)
    return context.canonical_sha256(semantic)


def _is_retained_record(decision: ComposeDecision) -> bool:
    """Whether a decision carries a record eligible for semantic indexing."""

    return decision.action == ACTION_RETAINED and decision.record is not None


def _deduplicate_curated_record(
    decision: ComposeDecision, context: SourceLineContext
) -> ComposeDecision:
    """Exclude records that converge only after lossy curation lanes."""

    seen = context.seen_curated_semantics
    if seen is None or not _is_retained_record(decision):
        return decision
    semantic_sha256 = _post_transform_semantic_sha256(decision, context)
    first = seen.get(semantic_sha256)
    if first is None:
        seen[semantic_sha256] = (context.source_path, context.source_line)
        return decision
    duplicate = stage(
        DEDUP_STAGE,
        ACTION_EXCLUDED,
        reason_codes=[REASON_DUPLICATE_CURATED_RECORD],
        semantic_sha256=semantic_sha256,
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
    """Build one source-lane exclusion with authenticated evidence."""

    evidence = stage(
        SOURCE_STAGE,
        ACTION_EXCLUDED,
        reason_codes=[reason],
        detail=detail,
    )
    return ComposeDecision(ACTION_EXCLUDED, None, (reason,), (evidence,), None, None)


def _source_exclusion(
    context: SourceLineContext, reason: str, detail: dict[str, Any]
) -> ComposeDecision:
    implementation = context.excluded_source_line or _excluded_source_line
    return implementation(reason, detail)


def _decode_source_line(
    physical_line: bytes, context: SourceLineContext
) -> str | ComposeDecision:
    """Decode one physical line or return its UTF-8 exclusion."""

    try:
        return physical_line.decode("utf-8")
    except UnicodeDecodeError as exc:
        return _source_exclusion(context, REASON_INVALID_UTF8, {"error": str(exc)})


def _parse_source_record(
    text: str, context: SourceLineContext
) -> tuple[Any, str] | ComposeDecision:
    """Parse and semantically hash one fail-closed JSON document."""

    try:
        record = json.loads(
            text,
            object_pairs_hook=context.duplicate_key_rejector,
            parse_constant=context.constant_rejector,
        )
        return record, context.canonical_sha256(record)
    except (ValueError, RecursionError) as exc:
        return _source_exclusion(context, REASON_INVALID_JSON, {"error": str(exc)})


def _duplicate_source_decision(
    semantic_sha256: str, context: SourceLineContext
) -> ComposeDecision | None:
    """Return source-semantic duplicate evidence when this row was seen."""

    seen = context.seen_source_semantics
    first = seen.get(semantic_sha256) if seen is not None else None
    if first is None:
        return None
    return _source_exclusion(
        context,
        REASON_DUPLICATE_SOURCE_RECORD,
        {
            "semantic_sha256": semantic_sha256,
            "first_source_path": first[0],
            "first_source_line": first[1],
        },
    )


def _curate_source_record(
    record: Any,
    source_sha256: str,
    context: SourceLineContext,
) -> ComposeDecision:
    """Apply record lanes and post-transform dedup to parsed source JSON."""

    source = SourceCoordinates(
        context.source_path,
        context.source_line,
        source_sha256,
        context.source_file_sha256,
    )
    record_context = RecordContext(
        source,
        context.calibration_lookup(record, context.calibration_catalog),
        context.trajectory_preferences,
    )
    try:
        decision = context.record_composer(record, record_context)
        deduplicate = context.deduplicate_curated_record
        if deduplicate is None:
            return _deduplicate_curated_record(decision, context)
        return deduplicate(
            decision,
            source_path=context.source_path,
            source_line=context.source_line,
            seen_curated_semantics=context.seen_curated_semantics,
        )
    except RecursionError as exc:
        return _source_exclusion(
            context,
            REASON_INVALID_JSON,
            {"error": f"recursion depth exhausted during curation: {exc}"},
        )


def _remember_source_semantics(
    semantic_sha256: str,
    decision: ComposeDecision,
    context: SourceLineContext,
) -> None:
    """Index a source semantic only after its curated record is retained."""

    seen = context.seen_source_semantics
    if seen is None or not _is_retained_record(decision):
        return
    seen[semantic_sha256] = (context.source_path, context.source_line)


def compose_source_line(
    physical_line: bytes, context: SourceLineContext
) -> ComposeDecision:
    """Compose one LF-framed source line using the run writer's contract."""

    decoded = _decode_source_line(physical_line, context)
    if isinstance(decoded, ComposeDecision):
        return decoded
    parsed = _parse_source_record(decoded, context)
    if isinstance(parsed, ComposeDecision):
        return parsed
    record, semantic_sha256 = parsed
    if duplicate := _duplicate_source_decision(semantic_sha256, context):
        return duplicate
    decision = _curate_source_record(record, sha256_hex(physical_line), context)
    _remember_source_semantics(semantic_sha256, decision, context)
    return decision


def transform_contract(reviewed_trajectory_module: Any = None) -> dict[str, Any]:
    """Return the exact transform declaration written into COMPOSE.json."""

    reviewed = reviewed_trajectory_module is not None
    trajectory = {
        "name": (
            reviewed_trajectory_module.TRANSFORM_NAME
            if reviewed
            else "trajectory-pair-preference-curation"
        ),
        "version": (
            reviewed_trajectory_module.TRANSFORM_VERSION
            if reviewed
            else "1.1.0-compatible-core"
        ),
        "implementation": "reviewed_module" if reviewed else "compatible_core",
    }
    return {
        "identity": {
            "name": curate_identity.TRANSFORM_NAME,
            "version": curate_identity.TRANSFORM_VERSION,
        },
        "bridge": {
            "name": curate_bridge.TRANSFORM_NAME,
            "version": curate_bridge.TRANSFORM_VERSION,
        },
        "preferences": {
            "name": curate_preferences.TRANSFORM_NAME,
            "version": curate_preferences.TRANSFORM_VERSION,
            "trajectory": trajectory,
        },
        "coding": {
            "name": curate_coding.TRANSFORM_NAME,
            "version": curate_coding.TRANSFORM_VERSION,
            "registered_agentic": {
                "name": curate_agentic.TRANSFORM_NAME,
                "version": curate_agentic.TRANSFORM_VERSION,
                "record_kinds": ["multi_agent", "safety_case"],
            },
        },
        "rewards": {
            "name": curate_rewards.ANNOTATION_FIELD,
            "version": curate_rewards.REWARD_TRANSFORM_VERSION,
        },
    }


if __package__:
    _expose_package_sibling(__name__)
