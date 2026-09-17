#!/usr/bin/env python3
"""Thalamic-trajectory shape checks shared by the run validator's routes."""

import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_thalamic")
    from . import validate_run_spikes as _validate_run_spikes
    from . import validate_run_provenance as _validate_run_provenance
    from . import validate_run_reward_total as _validate_run_reward_total
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_thalamic"
    )
    import validate_run_spikes as _validate_run_spikes
    import validate_run_provenance as _validate_run_provenance
    import validate_run_reward_total as _validate_run_reward_total


THALAMIC_SCHEMA = _validate_run_spikes.THALAMIC_SCHEMA
THALAMIC_REQUIRED = tuple(THALAMIC_SCHEMA["required"])
# Type-check required keys against the schema's own declared types: the six
# trajectory fields (+ meta) are objects, but canonical `id` is a string.
THALAMIC_OBJECT_KEYS = tuple(
    key for key in THALAMIC_REQUIRED
    if THALAMIC_SCHEMA["properties"].get(key, {}).get("type") == "object"
)
THALAMIC_STRING_KEYS = tuple(
    key for key in THALAMIC_REQUIRED
    if THALAMIC_SCHEMA["properties"].get(key, {}).get("type") == "string"
)
# The six trajectory fields identify a thalamic record for routing; `meta`
# and `id`, though required, are exactly what legacy records are missing,
# so routing on them would hide every other invariant behind an
# "unrecognized shape" error.
THALAMIC_CORE_KEYS = tuple(
    key for key in THALAMIC_OBJECT_KEYS if key != "meta"
)
SAFETY_DECISIONS = frozenset(
    THALAMIC_SCHEMA["properties"]["safety_decision"]["properties"]
    ["decision"]["enum"]
)


class ThalamicHooks(NamedTuple):
    """The vocabularies and checkers one thalamic validation runs under.

    The validate_run facade builds this from its own live bindings, so
    patching any of the facade-level compatibility names keeps flowing
    through exactly as when the whole check lived inline. Siblings default
    to this module's bindings via :func:`default_hooks`.
    """

    safety_decisions: frozenset
    reward_checker: object
    object_keys: tuple
    string_keys: tuple
    meta_round_checker: object
    spike_checker: object


def default_hooks():
    """This module's own hooks, read at call time so patches here flow too."""
    return ThalamicHooks(
        SAFETY_DECISIONS,
        _validate_run_reward_total.check_reward_total,
        THALAMIC_OBJECT_KEYS,
        THALAMIC_STRING_KEYS,
        check_meta_round,
        _validate_run_spikes.check_spike_stream,
    )


def _required_object_field_errors(obj, key, where):
    if key not in obj:
        return [f"{where}: missing required key '{key}'"]
    if not isinstance(obj[key], dict):
        return [f"{where}: '{key}' must be an object"]
    return []


def _optional_nonempty_string_errors(obj, key, where):
    if key not in obj:
        return []
    value = obj[key]
    if not isinstance(value, str) or not value.strip():
        return [f"{where}: '{key}' must be a non-empty string"]
    return []


def _thalamic_shape_errors(obj, where, hooks):
    """Validate required object fields and optional canonical string fields."""
    object_keys, string_keys = hooks.object_keys, hooks.string_keys
    # Shape layer: the object-typed fields (incl. meta) are required here.
    # Canonical `id` presence/coverage is a deep-layer concern
    # (check_records / training_audit); at this layer it is only
    # type-checked when present.
    object_errors = [
        error
        for key in object_keys
        for error in _required_object_field_errors(obj, key, where)
    ]
    string_errors = [
        error
        for key in string_keys
        for error in _optional_nonempty_string_errors(obj, key, where)
    ]
    return object_errors + string_errors


def _safety_decision_errors(safety_decision, where, allowed_decisions=None):
    """Validate one object-typed safety decision without unhashable crashes.

    ``allowed_decisions`` defaults to this module's SAFETY_DECISIONS; the
    validate_run facade passes its own live binding so rebinding the
    facade-level compatibility name keeps affecting validation.
    """
    if not isinstance(safety_decision, dict):
        return []
    decisions = SAFETY_DECISIONS if allowed_decisions is None else allowed_decisions
    errs = _validate_run_provenance.typed_enum_errors(
        safety_decision.get("decision"),
        decisions,
        f"{where}: safety_decision.decision must be ACCEPT|MODIFY|REJECT",
    )
    rationale = safety_decision.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        errs.append(
            f"{where}: safety_decision.rationale must be a non-empty string"
        )
    return errs


def check_meta_round(obj, where):
    """Require meta.round presence and integer >=1.

    A missing or non-object `meta` is already reported by the required-key
    loop in check_thalamic, so this returns quietly in that case rather than
    emitting a second error for the same violation.
    """
    errs = []
    meta = obj.get("meta")
    if not isinstance(meta, dict):
        return errs
    if "round" not in meta:
        errs.append(f"{where}: meta.round is required")
        return errs
    rnd = meta.get("round")
    # bool is subclass of int, exclude
    if isinstance(rnd, bool) or not isinstance(rnd, int):
        errs.append(f"{where}: meta.round must be an integer")
        return errs
    if rnd < 1:
        errs.append(f"{where}: meta.round must be >= 1")
    return errs


def thalamic_core_errors(obj, where, hooks=None):
    """Validate the thalamic-owned core layers: shape, safety decision, and
    reward arithmetic. Provenance and the meta/spike tail stay with the
    caller so layer order and vocabulary rebinding match the inline gate.

    ``hooks`` defaults to :func:`default_hooks`; the validate_run facade
    passes its live bindings (``check_reward_total`` included) so patching
    the facade-level compatibility names keeps flowing through.
    """
    hooks = default_hooks() if hooks is None else hooks
    errs = _thalamic_shape_errors(obj, where, hooks)
    errs += _safety_decision_errors(
        obj.get("safety_decision"), where, hooks.safety_decisions
    )
    rc = obj.get("reward_components")
    if isinstance(rc, dict):
        errs += hooks.reward_checker(rc, where)
    return errs


def thalamic_tail_errors(obj, where, hooks=None):
    """Validate meta.round and the spike stream after the provenance layers.

    ``hooks`` defaults to :func:`default_hooks`; the validate_run facade
    passes its own live check_meta_round and check_spike_stream so rebinding
    either facade-level compatibility name keeps affecting validation.
    """
    hooks = default_hooks() if hooks is None else hooks
    errs = hooks.meta_round_checker(obj, where)
    # Optional trajectory-level spike train: same ordering contract as bridge.
    errs += hooks.spike_checker(obj, where)
    return errs


if __package__:
    _expose_package_sibling(__name__)
