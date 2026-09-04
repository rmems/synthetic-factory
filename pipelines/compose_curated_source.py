#!/usr/bin/env python3
"""Source-line decoding, semantic deduplication, and transform declaration."""

from __future__ import annotations

import functools
import json
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_source")
    from . import compose_curated_source_pointers as _pointers
    from . import compose_curated_source_semantics as _semantics
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
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ComposeDecision,
        ComposeError,
        REASON_DUPLICATE_SOURCE_RECORD,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
        canonical_sha256,
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
    from .curate_identity import reject_duplicate_object_keys
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_source"
    )
    import compose_curated_source_pointers as _pointers
    import compose_curated_source_semantics as _semantics
    import curate_agentic
    import curate_bridge
    import curate_coding
    import curate_identity
    import curate_preferences
    import curate_rewards
    from check_records import reject_json_constant
    from compose_contract import (
        ACTION_EXCLUDED,
        COMPOSE_NAME,
        COMPOSE_VERSION,
        ComposeDecision,
        ComposeError,
        REASON_DUPLICATE_SOURCE_RECORD,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
        canonical_sha256,
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
    from curate_identity import reject_duplicate_object_keys

# JSON Pointer and identity-owner helpers, re-exported for importers.
_identity_owner = _pointers.identity_owner
_descendant_mapping = _pointers.descendant_mapping
_is_child_json_pointer = _pointers.is_child_json_pointer
_json_pointer_tokens = _pointers.json_pointer_tokens
_pop_json_pointer = _pointers.pop_json_pointer
_original_id_paths = _pointers.original_id_paths
_mapped_legacy_id_paths = _pointers.mapped_legacy_id_paths

# Semantic normalisation and post-transform dedup, re-exported likewise.
DEDUP_STAGE = _semantics.DEDUP_STAGE
_semantic_identity_owners = _semantics.semantic_identity_owners
_identity_stage_detail_of = _semantics.identity_stage_detail_of
_strip_assigned_ids = _semantics.strip_assigned_ids
_strip_provenance_labels = _semantics.strip_provenance_labels
_strip_sidecar_binding = _semantics.strip_sidecar_binding
_post_transform_semantic_sha256 = _semantics.post_transform_semantic_sha256
_is_retained_record = _semantics.is_retained_record
_deduplicate_curated_record = _semantics.deduplicate_curated_record

__all__ = """
DEDUP_STAGE SOURCE_STAGE SourceLineContext _curate_source_record _curated_deduplicator
_decode_source_line _deduplicate_curated_record _descendant_mapping
_duplicate_source_decision _excluded_source_line _identity_owner
_identity_stage_detail_of _is_child_json_pointer _is_retained_record
_json_pointer_tokens _mapped_legacy_id_paths _original_id_paths _parse_source_record
_pop_json_pointer _post_transform_semantic_sha256 _remember_source_semantics
_semantic_identity_owners _source_exclusion _strip_assigned_ids
_strip_provenance_labels _strip_sidecar_binding compose_source_line transform_contract
""".split()


SOURCE_STAGE = StageDefinition("source", COMPOSE_NAME, COMPOSE_VERSION)


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
    canonical_sha256: Any = canonical_sha256
    record_composer: Callable[[Any, RecordContext], ComposeDecision] = compose_record
    calibration_lookup: Callable[[Mapping[str, Any], Mapping[str, Any] | None], Any] = (
        calibration_for
    )
    duplicate_key_rejector: Callable[[list[tuple[str, Any]]], dict[str, Any]] = (
        reject_duplicate_object_keys
    )
    constant_rejector: Callable[[str], Any] = reject_json_constant
    excluded_source_line: Callable[[str, dict[str, Any]], ComposeDecision] | None = None
    deduplicate_curated_record: Callable[..., ComposeDecision] | None = None


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


def _curated_deduplicator(
    context: SourceLineContext,
) -> Callable[[ComposeDecision], ComposeDecision]:
    """Resolve the post-transform deduplicator this line's context supplies."""

    supplied: Any = context.deduplicate_curated_record
    if supplied is None:
        return lambda decision: _deduplicate_curated_record(decision, context)
    if not callable(supplied):
        raise ComposeError("source-line deduplicator must be callable or None")
    return functools.partial(
        supplied,
        source_path=context.source_path,
        source_line=context.source_line,
        seen_curated_semantics=context.seen_curated_semantics,
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
        return _curated_deduplicator(context)(decision)
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
