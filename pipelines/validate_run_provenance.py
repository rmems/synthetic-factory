#!/usr/bin/env python3
"""Schema-derived provenance checks shared by the run validator's routes."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_provenance")
    from . import validate_run_spikes as _validate_run_spikes
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_provenance"
    )
    import validate_run_spikes as _validate_run_spikes


ALLOWED_PROVENANCE_KIND = frozenset(
    _validate_run_spikes.THALAMIC_SCHEMA["properties"]["provenance"]["properties"][
        "kind"
    ]["enum"]
)
ALLOWED_SIM_OR_REAL = frozenset(
    _validate_run_spikes.THALAMIC_SCHEMA["properties"]["state"]["properties"][
        "sim_or_real"
    ]["enum"]
)


def typed_enum_errors(value, allowed, message):
    """Return one bounded enum error for any decoded JSON value."""
    if isinstance(value, str) and value in allowed:
        return []
    return [message]


def _contains_real(value):
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized == "real" or normalized.startswith(
        ("real_", "real-", "real ")
    )


def _claimed_value_errors(claimed, where):
    if claimed is None:
        return []
    if isinstance(claimed, str):
        return []
    return [f"{where}: provenance.claimed must be a string or null"]


def state_provenance_errors(
    obj,
    where,
    allowed_sim_or_real=ALLOWED_SIM_OR_REAL,
    enum_errors=typed_enum_errors,
):
    """Validate the state provenance enum without assuming a string value."""
    state = obj.get("state")
    if isinstance(state, dict):
        if "sim_or_real" not in state:
            return []
        value = state.get("sim_or_real")
        # One violation, one error: a 'real' value gets the specific
        # (more actionable) message instead of that message plus the generic
        # enum error, since inflated counts feed training_audit.
        if _contains_real(value):
            return [
                f"{where}: state.sim_or_real must not be 'real' (use 'designed')"
            ]
        return enum_errors(
            value,
            allowed_sim_or_real,
            f"{where}: state.sim_or_real must be one of {sorted(allowed_sim_or_real)}",
        )
    if "state" in obj:
        return [f"{where}: state must be an object"]
    return []


def provenance_object_errors(
    obj,
    where,
    allowed_provenance_kind=ALLOWED_PROVENANCE_KIND,
    enum_errors=typed_enum_errors,
):
    """Validate the provenance object and its schema-derived kind enum."""
    if "provenance" not in obj:
        return []
    provenance = obj.get("provenance")
    if not isinstance(provenance, dict):
        return [f"{where}: provenance must be an object"]

    kind = provenance.get("kind")
    errors = enum_errors(
        kind,
        allowed_provenance_kind,
        f"{where}: provenance.kind must be one of {sorted(allowed_provenance_kind)}",
    )
    if _contains_real(kind):
        errors.append(f"{where}: provenance.kind must not be 'real'")
    return errors + _claimed_value_errors(provenance.get("claimed"), where)


def check_provenance(obj, where):
    """Validate direct state and provenance objects for every trajectory route."""
    return state_provenance_errors(obj, where) + provenance_object_errors(obj, where)


def _field_path(path, key):
    if path:
        return f"{path}.{key}"
    return key


def _provenance_field_errors(key, value, where, path):
    if key == "sim_or_real" and _contains_real(value):
        return [f"{where}: {path} must not be 'real' (use 'designed')"]
    if key != "provenance":
        return []
    if not isinstance(value, dict):
        return []
    if _contains_real(value.get("kind")):
        return [f"{where}: {path}.kind must not be 'real'"]
    return []


def _nested_provenance_errors(node, where, path=""):
    if isinstance(node, dict):
        return _mapping_provenance_errors(node, where, path)
    if isinstance(node, list):
        return _list_provenance_errors(node, where, path)
    return []


def _mapping_provenance_errors(mapping, where, path):
    errors = []
    for key, value in mapping.items():
        field_path = _field_path(path, key)
        errors += _provenance_field_errors(key, value, where, field_path)
        errors += _nested_provenance_errors(value, where, field_path)
    return errors


def _list_provenance_errors(items, where, path):
    errors = []
    for index, item in enumerate(items):
        errors += _nested_provenance_errors(item, where, f"{path}[{index}]")
    return errors


def _deduplicate(errors):
    seen = set()
    unique = []
    for error in errors:
        if error not in seen:
            seen.add(error)
            unique.append(error)
    return unique


def check_provenance_publish(obj, where):
    """Fail closed on nested ``real`` provenance values, preserving error order."""
    return _deduplicate(_nested_provenance_errors(obj, where))


if __package__:
    _expose_package_sibling(__name__)
