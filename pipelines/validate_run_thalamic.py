#!/usr/bin/env python3
"""Thalamic-trajectory shape checks shared by the run validator's routes."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_thalamic")
    from . import validate_run_spikes as _validate_run_spikes
    from . import validate_run_provenance as _validate_run_provenance
    from . import validate_run_rewards as _validate_run_rewards
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_thalamic"
    )
    import validate_run_spikes as _validate_run_spikes
    import validate_run_provenance as _validate_run_provenance
    import validate_run_rewards as _validate_run_rewards


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


def _thalamic_shape_errors(obj, where):
    """Validate required object fields and optional canonical string fields."""
    # Shape layer: the object-typed fields (incl. meta) are required here.
    # Canonical `id` presence/coverage is a deep-layer concern
    # (check_records / training_audit); at this layer it is only
    # type-checked when present.
    object_errors = [
        error
        for key in THALAMIC_OBJECT_KEYS
        for error in _required_object_field_errors(obj, key, where)
    ]
    string_errors = [
        error
        for key in THALAMIC_STRING_KEYS
        for error in _optional_nonempty_string_errors(obj, key, where)
    ]
    return object_errors + string_errors


def _safety_decision_errors(safety_decision, where):
    """Validate one object-typed safety decision without unhashable crashes."""
    if not isinstance(safety_decision, dict):
        return []
    errs = _validate_run_provenance.typed_enum_errors(
        safety_decision.get("decision"),
        SAFETY_DECISIONS,
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


def _default_provenance_errors(obj, where):
    """Run both provenance layers with the provenance sibling's vocabulary."""
    return _validate_run_provenance.state_provenance_errors(
        obj,
        where,
        _validate_run_provenance.ALLOWED_SIM_OR_REAL,
        _validate_run_provenance.typed_enum_errors,
    ) + _validate_run_provenance.provenance_object_errors(
        obj,
        where,
        _validate_run_provenance.ALLOWED_PROVENANCE_KIND,
        _validate_run_provenance.typed_enum_errors,
    )


def check_thalamic(
    obj,
    where,
    *,
    reward_total_errors=_validate_run_rewards.check_reward_total,
    provenance_errors=None,
    provenance_publish_errors=None,
    spike_stream_errors=None,
):
    """Validate one thalamic trajectory across the shape, reward, provenance,
    meta.round, and spike-stream layers.

    The cross-layer gates default to the sibling implementations; the
    validate_run facade passes its live globals explicitly so vocabulary
    rebinding (mock.patch.object on the facade) keeps flowing through.
    """
    if provenance_errors is None:
        provenance_errors = _default_provenance_errors
    if provenance_publish_errors is None:
        provenance_publish_errors = _validate_run_provenance.check_provenance_publish
    if spike_stream_errors is None:
        spike_stream_errors = _validate_run_spikes.check_spike_stream
    errs = _thalamic_shape_errors(obj, where)
    errs += _safety_decision_errors(obj.get("safety_decision"), where)
    rc = obj.get("reward_components")
    if isinstance(rc, dict):
        errs += reward_total_errors(rc, where)
    # strict provenance and meta checks (including publish-time deep scan)
    errs += provenance_errors(obj, where)
    # Deep publish-time provenance: any nested 'real' fails
    errs += [e for e in provenance_publish_errors(obj, where) if e not in errs]
    errs += check_meta_round(obj, where)
    # Optional trajectory-level spike train: same ordering contract as bridge.
    errs += spike_stream_errors(obj, where)
    return errs


if __package__:
    _expose_package_sibling(__name__)
