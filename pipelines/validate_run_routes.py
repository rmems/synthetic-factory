#!/usr/bin/env python3
"""Shape routing for the run validator: kind dispatch and staged finishers."""

import sys
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_routes")
    from . import validate_run_preference as _validate_run_preference
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_routes"
    )
    import validate_run_preference as _validate_run_preference


STAGING_FINISHED_KINDS = frozenset(
    {"preference", "safety_case", "multi_agent", "episode"}
)
staging_preference_goal_errors = _validate_run_preference.staging_preference_goal_errors


class LineHooks(NamedTuple):
    """Live checkers and vocabularies ``check_line`` reads per call.

    The validate_run facade builds this from its own compatibility names so
    patching check_thalamic, check_episode, THALAMIC_CORE_KEYS, and the
    staging finishers keeps flowing through the router.
    """

    thalamic_core_keys: tuple
    check_thalamic: object
    check_episode: object
    check_safety_case: object
    check_multi_agent: object
    check_spike_order: object
    episode_like: object
    require_reward: object
    check_provenance_publish: object
    hidden_thought_errors: object
    preference_goal_errors: object


class LineCall(NamedTuple):
    """One record plus the live hooks the router consults for that call."""

    obj: object
    where: str
    factory_staging: bool
    hooks: object


def route_thalamic(obj, where, _factory_staging, hooks):
    return hooks.check_thalamic(obj, where)


def _empty_spike_events(events):
    if not isinstance(events, list):
        return True
    return not events


def _language_view_errors(obj, where, hooks):
    view = obj.get("language_view")
    if not isinstance(view, dict):
        return [f"{where}: language_view must be an object"]
    traj = view.get("trajectory")
    if isinstance(traj, dict):
        return hooks.check_thalamic(traj, f"{where}.language_view.trajectory")
    return [f"{where}: language_view.trajectory missing or not an object"]


def route_bridge_pair(obj, where, _factory_staging, hooks):
    events = obj["spike_events"]
    if _empty_spike_events(events):
        errs = [f"{where}: spike_events must be a non-empty array"]
    else:
        errs = hooks.check_spike_order(events, where, enclosing=obj)
    return errs + _language_view_errors(obj, where, hooks)


def route_safety_case(obj, where, factory_staging, hooks):
    return hooks.check_safety_case(obj, where, factory_staging=factory_staging)


def route_multi_agent(obj, where, factory_staging, hooks):
    return hooks.check_multi_agent(obj, where, factory_staging=factory_staging)


def route_episode(obj, where, factory_staging, hooks):
    return hooks.check_episode(
        obj,
        where,
        forbid_hidden_thought=factory_staging,
        enforce_terminal_outcome=factory_staging,
    )


def line_routes(hooks):
    """Return the ordered (required_keys, kind, route) table ``check_line`` walks."""
    return (
        (hooks.thalamic_core_keys, "thalamic", route_thalamic),
        (
            ("chosen", "rejected"),
            "preference",
            _validate_run_preference.route_preference,
        ),
        (("language_view", "spike_events"), "bridge_pair", route_bridge_pair),
        (("case_type",), "safety_case", route_safety_case),
        (("transcript", "agents"), "multi_agent", route_multi_agent),
        (("goal", "steps"), "episode", route_episode),
    )


def finish_agentic(errors, kind, call):
    errors += call.hooks.hidden_thought_errors(call.obj, call.where)
    errors += [
        error
        for error in call.hooks.check_provenance_publish(call.obj, call.where)
        if error not in errors
    ]
    if kind == "preference":
        errors += call.hooks.preference_goal_errors(call.obj, call.where)
    return errors


def route_code_repair(obj, where):
    """Bind operational family checks to the sealed source without execution.

    Admission is imported here, not at module import: ``code_repair._contract``
    loads ``coding_constants``, which historically imported ``validate_run``.
    An eager import would re-enter the facade while ``check_line`` is still
    binding and would also pull the sealed-catalog stack into every CLI
    invoke that never sees a repair record.
    """
    if __package__:
        from .code_repair.admission import sealed_record_findings
    else:
        from code_repair.admission import sealed_record_findings
    return sealed_record_findings(obj, where), "code_repair"


def route_fault_recovery(obj, where):
    """Bind native simulator checks to the sealed producer without execution.

    Admission is imported here, not at module import: the simulator stack
    materializes a replay snapshot. An eager import would pull that stack
    into every CLI invoke that never sees a fault-recovery record.
    """
    if __package__:
        from .curate_identity_simulator import record_findings
    else:
        from curate_identity_simulator import record_findings
    return record_findings(obj, where), "fault_recovery"


def _route_oracle(obj, where, _factory_staging):
    """Bind oracle-grounded envelope checks without re-running any oracle.

    Envelope and status findings are fail-closed here, as are the family
    findings of an accepted-filed record: a fabricated measurement must not
    ride a trusted envelope into the accepted partition. Rejected-filed
    records keep their honestly-reported reasons as evidence and stay owned
    by oracle_validate, which also checks the filing (accepted- vs rejected-).
    """
    if __package__:
        from .oracle_grounded import record as _oracle_record
    else:
        from oracle_grounded import record as _oracle_record
    try:
        layers = _oracle_record.classify(obj)
    except Exception as exc:  # final boundary around one untrusted record
        return [
            f"{where}: record validation raised an internal exception: "
            f"{type(exc).__name__}"
        ]
    errors = [f"{where}: {finding}" for finding in layers["envelope"] + layers["status"]]
    return errors + _oracle_filing_errors(obj, layers, where)


def _oracle_filing_errors(obj, layers, where):
    """Findings that depend on the accepted-/rejected- filing of one record.

    ``accepted-`` files must survive their own family invariants, so the
    recomputed family findings are staging errors there; ``rejected-`` files
    keep those reasons as honestly-reported evidence owned by oracle_validate.
    """
    filename = where.rsplit(":", 1)[0].rsplit("/", 1)[-1]
    expected = None
    if filename.startswith("accepted-"):
        expected = "accepted"
    elif filename.startswith("rejected-"):
        expected = "rejected"
    validation = obj.get("validation")
    declared = validation.get("status") if isinstance(validation, dict) else None
    errors = []
    if expected and declared != expected:
        errors.append(
            f"{where}: record declares verdict {declared!r} but is filed in "
            f"{filename!r}, which is reserved for {expected!r} records"
        )
    if expected == "accepted":
        errors.extend(f"{where}: {finding}" for finding in layers["family"])
    return errors


def _unknown_shape(obj, where):
    return [f"{where}: unrecognized record shape (keys: {sorted(obj)[:8]})"], "unknown"


def _should_finish_agentic(call, kind):
    if not call.factory_staging:
        return False
    return kind in STAGING_FINISHED_KINDS


def _apply_route(call, kind, route):
    errors = route(call.obj, call.where, call.factory_staging, call.hooks)
    if _should_finish_agentic(call, kind):
        return finish_agentic(errors, kind, call), kind
    return errors, kind


def _route_known_shape(call):
    for required_keys, kind, route in line_routes(call.hooks):
        if all(key in call.obj for key in required_keys):
            return _apply_route(call, kind, route)
    return _unknown_shape(call.obj, call.where)


def _route_parity(obj, where, _factory_staging):
    """Bind the shared parity envelope check without re-running any oracle.

    The oracle_grounded parity contract is imported lazily for the same reason
    as ``route_code_repair``: an eager import would pull the sealed-catalog
    stack into every CLI invoke that never sees a parity record.
    """
    if __package__:
        from .oracle_grounded import parity_contract
    else:
        from oracle_grounded import parity_contract
    return parity_contract.check_envelope(obj, where)


def _parity_record_kinds():
    if __package__:
        from .oracle_grounded import parity_contract
    else:
        from oracle_grounded import parity_contract
    return parity_contract.RECORD_KINDS


def _route_family(obj, where):
    """Route named procedural families ahead of the shape table."""
    family = obj.get("family")
    if family == "python-function-repair":
        return route_code_repair(obj, where)
    if family == "neuromorphic-fault-recovery":
        return route_fault_recovery(obj, where)
    return None


def check_line(obj, where, factory_staging=False, hooks=None):
    """Route an object to the right checker based on its shape."""
    if hooks is None:
        raise TypeError("check_line requires LineHooks from the validate_run facade")
    if not isinstance(obj, dict):
        return [f"{where}: record must be a JSON object"], "unknown"
    # Self-declared families route ahead of the shape table, in the same order
    # as record_kind.classify_kind: a record that names its own family can
    # never be confused with a trajectory that happens to share a key name.
    declared_kind = obj.get("record_kind")
    if isinstance(declared_kind, str) and declared_kind in _parity_record_kinds():
        return _route_parity(obj, where, factory_staging), declared_kind
    routed = _route_family(obj, where)
    if routed is not None:
        return routed
    oracle_shape = obj.get("schema") == "oracle-grounded/v1" or all(
        key in obj for key in ("oracle", "result", "proposal_hash")
    )
    if oracle_shape:
        return _route_oracle(obj, where, factory_staging), "oracle"
    return _route_known_shape(LineCall(obj, where, factory_staging, hooks))


if __package__:
    _expose_package_sibling(__name__)
