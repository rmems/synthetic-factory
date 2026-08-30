#!/usr/bin/env python3
"""Exact and semantic identity projections for the quality gate.

This module is deliberately dependency-free within ``pipelines`` so the
quality-gate CLI can re-export its public compatibility surface without
creating an import cycle.
"""

from __future__ import annotations

import hashlib
import json


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
    # bridge models the paired language view, bridge notes, and raster sidecar
    # (prompts/03-neuromorphic-event-language-bridge.md). Listing all four
    # keeps a bridge record's whole modeled content in the projection rather
    # than only its stream.
    "spike_events",
    "language_view",
    "bridge_notes",
    "raster",
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
    {(), ("language_view", "trajectory")}
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
    }
)

_PREFERENCE_WRAPPER_FIELDS = _IDENTITY_FIELDS + (
    "critique",
    "reward_delta",
    "lesson_category",
)


def canonical_blob(value):
    """Return the stable JSON representation used by identity digests."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _preference_identity_side(value):
    """Return all modeled training fields from one preference side.

    Preference actions and outcomes are labels, not bookkeeping. Keeping only
    ``state`` made distinct preference training units exact-hash collisions.
    Malformed sides retain their complete value so unrelated malformed records
    do not all collapse to the same sentinel.
    """
    if not isinstance(value, dict):
        return value
    modeled = {key: value[key] for key in _IDENTITY_FIELDS if key in value}
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
        return None
    meta = obj.get("meta")
    nested = meta.get("raster") if isinstance(meta, dict) else None
    for candidate in (obj.get("raster"), nested):
        if isinstance(candidate, dict):
            return candidate
    return None


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
    modeled = {key: obj[key] for key in _IDENTITY_FIELDS if key in obj}
    bridge_raster = _bridge_raster_sidecar(obj)
    if bridge_raster is not None:
        modeled["raster"] = bridge_raster
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
    blob = canonical_blob(exact_identity_view(obj))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
