#!/usr/bin/env python3
"""Lane-manifest entry parsing for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

A lane manifest is either JSONL (one entry per line) or a JSON document whose
entry list sits at the top level or under one of ``MANIFEST_LIST_KEYS``. Both
shapes are parsed from bytes that were captured once, and every entry is then
normalized to one flat record-level vocabulary before authentication.

``collect_lane_manifests`` then folds every lane's normalized entries into the
corpus-level view the curation manifest publishes: exclusions, quarantines,
repairs, the stratified-review candidate pool, per-lane action counts, reason
codes, and the retained identity mappings.
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_manifests")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from .check_records import reject_json_constant
    from .exact_json import parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_manifests"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    from check_records import reject_json_constant
    from exact_json import parse_finite_json_float

GateError = _contract.GateError
MANIFEST_LIST_KEYS = _contract.MANIFEST_LIST_KEYS
DERIVED_CHANGE_REASON = _contract.DERIVED_CHANGE_REASON
EXCLUSION_ACTIONS = _contract.EXCLUSION_ACTIONS
QUARANTINE_ACTIONS = _contract.QUARANTINE_ACTIONS
REPAIR_ACTIONS = _contract.REPAIR_ACTIONS
RETAIN_ACTIONS = _contract.RETAIN_ACTIONS
record_sha256 = _digest.record_sha256
_lf_lines = _digest._lf_lines
_normalized_sha256 = _digest._normalized_sha256
_read_regular_file_snapshot = _digest._read_regular_file_snapshot


def _manifest_entries(
    path: Path,
    format_hint: str | None = None,
    *,
    payload: bytes | None = None,
) -> list[dict[str, Any]]:
    if format_hint not in {None, "json", "jsonl"}:
        raise GateError(f"{path}: unsupported manifest format {format_hint!r}")
    if payload is None:
        payload, _digest, _size = _read_regular_file_snapshot(path, "lane manifest")
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise GateError(f"cannot decode lane manifest {path}: {exc}") from exc
    if format_hint == "jsonl" or (format_hint is None and path.suffix == ".jsonl"):
        return _jsonl_manifest_entries(path, text)
    return _json_manifest_entries(path, text)


def _jsonl_manifest_entries(path: Path, text: str) -> list[dict[str, Any]]:
    """One object per non-blank line, refused at the first bad line."""
    entries = []
    for number, line in enumerate(_lf_lines(text), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(
                line,
                parse_constant=reject_json_constant,
                parse_float=parse_finite_json_float,
            )
        except ValueError as exc:
            raise GateError(f"{path}:{number}: invalid JSON manifest line: {exc}") from exc
        if not isinstance(entry, dict):
            raise GateError(f"{path}:{number}: manifest entry must be an object")
        entries.append(entry)
    return entries


def _json_manifest_entries(path: Path, text: str) -> list[dict[str, Any]]:
    """A top-level list, or the first ``MANIFEST_LIST_KEYS`` list in an object."""
    try:
        document = json.loads(
            text,
            parse_constant=reject_json_constant,
            parse_float=parse_finite_json_float,
        )
    except ValueError as exc:
        raise GateError(f"{path}: invalid JSON: {exc}") from exc
    if isinstance(document, list):
        candidates = document
    elif isinstance(document, dict):
        candidates = None
        for key in MANIFEST_LIST_KEYS:
            value = document.get(key)
            if isinstance(value, list):
                candidates = value
                break
        if candidates is None:
            raise GateError(
                f"{path}: manifest object needs one of {', '.join(MANIFEST_LIST_KEYS)} as a list"
            )
    else:
        raise GateError(f"{path}: manifest must be a list or an object")
    for entry in candidates:
        if not isinstance(entry, dict):
            raise GateError(f"{path}: every manifest entry must be an object")
    return list(candidates)


def _preserved_identity_detail(entry):
    if entry.get("record_kind") == "fault_recovery":
        return {"identity_detail": copy.deepcopy(entry)}
    return {}


def _normalize_entry(entry: dict[str, Any], lane: dict[str, Any]) -> dict[str, Any]:
    source = entry.get("source")
    if not isinstance(source, dict):
        source = {}
    transform_value = entry.get("transform")
    if isinstance(transform_value, dict):
        transform = transform_value
        transform_name = transform.get("name")
        transform_version = transform.get("version")
    else:
        transform_name = transform_value if isinstance(transform_value, str) else None
        transform_version = None
    declared_transform = entry.get("transform_name") or transform_name
    declared_version = entry.get("transform_version") or transform_version
    reasons = entry.get("reason_codes")
    if reasons is None:
        reasons = []
    return {
        "lane_order": lane["order"],
        "transform": declared_transform or lane["transform"],
        "version": declared_version or lane["version"],
        "declared_transform": declared_transform,
        "declared_version": declared_version,
        "action": entry.get("action"),
        "reason_codes": copy.deepcopy(reasons),
        "source_path": entry.get("source_path") or source.get("path"),
        "source_line": (
            entry.get("source_line") if entry.get("source_line") is not None else source.get("line")
        ),
        "source_hash": (
            entry.get("source_hash") or entry.get("source_sha256") or source.get("sha256")
        ),
        "record_kind": entry.get("record_kind") or entry.get("kind"),
        "classification": entry.get("classification"),
        "output_id": entry.get("output_id"),
        "output_hash": entry.get("output_hash") or entry.get("output_sha256"),
        "id_mappings": copy.deepcopy(entry.get("id_mappings")),
        "provenance_mappings": copy.deepcopy(entry.get("provenance_mappings")),
        "manifest_entry_sha256": record_sha256(entry),
        **_preserved_identity_detail(entry),
    }


# ---------------------------------------------------------------------------
# folding every lane's manifest into exclusions, repairs and counts
# ---------------------------------------------------------------------------


def _public_manifest_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in entry.items() if not key.startswith("_")}


class _LaneManifestFold:
    """Accumulator for the corpus-level view folded out of every lane."""

    def __init__(self) -> None:
        self.exclusions: list[dict[str, Any]] = []
        self.quarantines: list[dict[str, Any]] = []
        self.repairs: list[dict[str, Any]] = []
        self.review_candidates: list[dict[str, Any]] = []
        self.actions_by_lane: dict[str, dict[str, int]] = {}
        self.reason_counts: Counter[str] = Counter()
        self.identity_mappings: list[dict[str, Any]] = []

    def result(self) -> dict[str, Any]:
        return {
            "actions_by_lane": self.actions_by_lane,
            "lanes_without_manifest": [],
            "exclusions": self.exclusions,
            "quarantines": self.quarantines,
            "repairs": self.repairs,
            "identity_mappings": self.identity_mappings,
            "review_candidates": self.review_candidates,
            "reason_codes": dict(sorted(self.reason_counts.items())),
        }


class RetentionView(NamedTuple):
    """What survived composition, and each surviving source record's digest.

    Both are ``None`` during integration, when every declared source is still
    in play; promotion supplies them from the authenticated bindings.
    """

    retained_source_keys: set[tuple[str, int]] | None = None
    source_record_sha256_by_key: dict[tuple[str, int], str] | None = None

    def retains(self, source_key: Any) -> bool:
        return self.retained_source_keys is None or source_key in self.retained_source_keys


class _NormalizedEntry(NamedTuple):
    """One manifest entry after normalisation, with its action already lowered."""

    normalized: dict[str, Any]
    lowered: str
    source_key: Any


def _entry_view(entry: dict[str, Any], source_key: Any, view: RetentionView) -> dict[str, Any]:
    """The public entry with ``content_changed`` resolved against retention."""
    retained_source_keys = view.retained_source_keys
    source_record_sha256_by_key = view.source_record_sha256_by_key
    normalized = _public_manifest_entry(entry)
    if retained_source_keys is not None and source_key not in retained_source_keys:
        # ``content_changed`` is derived from a source record that is
        # intentionally absent after a later terminal disposition.
        # Keep the repair action/reasons, but omit this non-replayable
        # convenience field in both integration and promotion views.
        normalized.pop("content_changed", None)
    if (
        source_record_sha256_by_key is not None
        and source_key in source_record_sha256_by_key
        and normalized.get("output_hash") is not None
        and (retained_source_keys is None or source_key in retained_source_keys)
    ):
        normalized["content_changed"] = (
            normalized["output_hash"] != source_record_sha256_by_key[source_key]
        )
    return normalized


def _classify_entry(
    fold: _LaneManifestFold,
    row: _NormalizedEntry,
    view: RetentionView,
) -> None:
    """Route one normalized entry into the disposition and review buckets."""
    normalized, lowered, source_key = row
    if lowered in EXCLUSION_ACTIONS:
        fold.exclusions.append(normalized)
        fold.review_candidates.append(normalized)
        fold.reason_counts.update(normalized["reason_codes"] or ["UNSPECIFIED"])
    elif lowered in QUARANTINE_ACTIONS:
        fold.quarantines.append(normalized)
        fold.review_candidates.append(normalized)
        fold.reason_counts.update(normalized["reason_codes"] or ["UNSPECIFIED"])
    elif lowered in REPAIR_ACTIONS:
        fold.repairs.append(normalized)
        fold.review_candidates.append(normalized)
    elif lowered in RETAIN_ACTIONS and normalized.get("content_changed") and view.retains(
        source_key
    ):
        derived = copy.deepcopy(normalized)
        derived["review_action"] = "changed"
        derived["review_reason_codes"] = [DERIVED_CHANGE_REASON]
        fold.review_candidates.append(derived)


def _fold_lane(fold: _LaneManifestFold, lane: dict[str, Any], view: RetentionView) -> None:
    counts: Counter[str] = Counter()
    for entry in lane["entries"]:
        source_key = entry.get("_source_key")
        normalized = _entry_view(entry, source_key, view)
        action = normalized["action"]
        key = str(action) if action is not None else "unspecified"
        counts[key] += 1
        lowered = key.strip().lower()
        _classify_entry(fold, _NormalizedEntry(normalized, lowered, source_key), view)
        if (
            lane["transform"] == "curate_identity"
            and lowered == "retained"
            and view.retains(source_key)
        ):
            normalized["source_originals_sha256"] = _normalized_sha256(
                entry.get("_source_originals_sha256"),
                "retained identity source originals",
            )
            fold.identity_mappings.append(normalized)
    fold.actions_by_lane[lane["transform"]] = dict(sorted(counts.items()))


def collect_lane_manifests(
    prepared_lanes: Sequence[dict[str, Any]],
    retained_source_keys: set[tuple[str, int]] | None = None,
    source_record_sha256_by_key: dict[tuple[str, int], str] | None = None,
) -> dict[str, Any]:
    """Fold every lane's record-level manifest into exclusions and counts."""
    fold = _LaneManifestFold()
    for lane in prepared_lanes:
        _fold_lane(
            fold,
            lane,
            RetentionView(retained_source_keys, source_record_sha256_by_key),
        )
    return fold.result()


if __package__:
    _expose_package_sibling(__name__)
