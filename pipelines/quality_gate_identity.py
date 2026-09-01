#!/usr/bin/env python3
"""Exact and semantic identity projections for the quality gate.

This module is deliberately dependency-free within ``pipelines`` so the
quality-gate CLI can re-export its public compatibility surface without
creating an import cycle.
"""

from __future__ import annotations

import hashlib
import json

from exact_json import dumps_exact_json, exact_fraction


_IDENTITY_FIELDS = (
    "state",
    "steps",
    "proposed_action",
    "safety_decision",
    "executed_action",
    "future_outcome",
    "outcome",
    "reward_components",
    "reward",
    # Multi-agent coordination records share generic reward envelopes. The
    # training unit is the joint decision, not the boolean success flag.
    "goal",
    "agents",
    "transcript",
    "disagreements",
    "resolution",
    "joint_outcome",
    # Long-horizon coding supervision includes the scenario and optional
    # initial approach as modeled training content. Omitting these fields can
    # collapse distinct coding tasks that happen to share steps and outcomes.
    "codebase_type",
    "bug_class",
    "plan",
    # Cascading-error recovery models the injected fault and its root-cause
    # diagnosis as training fields (prompts/09-cascading-error-recovery-
    # factory.md). Without them two records with identical goals, steps,
    # outcomes and rewards but different faults and diagnoses collapse to one
    # exact hash, and promotion drops the second as a duplicate.
    "error_introduced",
    "diagnosis",
    # Thalamic distillation is driven by ``spike_events`` + ``state``
    # (prompts/01-thalamic-trajectory-factory.md), and the event-language
    # bridge models the paired language view, bridge notes, raster sidecar,
    # per-check gate-compute budget, and spike-implemented gate head
    # (prompts/03-neuromorphic-event-language-bridge.md). The gate head is
    # carrier-normalized below; these fields keep the rest of a bridge
    # record's modeled content in the projection rather than only its stream.
    "spike_events",
    "language_view",
    "bridge_notes",
    "raster",
    "gate_compute",
    # Safety-calibration supervision is the gate label and its observable
    # reason (prompts/12-safety-calibration-factory.md); goal/outcome/reward
    # alone cannot separate a correct refusal from a missed one.
    "case_type",
    "rationale",
    "decision",
)

_CANONICAL_ID_KEYS = frozenset(
    {"episode_id", "record_id", "trajectory_id", "pair_id", "sample_id"}
)
_SEMANTIC_ROOT_BOOKKEEPING_KEYS = frozenset({"id", "meta"})
_SEMANTIC_CONTAINER_BOOKKEEPING_PARENTS = frozenset(
    {
        (),
        ("language_view", "trajectory"),
        ("chosen", "language_view", "trajectory"),
        ("rejected", "language_view", "trajectory"),
    }
)
# Promotion rewrites ``sim_or_real`` and files the original wording under
# ``provenance.claimed``, at the root or inside ``state``. That claim is
# bookkeeping about the promotion, not training content: leaving it in the
# semantic view lets otherwise identical records pass as distinct.
_SEMANTIC_PROMOTION_BOOKKEEPING_KEYS = frozenset({"provenance", "tag_provenance"})
# Where bookkeeping actually lives in the record contract. Stripping a
# canonical id at every depth would erase semantic action arguments such as
# ``executed_action.record_id``.
_SEMANTIC_BOOKKEEPING_PARENTS = frozenset(
    {
        (),
        ("state",),
        ("language_view", "trajectory"),
        ("language_view", "trajectory", "state"),
        ("chosen",),
        ("rejected",),
        ("chosen", "state"),
        ("rejected", "state"),
        ("chosen", "language_view", "trajectory"),
        ("rejected", "language_view", "trajectory"),
        ("chosen", "language_view", "trajectory", "state"),
        ("rejected", "language_view", "trajectory", "state"),
    }
)

_PREFERENCE_WRAPPER_FIELDS = _IDENTITY_FIELDS + (
    "critique",
    "reward_delta",
    "lesson_category",
)

_TRAJECTORY_GATE_COMPUTE = ("trajectory", "gate_compute")
_SAFETY_GATE_COMPUTE = ("trajectory", "safety_decision", "gate_compute")
_TRAJECTORY_GATE_SNN = ("trajectory", "gate_snn")
_SAFETY_GATE_SNN = ("trajectory", "safety_decision", "gate_snn")
_GATE_SNN_ROOT = "root"
_GATE_SNN_META = "meta"
_GATE_SNN_CARRIERS = (
    (_GATE_SNN_ROOT, ("gate_snn",)),
    (_GATE_SNN_META, ("meta", "gate_snn")),
    (_TRAJECTORY_GATE_SNN, ("language_view", *_TRAJECTORY_GATE_SNN)),
    (_SAFETY_GATE_SNN, ("language_view", *_SAFETY_GATE_SNN)),
)
_NO_GATE_SNN_CARRIER = object()
_RASTER_ROOT = "root"
_RASTER_META = "meta"
_NOT_CANONICAL_PRIMITIVE = object()


def _canonical_identity_primitive(value):
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["boolean", value]
    fraction = exact_fraction(value)
    if fraction is not None:
        return ["number", str(fraction.numerator), str(fraction.denominator)]
    if isinstance(value, str):
        return ["string", value]
    return _NOT_CANONICAL_PRIMITIVE


def _canonical_identity_value(value):
    """Return a collision-safe typed projection with exact numeric values."""

    primitive = _canonical_identity_primitive(value)
    if primitive is not _NOT_CANONICAL_PRIMITIVE:
        return primitive
    if isinstance(value, (list, tuple)):
        return ["array", [_canonical_identity_value(child) for child in value]]
    if isinstance(value, dict):
        return [
            "object",
            [[key, _canonical_identity_value(value[key])] for key in sorted(value)],
        ]
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def canonical_blob(value):
    """Return the stable JSON representation used by semantic encoders."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def canonical_numeric_value(value):
    """Return a typed value projection with numbers canonicalized exactly."""

    return _canonical_identity_value(value)


def _canonical_record_blob(value):
    """Return collision-safe record identity with numeric values canonicalized."""

    normalized = canonical_numeric_value(value)
    return dumps_exact_json(normalized, sort_keys=True, ensure_ascii=False)


def _preference_identity_side(value):
    """Return all modeled training fields from one preference side.

    Preference actions and outcomes are labels, not bookkeeping. Keeping only
    ``state`` made distinct preference training units exact-hash collisions.
    Malformed sides retain their complete value so unrelated malformed records
    do not all collapse to the same sentinel.
    """
    if not isinstance(value, dict):
        return value
    modeled = _with_bridge_sidecars(
        value, {key: value[key] for key in _IDENTITY_FIELDS if key in value}
    )
    return modeled or value


def _preference_identity_view(obj):
    view = {
        "chosen": _preference_identity_side(obj.get("chosen")),
        "rejected": _preference_identity_side(obj.get("rejected")),
    }
    for key in _PREFERENCE_WRAPPER_FIELDS:
        if key in obj:
            view[key] = obj[key]
    return view


def _bridge_raster_sidecar(obj):
    """Return the modeled raster regardless of its accepted carrier.

    Bridge curation accepts a dictionary raster at the record root or under
    ``meta.raster``, preferring the root carrier.  Exact identity uses the same
    resolution order but normalizes either location to the modeled ``raster``
    field so carrier placement alone does not change the training identity.
    """
    if "language_view" not in obj or "spike_events" not in obj:
        return None, None
    top_level = obj.get("raster")
    if isinstance(top_level, dict):
        return top_level, _RASTER_ROOT
    meta = obj.get("meta")
    nested = meta.get("raster") if isinstance(meta, dict) else None
    if isinstance(nested, dict):
        return nested, _RASTER_META
    return None, None


def _bridge_gate_compute_sidecar(obj):
    """Return the curator-selected gate-compute budget and nested carrier.

    ``curate_bridge`` prefers a dictionary at the record root, then under the
    language trajectory, then under that trajectory's safety decision.  The
    returned carrier is relative to ``language_view`` and is ``None`` for the
    canonical root location.
    """
    if "language_view" not in obj or "spike_events" not in obj:
        return None, None
    top_level = obj.get("gate_compute")
    if isinstance(top_level, dict):
        return top_level, None
    language_view = obj.get("language_view")
    if not isinstance(language_view, dict):
        return None, None
    trajectory = language_view.get("trajectory")
    if not isinstance(trajectory, dict):
        return None, None
    nested = trajectory.get("gate_compute")
    if isinstance(nested, dict):
        return nested, _TRAJECTORY_GATE_COMPUTE
    safety_decision = trajectory.get("safety_decision")
    safety_budget = (
        safety_decision.get("gate_compute")
        if isinstance(safety_decision, dict)
        else None
    )
    if isinstance(safety_budget, dict):
        return safety_budget, _SAFETY_GATE_COMPUTE
    return None, None


def _bridge_gate_snn_sidecar(obj):
    """Return the curator-selected gate head and its accepted carrier."""

    for carrier, path in _GATE_SNN_CARRIERS:
        candidate = _value_at_path(obj, path)
        if isinstance(candidate, dict):
            return candidate, carrier
    return None, None


def _value_at_path(value, path):
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _nested_gate_compute_removals(language_view, selected, carrier):
    """Return selected/redundant nested carrier paths to remove."""
    removals = [] if carrier is None else [carrier]
    if carrier is None:
        lower_carriers = (_TRAJECTORY_GATE_COMPUTE, _SAFETY_GATE_COMPUTE)
    elif carrier == _TRAJECTORY_GATE_COMPUTE:
        lower_carriers = (_SAFETY_GATE_COMPUTE,)
    else:
        lower_carriers = ()
    selected_blob = _canonical_record_blob(selected)
    for path in lower_carriers:
        candidate = _value_at_path(language_view, path)
        if isinstance(candidate, dict) and _canonical_record_blob(candidate) == selected_blob:
            removals.append(path)
    return removals


def _nested_gate_snn_removals(language_view, selected, carrier):
    """Return selected/redundant nested gate-head paths to remove."""

    removals = [carrier] if isinstance(carrier, tuple) else []
    if carrier in (_GATE_SNN_ROOT, _GATE_SNN_META):
        lower_carriers = (_TRAJECTORY_GATE_SNN, _SAFETY_GATE_SNN)
    elif carrier == _TRAJECTORY_GATE_SNN:
        lower_carriers = (_SAFETY_GATE_SNN,)
    else:
        lower_carriers = ()
    selected_blob = _canonical_record_blob(selected)
    for path in lower_carriers:
        candidate = _value_at_path(language_view, path)
        if isinstance(candidate, dict) and _canonical_record_blob(candidate) == selected_blob:
            removals.append(path)
    return removals


def _copy_without_path(value, path):
    """Copy dictionaries along ``path`` and remove only its final key."""
    copied = dict(value)
    key = path[0]
    if len(path) == 1:
        copied.pop(key)
    else:
        child = _copy_without_path(copied[key], path[1:])
        if key == "safety_decision" and not child:
            copied.pop(key)
        else:
            copied[key] = child
    return copied


def _copy_without_paths(value, paths):
    copied = value
    for path in paths:
        copied = _copy_without_path(copied, path)
    return copied


def _unselected_root_gate_compute(obj, nested_carrier):
    """Return an ignored malformed root carrier when curation fell through."""
    if nested_carrier is None:
        return None
    if "gate_compute" not in obj:
        return None
    root_value = obj["gate_compute"]
    if isinstance(root_value, dict):
        return None
    return {"root": root_value}


def _same_canonical_dict(candidate, selected):
    if not isinstance(candidate, dict):
        return False
    return _canonical_record_blob(candidate) == _canonical_record_blob(selected)


def _unselected_raster_carriers(obj, selected, carrier):
    """Return non-selected raster evidence that must remain in identity."""
    if carrier == _RASTER_META:
        if "raster" not in obj:
            return None
        return {_RASTER_ROOT: obj["raster"]}
    if carrier != _RASTER_ROOT:
        return None
    meta = obj.get("meta")
    if not isinstance(meta, dict):
        return None
    if "raster" not in meta:
        return None
    nested = meta["raster"]
    if _same_canonical_dict(nested, selected):
        return None
    return {_RASTER_META: nested}


def _malformed_meta_raster_carrier(obj):
    """Return an explicit metadata-only raster that curation would reject."""
    if "language_view" not in obj or "spike_events" not in obj:
        return None
    meta = obj.get("meta")
    if not isinstance(meta, dict) or "raster" not in meta:
        return None
    return {_RASTER_META: meta["raster"]}


def _with_bridge_raster(obj, modeled):
    bridge_raster, raster_carrier = _bridge_raster_sidecar(obj)
    if bridge_raster is None:
        malformed_meta = _malformed_meta_raster_carrier(obj)
        if malformed_meta is not None:
            modeled["raster_unselected"] = malformed_meta
        return modeled
    unselected_raster = _unselected_raster_carriers(
        obj, bridge_raster, raster_carrier
    )
    if unselected_raster is not None:
        modeled["raster_unselected"] = unselected_raster
    modeled["raster"] = bridge_raster
    return modeled


def _with_bridge_gate_compute(obj, modeled):
    bridge_gate_compute, nested_carrier = _bridge_gate_compute_sidecar(obj)
    if bridge_gate_compute is None:
        return modeled
    unselected_root = _unselected_root_gate_compute(obj, nested_carrier)
    if unselected_root is not None:
        modeled["gate_compute_unselected"] = unselected_root
    modeled["gate_compute"] = bridge_gate_compute
    removals = _nested_gate_compute_removals(
        obj["language_view"], bridge_gate_compute, nested_carrier
    )
    if removals:
        modeled["language_view"] = _copy_without_paths(
            obj["language_view"], removals
        )
    return modeled


def _declared_root_meta_gate_snn(obj, carrier):
    """Return one declared root/meta carrier, including malformed values."""

    container = obj if carrier == _GATE_SNN_ROOT else obj.get("meta")
    if not isinstance(container, dict) or "gate_snn" not in container:
        return _NO_GATE_SNN_CARRIER
    return container["gate_snn"]


def _unselected_gate_snn_carriers(obj, selected, carrier):
    """Return non-selected root/meta gate heads omitted from modeled fields."""

    unselected = {}
    for candidate_carrier in (_GATE_SNN_ROOT, _GATE_SNN_META):
        if candidate_carrier == carrier:
            continue
        candidate = _declared_root_meta_gate_snn(obj, candidate_carrier)
        if candidate is _NO_GATE_SNN_CARRIER:
            continue
        if _same_canonical_dict(candidate, selected):
            continue
        unselected[candidate_carrier] = candidate
    return unselected or None


def _with_bridge_gate_snn(obj, modeled):
    """Normalize accepted gate-head carriers into one modeled identity field."""

    gate_snn, carrier = _bridge_gate_snn_sidecar(obj)
    unselected = _unselected_gate_snn_carriers(obj, gate_snn, carrier)
    if unselected is not None:
        modeled["gate_snn_unselected"] = unselected
    if gate_snn is None:
        return modeled
    modeled["gate_snn"] = gate_snn
    language_view = modeled.get("language_view")
    if not isinstance(language_view, dict):
        return modeled
    removals = _nested_gate_snn_removals(language_view, gate_snn, carrier)
    if removals:
        modeled["language_view"] = _copy_without_paths(language_view, removals)
    return modeled


def _with_bridge_sidecars(obj, modeled):
    """Normalize accepted bridge sidecars into the modeled identity fields."""
    normalized = _with_bridge_gate_compute(obj, _with_bridge_raster(obj, modeled))
    return _with_bridge_gate_snn(obj, normalized)


def exact_identity_view(obj):
    """Return the canonical training identity used by exact-hash dedup.

    Wrapper ids are deliberately outside modeled state/action records.
    Preference wrappers keep both modeled sides plus their shared task and
    supervision fields. Canonical ids inside fallback shapes remain exact
    identity; the independent semantic view removes them before cosine.
    """
    if not isinstance(obj, dict):
        # A JSONL line that parses to a scalar/array must hash, not raise.
        return obj
    if "chosen" in obj or "rejected" in obj:
        # Malformed pairs must hash rather than raise. Both side keys remain in
        # the view so a one-sided record stays distinguishable.
        return _preference_identity_view(obj)
    modeled = _with_bridge_sidecars(
        obj, {key: obj[key] for key in _IDENTITY_FIELDS if key in obj}
    )
    if modeled:
        return modeled
    # Shapes this gate does not model must not all hash to an empty key set.
    return obj


def dedup_view(obj):
    """Backward-compatible name for the exact-identity representation."""
    return exact_identity_view(obj)


def _is_semantic_bookkeeping_key(path, key):
    if (
        path in _SEMANTIC_CONTAINER_BOOKKEEPING_PARENTS
        and key in _SEMANTIC_ROOT_BOOKKEEPING_KEYS
    ):
        return True
    if path not in _SEMANTIC_BOOKKEEPING_PARENTS:
        return False
    return key in (_CANONICAL_ID_KEYS | _SEMANTIC_PROMOTION_BOOKKEEPING_KEYS)


def _without_mapping_bookkeeping(value, path):
    cleaned = {}
    for key, child in value.items():
        if _is_semantic_bookkeeping_key(path, key):
            continue
        cleaned[key] = _without_canonical_ids(child, path + (key,))
    return cleaned


def _without_canonical_ids(value, path=()):
    """Copy ``value`` while removing semantic-view bookkeeping.

    Removal is scoped to the record root, modeled state carriers (including a
    bridge's ``language_view.trajectory.state``), and either preference side.
    Identifier-shaped action arguments deeper in a modeled payload therefore
    remain observable to the encoder.
    """
    if isinstance(value, dict):
        return _without_mapping_bookkeeping(value, path)
    if isinstance(value, list):
        return [_without_canonical_ids(child, path) for child in value]
    if isinstance(value, tuple):
        return tuple(_without_canonical_ids(child, path) for child in value)
    return value


def semantic_similarity_view(obj):
    """Return training semantics for the cosine encoder."""
    return _without_canonical_ids(exact_identity_view(obj))


def record_hash(obj):
    """Return the quality gate's compact SHA-256 exact-identity digest."""
    blob = _canonical_record_blob(exact_identity_view(obj))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
