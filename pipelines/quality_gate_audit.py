#!/usr/bin/env python3
"""Run scanning, mix enforcement, and manifest I/O for the quality gate."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import NamedTuple, Optional

from check_records import walk_key
from quality_gate_embedding import (
    DEFAULT_EMBEDDING_THRESHOLD,
    DEFAULT_MAX_EMBEDDING_PAIRS,
    EMBEDDING_CANDIDATE_SKETCH,
    EMBEDDING_ENCODER,
    _embedding_duplicates,
    embedding_tokens,
    validate_embedding_threshold,
)
from quality_gate_identity import record_hash
from training_audit import reward_shape


DEFAULT_TARGET_SYNTHETIC_RATIO: float = 0.30
DEFAULT_MIX_TOLERANCE: float = 0.20
SYNTHETIC_KINDS = frozenset({"designed", "simulated", "hil"})
REAL_KINDS = frozenset({"real", "unknown"})
MAX_ERROR_EXAMPLES = 10


def _validate_ratio(name, value):
    if value is None:
        return
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite ratio in [0, 1], got {value!r}")


class MixPolicy(NamedTuple):
    """Blocking synthetic/real mix policy. Defaults to roughly 30/70."""

    target: float = DEFAULT_TARGET_SYNTHETIC_RATIO
    tolerance: float = DEFAULT_MIX_TOLERANCE
    max_synthetic_ratio: Optional[float] = None
    min_synthetic_ratio: Optional[float] = None
    max_unlabeled_ratio: Optional[float] = None

    @property
    def ceiling(self) -> float:
        if self.max_synthetic_ratio is not None:
            return self.max_synthetic_ratio
        return min(1.0, self.target + self.tolerance)

    def validate(self) -> "MixPolicy":
        values = (
            ("mix target", self.target),
            ("mix tolerance", self.tolerance),
            ("max synthetic ratio", self.max_synthetic_ratio),
            ("min synthetic ratio", self.min_synthetic_ratio),
            ("max unlabeled ratio", self.max_unlabeled_ratio),
        )
        for name, value in values:
            _validate_ratio(name, value)
        if self.min_synthetic_ratio is not None:
            self._validate_floor()
        return self

    def _validate_floor(self):
        if self.min_synthetic_ratio > self.ceiling:
            raise ValueError(
                f"min synthetic ratio {self.min_synthetic_ratio} exceeds the "
                f"blocking ceiling {self.ceiling}"
            )

    def as_dict(self) -> dict:
        return {
            "target_synthetic_ratio": self.target,
            "tolerance": self.tolerance,
            "max_synthetic_ratio": self.ceiling,
            "min_synthetic_ratio": self.min_synthetic_ratio,
            "max_unlabeled_ratio": self.max_unlabeled_ratio,
            "blocking": True,
        }


@dataclass(frozen=True)
class AuditOptions:
    """Validated options for one quality-gate scan."""

    threshold: float = DEFAULT_EMBEDDING_THRESHOLD
    mix_policy: MixPolicy = MixPolicy()
    embedding_dedup: bool = True
    max_embedding_pairs: int = DEFAULT_MAX_EMBEDDING_PAIRS


def _validate_pair_cap(max_pairs):
    if max_pairs < 1:
        raise ValueError(f"max_embedding_pairs must be >= 1, got {max_pairs!r}")
    return max_pairs


def _options_with_overrides(options, overrides):
    if isinstance(options, (int, float)) and not isinstance(options, bool):
        overrides = {"threshold": options, **overrides}
        options = None
    base = options or AuditOptions()
    if not isinstance(base, AuditOptions):
        raise ValueError("options must be an AuditOptions value")
    try:
        return replace(base, **overrides)
    except TypeError as exc:
        raise ValueError(str(exc)) from exc


def _validated_options(options, overrides):
    selected = _options_with_overrides(options, overrides)
    validate_embedding_threshold(selected.threshold)
    _validate_pair_cap(selected.max_embedding_pairs)
    policy = (selected.mix_policy or MixPolicy()).validate()
    return replace(selected, mix_policy=policy)


def _state_provenance_kind(state):
    if not isinstance(state, dict):
        return None
    kind = state.get("sim_or_real")
    if kind:
        return str(kind)
    nested = state.get("provenance")
    if isinstance(nested, dict) and nested.get("kind"):
        return str(nested["kind"])
    return None


def _owner_provenance_kind(owner):
    if not isinstance(owner, dict):
        return None
    state_kind = _state_provenance_kind(owner.get("state"))
    if state_kind:
        return state_kind
    provenance = owner.get("provenance")
    if isinstance(provenance, dict) and provenance.get("kind"):
        return str(provenance["kind"])
    return None


_NOT_PREFERENCE = object()


def _preference_provenance(record):
    if "chosen" not in record and "rejected" not in record:
        return _NOT_PREFERENCE
    chosen = _owner_provenance_kind(record.get("chosen"))
    rejected = _owner_provenance_kind(record.get("rejected"))
    if chosen and chosen == rejected:
        return chosen
    if chosen or rejected:
        return None
    return _NOT_PREFERENCE


def _bridge_provenance_kind(record):
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, dict) else None
    return _owner_provenance_kind(trajectory)


def _top_level_provenance_kind(record):
    provenance = record.get("provenance")
    if isinstance(provenance, dict) and provenance.get("kind"):
        return str(provenance["kind"])
    return None


def _has_factory_origin(record):
    meta = record.get("meta")
    factory = meta.get("factory") if isinstance(meta, dict) else None
    return isinstance(factory, str) and bool(factory.strip())


def _record_provenance_kind(record):
    if not isinstance(record, dict):
        return None
    state_kind = _state_provenance_kind(record.get("state"))
    if state_kind:
        return state_kind
    preference_kind = _preference_provenance(record)
    if preference_kind is not _NOT_PREFERENCE:
        return preference_kind
    bridge_kind = _bridge_provenance_kind(record)
    if bridge_kind:
        return bridge_kind
    top_level = _top_level_provenance_kind(record)
    if _has_factory_origin(record) and top_level in (None, "unknown"):
        return "designed"
    return top_level


@dataclass
class ScanState:
    hashes: Counter = field(default_factory=Counter)
    first_seen: dict = field(default_factory=dict)
    provenance: Counter = field(default_factory=Counter)
    reward_keys: Counter = field(default_factory=Counter)
    reward_shapes: Counter = field(default_factory=Counter)
    records_with_rewards: int = 0
    total: int = 0
    kept: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    exact_clusters: dict = field(default_factory=lambda: defaultdict(list))
    unreadable_files: int = 0
    malformed_lines: int = 0
    unreadable_examples: list = field(default_factory=list)
    malformed_examples: list = field(default_factory=list)


def _record_unreadable(state, rel, exc):
    state.unreadable_files += 1
    if len(state.unreadable_examples) < MAX_ERROR_EXAMPLES:
        state.unreadable_examples.append(
            {"file": str(rel), "error": f"{type(exc).__name__}: {exc}"}
        )


def _read_jsonl(path, rel, state):
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        _record_unreadable(state, rel, exc)
        return ()


def _record_malformed(state, rel, lineno, exc):
    state.malformed_lines += 1
    if len(state.malformed_examples) < MAX_ERROR_EXAMPLES:
        state.malformed_examples.append(
            {"file": str(rel), "line": lineno, "error": str(exc)}
        )


_PARSE_FAILED = object()


def _parse_record(line, rel, lineno, state):
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        _record_malformed(state, rel, lineno, exc)
        return _PARSE_FAILED


def _consume_identity(obj, where, state, embedding_dedup):
    digest = record_hash(obj)
    state.hashes[digest] += 1
    state.exact_clusters[digest].append(where)
    if state.hashes[digest] == 1:
        state.first_seen[digest] = where
        if embedding_dedup:
            state.kept.append({**where, "tokens": embedding_tokens(obj)})
        return
    origin = state.first_seen[digest]
    state.duplicates.append(
        {
            **where,
            "hash": digest,
            "kind": "exact",
            "duplicate_of": dict(origin),
            "reason": (
                f"exact content hash {digest} already seen at "
                f"{origin['file']}:{origin['line']}"
            ),
        }
    )


def _consume_provenance(obj, state):
    kind = _record_provenance_kind(obj)
    if kind:
        state.provenance[kind] += 1


def _consume_rewards(obj, state):
    rewards = list(walk_key(obj, "reward_components"))
    state.records_with_rewards += int(bool(rewards))
    for _path, reward in rewards:
        if isinstance(reward, dict):
            state.reward_keys.update(str(key) for key in reward)
        state.reward_shapes[reward_shape(reward)] += 1


def _consume_record(obj, where, state, embedding_dedup):
    state.total += 1
    _consume_identity(obj, where, state, embedding_dedup)
    _consume_provenance(obj, state)
    _consume_rewards(obj, state)


def _scan_jsonl_file(path, run_dir, state, embedding_dedup):
    rel = path.relative_to(run_dir)
    for lineno, line in enumerate(_read_jsonl(path, rel, state), 1):
        if not line.strip():
            continue
        obj = _parse_record(line, rel, lineno, state)
        if obj is not _PARSE_FAILED:
            _consume_record(
                obj,
                {"file": str(rel), "line": lineno},
                state,
                embedding_dedup,
            )


def _scan_run(run_dir, embedding_dedup):
    state = ScanState()
    for path in sorted(run_dir.rglob("*.jsonl")):
        _scan_jsonl_file(path, run_dir, state, embedding_dedup)
    return state


def _disabled_embedding_report(threshold):
    return {
        "enabled": False,
        "encoder": EMBEDDING_ENCODER,
        "candidate_sketch": EMBEDDING_CANDIDATE_SKETCH,
        "threshold": threshold,
        "compared_records": 0,
        "candidate_pairs": 0,
        "truncated": False,
    }


def _embedding_report(scan, options):
    if not options.embedding_dedup:
        return [], [], _disabled_embedding_report(options.threshold)
    return _embedding_duplicates(
        scan.kept, options.threshold, options.max_embedding_pairs
    )


def _exact_duplicate_clusters(scan):
    return [
        {
            "kind": "exact",
            "hash": digest,
            "size": len(members),
            "representative": dict(members[0]),
            "members": [dict(member) for member in members],
            "reason": f"{len(members)} records share exact content hash {digest}",
        }
        for digest, members in scan.exact_clusters.items()
        if len(members) > 1
    ]


def _mix_report(total, provenance):
    synthetic = sum(value for key, value in provenance.items() if key in SYNTHETIC_KINDS)
    real_unknown = sum(value for key, value in provenance.items() if key in REAL_KINDS)
    unlabeled = total - synthetic - real_unknown
    labeled = synthetic + real_unknown
    return {
        "synthetic": synthetic,
        "real_unknown": real_unknown,
        "unlabeled": unlabeled,
        "total": total,
        "provenance": dict(provenance),
        "synthetic_ratio": synthetic / total if total else 0.0,
        "unlabeled_ratio": unlabeled / total if total else 0.0,
        "labeled_synthetic_ratio": synthetic / labeled if labeled else 0.0,
    }


def _input_messages(scan):
    blockers = []
    warnings = []
    if scan.unreadable_files:
        blockers.append(f"{scan.unreadable_files} file(s) unreadable/undecodable")
        warnings.append(
            f"{scan.unreadable_files} file(s) unreadable/undecodable — counts, "
            "mix and dedup cover only the readable subset"
        )
    if scan.malformed_lines:
        blockers.append(f"{scan.malformed_lines} malformed JSON line(s)")
        warnings.append(
            f"{scan.malformed_lines} malformed JSON line(s) skipped — counts, "
            "mix and dedup cover only the parseable subset"
        )
    return blockers, warnings


def _duplicate_messages(exact_count, embedding_duplicates, threshold):
    blockers = []
    if exact_count:
        blockers.append(f"{exact_count} exact-hash duplicate record(s) must be excluded")
    if embedding_duplicates:
        blockers.append(
            f"{len(embedding_duplicates)} embedding near-duplicate record(s) "
            f"(cosine > {threshold}) must be excluded"
        )
    return blockers


def _synthetic_ratio_messages(mix, policy):
    ratio = mix["synthetic_ratio"]
    if ratio > policy.ceiling:
        return [
            f"synthetic_ratio {ratio:.2f} > {policy.ceiling:.2f} — mix policy is "
            f"~{policy.target:.2f} synthetic / {1 - policy.target:.2f} real "
            f"(Demystifying Synthetic Data), tolerance {policy.tolerance:.2f}"
        ], []
    if ratio > policy.target:
        return [], [
            f"synthetic_ratio {ratio:.2f} > target {policy.target:.2f} but within "
            f"the blocking ceiling {policy.ceiling:.2f} — SOTA recommends "
            f"~{policy.target:.2f} synthetic / {1 - policy.target:.2f} real "
            "(Demystifying Synthetic Data)"
        ]
    return [], []


def _unlabeled_ratio_messages(mix, policy):
    ratio = mix["unlabeled_ratio"]
    if policy.max_unlabeled_ratio is not None and ratio > policy.max_unlabeled_ratio:
        return [
            f"unlabeled_ratio {ratio:.2f} > {policy.max_unlabeled_ratio:.2f} — "
            "mix cannot be enforced on unlabeled data"
        ], []
    if ratio > 0.5:
        return [], [
            f"unlabeled_ratio {ratio:.2f} — the enforced synthetic_ratio "
            "understates the real synthetic share"
        ]
    return [], []


def _mix_messages(mix, policy):
    blockers = []
    warnings = []
    if mix["total"]:
        ratio_blockers, ratio_warnings = _synthetic_ratio_messages(mix, policy)
        unlabeled_blockers, unlabeled_warnings = _unlabeled_ratio_messages(mix, policy)
        blockers.extend(ratio_blockers + unlabeled_blockers)
        warnings.extend(ratio_warnings + unlabeled_warnings)
    if policy.min_synthetic_ratio is not None:
        if mix["synthetic_ratio"] < policy.min_synthetic_ratio:
            blockers.append(
                f"synthetic_ratio {mix['synthetic_ratio']:.2f} < floor "
                f"{policy.min_synthetic_ratio:.2f}"
            )
    return blockers, warnings


def _embedding_messages(stats, options):
    blockers = []
    warnings = []
    if stats["truncated"]:
        blockers.append(
            f"embedding candidate cap {options.max_embedding_pairs} reached — "
            "near-duplicate recall is partial, so this run cannot be certified"
        )
    if not options.embedding_dedup:
        warnings.append(
            "embedding dedup disabled — only exact-hash duplicates were excluded"
        )
    return blockers, warnings


def _quality_messages(scan, mix, embedding_result, options):
    embedding_duplicates, _embedding_clusters, embedding_stats = embedding_result
    exact_count = len(scan.duplicates)
    blockers = _duplicate_messages(exact_count, embedding_duplicates, options.threshold)
    warnings = []
    for new_blockers, new_warnings in (
        _input_messages(scan),
        _mix_messages(mix, options.mix_policy),
        _embedding_messages(embedding_stats, options),
    ):
        blockers.extend(new_blockers)
        warnings.extend(new_warnings)
    return blockers, warnings


def _reward_shape_report(scan):
    return {
        "records_with_reward_components": scan.records_with_rewards,
        "unique_component_keys": len(scan.reward_keys),
        "unique_shapes": len(scan.reward_shapes),
        "top_component_keys": scan.reward_keys.most_common(20),
        "top_shapes": scan.reward_shapes.most_common(10),
    }


def _error_report(scan):
    return {
        "unreadable_files": scan.unreadable_files,
        "malformed_lines": scan.malformed_lines,
        "unreadable_examples": scan.unreadable_examples,
        "malformed_examples": scan.malformed_examples,
    }


def _count_report(scan, embedding_clusters, duplicates):
    return {
        "total": scan.total,
        "unique_hashes": len(scan.hashes),
        "duplicate_groups": sum(count > 1 for count in scan.hashes.values()),
        "embedding_duplicate_groups": len(embedding_clusters),
        "excluded_records": len(duplicates),
        "unreadable_files": scan.unreadable_files,
        "malformed_lines": scan.malformed_lines,
    }


def _audit_result(scan, mix, embedding_result, options):
    embedding_duplicates, embedding_clusters, embedding = embedding_result
    duplicates = [*scan.duplicates, *embedding_duplicates]
    clusters = [*_exact_duplicate_clusters(scan), *embedding_clusters]
    blockers, warnings = _quality_messages(
        scan, mix, embedding_result, options
    )
    return {
        "counts": _count_report(scan, embedding_clusters, duplicates),
        "mix": mix,
        "mix_policy": options.mix_policy.as_dict(),
        "duplicates": duplicates,
        "duplicate_clusters": clusters,
        "embedding": embedding,
        "reward_shapes": _reward_shape_report(scan),
        "errors": _error_report(scan),
        "warnings": warnings,
        "blockers": blockers,
        "blocked": bool(blockers),
        "threshold": options.threshold,
    }


def audit_run(run_dir, options=None, **overrides):
    """Audit a run directory for exact/near duplicates and provenance mix."""
    selected = _validated_options(options, overrides)
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise ValueError(f"run directory does not exist or is not a directory: {run_dir}")
    scan = _scan_run(run_dir, selected.embedding_dedup)
    embedding_result = _embedding_report(scan, selected)
    mix = _mix_report(scan.total, scan.provenance)
    return _audit_result(scan, mix, embedding_result, selected)


def _same_or_ancestor(candidate, target):
    return candidate == target or candidate in target.parents


def _manifest_conflicts_with_run(path, run_dir, allow_within_run):
    if allow_within_run:
        return _same_or_ancestor(path, run_dir)
    return _same_or_ancestor(run_dir, path)


def validate_manifest_target(path, run_dir, *, allow_within_run=False):
    """Validate that a manifest target cannot overwrite audited evidence."""
    path = Path(path)
    run_dir = Path(run_dir)
    if path.suffix.lower() == ".jsonl":
        raise ValueError(f"manifest path must not be a JSONL input: {path}")
    if path.exists() or path.is_symlink():
        raise ValueError(f"refusing to overwrite existing manifest path: {path}")
    conflict = _manifest_conflicts_with_run(
        path.resolve(), run_dir.resolve(), allow_within_run
    )
    if conflict:
        _raise_manifest_conflict(path, allow_within_run)
    return path


def _raise_manifest_conflict(path, allow_within_run):
    if allow_within_run:
        raise ValueError(
            "manifest path must not equal or contain the promotion destination: "
            f"{path}"
        )
    raise ValueError(f"manifest path must be outside the audited run directory: {path}")


def write_manifest(path, run_dir, result, *, allow_within_run=False):
    """Create the curated sidecar manifest without overwriting any path."""
    path = validate_manifest_target(path, run_dir, allow_within_run=allow_within_run)
    manifest = {
        "schema": "quality-manifest/1",
        "generated_by": "pipelines/quality_gate.py",
        "run_dir": str(run_dir),
        **result,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(manifest, indent=2) + "\n")
    except OSError as exc:
        raise ValueError(
            f"could not create manifest {path}: {type(exc).__name__}: {exc}"
        ) from exc
    return path
