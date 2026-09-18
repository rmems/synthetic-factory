#!/usr/bin/env python3
"""Validate a dated factory run under outputs/raw/<date>/.

Checks every .jsonl file: each line must parse as JSON, and any embedded
ThalamicTrajectory (top-level, chosen/rejected pair, or language_view.trajectory)
must satisfy schemas/thalamic-trajectory.schema.json's constraints. Coding
episodes are checked against their own shape. Prints totals JSON to stdout
and errors to stderr; exits nonzero if any file has errors. Does not write
manifest.json unless --write is passed.

Usage: python3 pipelines/validate_run.py [--write] <run_dir>
"""

import argparse
import json
import math
import posixpath
import re
import sys
from pathlib import Path

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import
    _assert_direct_sibling("validate_run")
    from . import validate_run_spikes as _validate_run_spikes
    from . import validate_run_provenance as _validate_run_provenance
    from . import validate_run_rewards as _validate_run_rewards
    from . import validate_run_reward_total as _validate_run_reward_total
    from . import validate_run_thalamic as _validate_run_thalamic
    from . import validate_run_safety as _validate_run_safety
    from . import validate_run_episode as _validate_run_episode
    from . import validate_run_multi_agent as _validate_run_multi_agent
    from . import validate_run_preference as _validate_run_preference
    from .validate_run_input import parse_exact_json_record as _parse_exact_json_record
else:
    import validate_run_spikes as _validate_run_spikes
    import validate_run_provenance as _validate_run_provenance
    import validate_run_rewards as _validate_run_rewards
    import validate_run_reward_total as _validate_run_reward_total
    import validate_run_thalamic as _validate_run_thalamic
    import validate_run_safety as _validate_run_safety
    import validate_run_episode as _validate_run_episode
    import validate_run_multi_agent as _validate_run_multi_agent
    import validate_run_preference as _validate_run_preference
    from validate_run_input import parse_exact_json_record as _parse_exact_json_record

# Historical public compatibility surface. Explicit binding keeps these names
# importable without asking static analyzers to treat unused imports as use.
BRIDGE_SPIKE_EVENT_KEYS = _validate_run_spikes.BRIDGE_SPIKE_EVENT_KEYS
REPO = _validate_run_spikes.REPO
SCHEMA_PATH = _validate_run_spikes.SCHEMA_PATH
SPIKE_CLOCK_DOMAIN_KEYS = _validate_run_spikes.SPIKE_CLOCK_DOMAIN_KEYS
SPIKE_CLOCK_DOMAIN_MISMATCH = _validate_run_spikes.SPIKE_CLOCK_DOMAIN_MISMATCH
SPIKE_EVENT_NUMBER_KEYS = _validate_run_spikes.SPIKE_EVENT_NUMBER_KEYS
SPIKE_EVENT_STRING_KEYS = _validate_run_spikes.SPIKE_EVENT_STRING_KEYS
SPIKE_ORDER_MISMATCH = _validate_run_spikes.SPIKE_ORDER_MISMATCH
SPIKE_TIME_KEYS = _validate_run_spikes.SPIKE_TIME_KEYS
SPIKE_TIME_KEY_MISMATCH = _validate_run_spikes.SPIKE_TIME_KEY_MISMATCH
THALAMIC_SCHEMA = _validate_run_spikes.THALAMIC_SCHEMA
_check_spike_order = _validate_run_spikes.check_spike_order
_check_spike_stream = _validate_run_spikes.check_spike_stream
_declared_clock_domains = _validate_run_spikes.declared_clock_domains
_event_time = _validate_run_spikes.event_time
_is_number = _validate_run_spikes.is_number
_typed_enum_errors = _validate_run_provenance.typed_enum_errors
check_provenance_publish = _validate_run_provenance.check_provenance_publish

# The spike-train surface lived here before it split into validate_run_spikes;
# ``__all__`` declares the names this module still re-exports so existing
# ``validate_run.X`` consumers (the CLI tests among them) resolve unchanged.
__all__ = [
    "ALLOWED_PROVENANCE_KIND",
    "ALLOWED_SIM_OR_REAL",
    "BRIDGE_SPIKE_EVENT_KEYS",
    "HIDDEN_THOUGHT_KEYS",
    "OBSERVABLE_BASIS_RE",
    "Path",
    "REPO",
    "REWARD_ARITHMETIC_MARKERS",
    "REWARD_NON_COMPONENT_KEYS",
    "REWARD_TOL",
    "REWARD_UNWEIGHTED_MISMATCH",
    "REWARD_WEIGHTED_MISMATCH",
    "SAFETY_CASE_DECISIONS",
    "SAFETY_CASE_SUCCESS",
    "SAFETY_CASE_TYPES",
    "SAFETY_DECISIONS",
    "SCHEMA_PATH",
    "SPIKE_CLOCK_DOMAIN_KEYS",
    "SPIKE_CLOCK_DOMAIN_MISMATCH",
    "SPIKE_EVENT_NUMBER_KEYS",
    "SPIKE_EVENT_STRING_KEYS",
    "SPIKE_ORDER_MISMATCH",
    "SPIKE_TIME_KEYS",
    "SPIKE_TIME_KEY_MISMATCH",
    "THALAMIC_CORE_KEYS",
    "THALAMIC_OBJECT_KEYS",
    "THALAMIC_REQUIRED",
    "THALAMIC_SCHEMA",
    "THALAMIC_STRING_KEYS",
    "argparse",
    "check_episode",
    "check_line",
    "check_meta_round",
    "check_multi_agent",
    "check_provenance",
    "check_provenance_publish",
    "check_reward_total",
    "check_safety_case",
    "check_spike_order",
    "check_spike_stream",
    "check_thalamic",
    "declared_clock_domains",
    "event_time",
    "episode_like",
    "is_number",
    "json",
    "main",
    "math",
    "parse_args",
    "posixpath",
    "re",
    "reject_json_constant",
    "sys",
    "terminal_outcome_agrees",
]

# Thalamic shape vocabulary lives in validate_run_thalamic; the facade rebinds
# it here so routing, compose_trajectory_goals, and the CLI tests keep
# resolving validate_run.THALAMIC_* unchanged.
THALAMIC_REQUIRED = _validate_run_thalamic.THALAMIC_REQUIRED
THALAMIC_OBJECT_KEYS = _validate_run_thalamic.THALAMIC_OBJECT_KEYS
THALAMIC_STRING_KEYS = _validate_run_thalamic.THALAMIC_STRING_KEYS
THALAMIC_CORE_KEYS = _validate_run_thalamic.THALAMIC_CORE_KEYS
SAFETY_DECISIONS = _validate_run_thalamic.SAFETY_DECISIONS

# provenance.kind allows 'unknown'; state.sim_or_real does not. Both
# vocabularies are the schema's own enums.
ALLOWED_PROVENANCE_KIND = _validate_run_provenance.ALLOWED_PROVENANCE_KIND
ALLOWED_SIM_OR_REAL = _validate_run_provenance.ALLOWED_SIM_OR_REAL
# Reward arithmetic lives in validate_run_rewards; the facade rebinds its
# vocabulary here so check_records and the CLI tests keep resolving
# validate_run.REWARD_* (including mock.patch.object targets) unchanged.
REWARD_NON_COMPONENT_KEYS = _validate_run_rewards.REWARD_NON_COMPONENT_KEYS
REWARD_TOL = _validate_run_rewards.REWARD_TOL


def reject_json_constant(value):
    """Reject Python's non-standard NaN and Infinity JSON extensions."""
    raise ValueError(f"non-standard JSON numeric constant {value}")


def is_number(value):
    """Compatibility facade for the shared finite-number predicate."""
    return _is_number(value)


def event_time(event):
    """Compatibility facade for schema-derived spike timestamps."""
    return _event_time(event)


def declared_clock_domains(events, enclosing=None):
    """Compatibility facade for spike clock-domain discovery."""
    return _declared_clock_domains(events, enclosing)


def check_spike_order(
    events,
    where,
    require_keys=BRIDGE_SPIKE_EVENT_KEYS,
    *,
    enclosing=None,
):
    """Compatibility facade for strict spike-stream validation."""
    return _check_spike_order(
        events,
        where,
        require_keys=require_keys,
        enclosing=enclosing,
    )


def check_spike_stream(obj, where):
    """Compatibility facade for optional trajectory spike streams."""
    return _check_spike_stream(obj, where)


_component_numeric = _validate_run_rewards.component_numeric
REWARD_WEIGHTED_MISMATCH = _validate_run_rewards.REWARD_WEIGHTED_MISMATCH
REWARD_UNWEIGHTED_MISMATCH = _validate_run_rewards.REWARD_UNWEIGHTED_MISMATCH
REWARD_ARITHMETIC_MARKERS = _validate_run_rewards.REWARD_ARITHMETIC_MARKERS


def check_reward_total(rc, where):
    """Compatibility facade for reward arithmetic (see validate_run_reward_total).

    The tolerance and bookkeeping vocabulary are this module's live bindings,
    so rebinding REWARD_TOL or REWARD_NON_COMPONENT_KEYS here keeps flowing
    through exactly as when the check lived inline.
    """
    settings = _validate_run_rewards.RewardSettings(REWARD_TOL, REWARD_NON_COMPONENT_KEYS)
    return _validate_run_reward_total.check_reward_total(rc, where, settings)


def _state_provenance_errors(obj, where):
    """Validate state provenance using this facade's live vocabulary seam."""
    return _validate_run_provenance.state_provenance_errors(
        obj,
        where,
        ALLOWED_SIM_OR_REAL,
        _typed_enum_errors,
    )


def _provenance_object_errors(obj, where):
    """Validate provenance using this facade's live vocabulary seam."""
    return _validate_run_provenance.provenance_object_errors(
        obj,
        where,
        ALLOWED_PROVENANCE_KIND,
        _typed_enum_errors,
    )


def check_provenance(obj, where):
    """Validate direct state and provenance objects for every trajectory route."""
    return _state_provenance_errors(obj, where) + _provenance_object_errors(obj, where)


check_meta_round = _validate_run_thalamic.check_meta_round


def check_thalamic(obj, where):
    """Compatibility facade for thalamic validation (see validate_run_thalamic).

    Provenance runs through this module's live gates so vocabulary
    rebinding (mock.patch.object on this module) keeps flowing through,
    exactly as when the whole check lived inline.
    """
    hooks = _validate_run_thalamic.ThalamicHooks(
        SAFETY_DECISIONS,
        check_reward_total,
        THALAMIC_OBJECT_KEYS,
        THALAMIC_STRING_KEYS,
        check_meta_round,
        check_spike_stream,
    )
    errs = _validate_run_thalamic.thalamic_core_errors(obj, where, hooks)
    errs += check_provenance(obj, where)
    # Deep publish-time provenance: any nested 'real' fails
    errs += [e for e in check_provenance_publish(obj, where) if e not in errs]
    errs += _validate_run_thalamic.thalamic_tail_errors(obj, where, hooks)
    return errs


SAFETY_CASE_TYPES = _validate_run_safety.SAFETY_CASE_TYPES
SAFETY_CASE_DECISIONS = _validate_run_safety.SAFETY_CASE_DECISIONS
SAFETY_CASE_SUCCESS = _validate_run_safety.SAFETY_CASE_SUCCESS
_nonempty_text_field_errors = _validate_run_safety.nonempty_text_field_errors
_require_reward = _validate_run_rewards.require_reward
terminal_outcome_agrees = _validate_run_rewards.terminal_outcome_agrees

# Episode, tool-turn and hidden-reasoning rules live in validate_run_episode;
# multi-agent coordination records live in validate_run_multi_agent; the
# preference-goal agreement rules live in validate_run_preference. The
# facade rebinds those surfaces here so coding_constants, training_audit,
# check_records, round_txn, and the CLI tests keep resolving the historical
# validate_run names unchanged.
HIDDEN_THOUGHT_KEYS = _validate_run_episode.HIDDEN_THOUGHT_KEYS
OBSERVABLE_BASIS_RE = _validate_run_episode.OBSERVABLE_BASIS_RE
episode_like = _validate_run_episode.episode_like
# Compatibility alias for callers of the pre-split validator surface.
_episode_like = episode_like
_hidden_thought_paths = _validate_run_episode.hidden_thought_paths
_staging_hidden_thought_errors = _validate_run_episode.staging_hidden_thought_errors
_staging_tool_turn_errors = _validate_run_episode.staging_tool_turn_errors
check_episode = _validate_run_episode.check_episode
check_multi_agent = _validate_run_multi_agent.check_multi_agent
_normalized_goal = _validate_run_preference.normalized_goal
_preference_side_context_anchors = _validate_run_preference.preference_side_context_anchors
_staging_preference_goal_errors = _validate_run_preference.staging_preference_goal_errors


def check_safety_case(obj, where, factory_staging=False):
    """Safety-case rules live in validate_run_safety; the episode/reward tail stays here.

    Vocabularies are this module's live SAFETY_CASE_* bindings, so
    rebinding those compatibility names keeps flowing through exactly as
    when the rules lived inline.
    """
    vocab = _validate_run_safety.SafetyCaseVocab(
        SAFETY_CASE_TYPES, SAFETY_CASE_DECISIONS, SAFETY_CASE_SUCCESS
    )
    errs = _validate_run_safety.safety_case_core_errors(
        obj, where, factory_staging, vocab
    )
    if "steps" in obj:
        errs += check_episode(
            obj, where, require_goal=False, forbid_hidden_thought=factory_staging
        )
    else:
        errs += _require_reward(obj, where)
    return errs


def _route_thalamic(obj, where, _factory_staging):
    return check_thalamic(obj, where)


def _preference_side_errors(side, label, episode_pref, episode_kwargs):
    """Validate one preference side as an episode or as a ThalamicTrajectory."""
    if not isinstance(side, dict):
        return [f"{label} must be an object"]
    if episode_pref:
        return check_episode(side, label, **episode_kwargs)
    return check_thalamic(side, label)


def _preference_episode_wrapper_errors(obj, where, chosen, factory_staging):
    """Wrapper-level invariants that only apply to episode preferences."""
    errs = []
    if "goal" not in obj and not (isinstance(chosen, dict) and "goal" in chosen):
        errs.append(f"{where}: preference episode needs a shared or chosen goal")
    errs += _require_reward(obj, where)
    reward = obj.get("reward")
    if (
        factory_staging
        and isinstance(reward, dict)
        and isinstance(reward.get("success"), bool)
        and reward["success"] is not True
    ):
        errs.append(f"{where}: preference wrapper reward.success must be true")
    return errs


def _route_preference(obj, where, factory_staging):
    errs = []
    chosen = obj.get("chosen")
    rejected = obj.get("rejected")
    episode_pref = episode_like(chosen) or episode_like(rejected)
    episode_kwargs = {
        "require_goal": "goal" not in obj,
        "forbid_hidden_thought": factory_staging,
    }
    errs += _preference_side_errors(chosen, f"{where}.chosen", episode_pref, episode_kwargs)
    errs += _preference_side_errors(rejected, f"{where}.rejected", episode_pref, episode_kwargs)
    if episode_pref:
        errs += _preference_episode_wrapper_errors(obj, where, chosen, factory_staging)
    if not isinstance(obj.get("critique"), str) or not obj["critique"].strip():
        errs.append(f"{where}: preference record needs a non-empty critique")
    return errs


def _route_bridge_pair(obj, where, _factory_staging):
    errs = []
    events = obj["spike_events"]
    if not isinstance(events, list) or not events:
        errs.append(f"{where}: spike_events must be a non-empty array")
    else:
        errs += check_spike_order(events, where, enclosing=obj)
    view = obj.get("language_view")
    if not isinstance(view, dict):
        errs.append(f"{where}: language_view must be an object")
    else:
        traj = view.get("trajectory")
        if isinstance(traj, dict):
            errs += check_thalamic(traj, f"{where}.language_view.trajectory")
        else:
            errs.append(f"{where}: language_view.trajectory missing or not an object")
    return errs


def _route_safety_case(obj, where, factory_staging):
    return check_safety_case(obj, where, factory_staging=factory_staging)


def _route_multi_agent(obj, where, factory_staging):
    return check_multi_agent(obj, where, factory_staging=factory_staging)


def _route_episode(obj, where, factory_staging):
    return check_episode(
        obj,
        where,
        forbid_hidden_thought=factory_staging,
        enforce_terminal_outcome=factory_staging,
    )


# Route on the object-typed trajectory fields so legacy v1 records
# (no canonical `id` yet) still reach the thalamic checker and have their
# state / reward / provenance / meta.round invariants enforced instead of
# being skipped as an unrecognized shape. Canonical `id` coverage is owned
# by the deep layer (check_records / training_audit); this layer only
# type-checks an `id` that is present. A record matches a route when every
# listed key is present; precedence is positional, so thalamic outranks
# preference, which outranks bridge pairs, safety cases, multi-agent
# transcripts, and episodes.
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


def _line_routes():
    """Return the ordered (required_keys, kind, route) table ``check_line`` walks."""
    return (
        (THALAMIC_CORE_KEYS, "thalamic", _route_thalamic),
        (("chosen", "rejected"), "preference", _route_preference),
        (("language_view", "spike_events"), "bridge_pair", _route_bridge_pair),
        (("case_type",), "safety_case", _route_safety_case),
        (("transcript", "agents"), "multi_agent", _route_multi_agent),
        (("goal", "steps"), "episode", _route_episode),
        (("oracle", "result", "proposal_hash"), "oracle", _route_oracle),
    )


_LINE_ROUTES = _line_routes()

# Kinds whose factory-staging pass also runs the shared agentic finishers.
_STAGING_FINISHED_KINDS = frozenset({"preference", "safety_case", "multi_agent", "episode"})


def _finish_agentic(errors, obj, where, kind):
    errors += _staging_hidden_thought_errors(obj, where)
    errors += [
        error for error in check_provenance_publish(obj, where) if error not in errors
    ]
    if kind == "preference":
        errors += _staging_preference_goal_errors(obj, where)
    return errors


def _route_code_repair(obj, where):
    """Bind operational family checks to the sealed source without execution."""
    if __package__:
        from .code_repair.admission import sealed_record_findings
    else:
        from code_repair.admission import sealed_record_findings
    return sealed_record_findings(obj, where), "code_repair"


def check_line(obj, where, factory_staging=False):
    """Route an object to the right checker based on its shape."""
    if not isinstance(obj, dict):
        return [f"{where}: record must be a JSON object"], "unknown"
    if obj.get("family") == "python-function-repair":
        return _route_code_repair(obj, where)
    for required_keys, kind, route in _LINE_ROUTES:
        if not all(k in obj for k in required_keys):
            continue
        errors = route(obj, where, factory_staging)
        if factory_staging and kind in _STAGING_FINISHED_KINDS:
            errors = _finish_agentic(errors, obj, where, kind)
        return errors, kind
    return [f"{where}: unrecognized record shape (keys: {sorted(obj)[:8]})"], "unknown"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a dated factory run under outputs/raw/<date>/.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write manifest.json into run_dir (default: print totals only)",
    )
    parser.add_argument("run_dir", help="run directory containing .jsonl files")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    manifest = {"run_dir": str(run_dir), "files": [], "totals": {}, "errors": []}
    kind_totals = {}

    for path in sorted(run_dir.rglob("*.jsonl")):
        rel = path.relative_to(run_dir)
        entry = {"file": str(rel), "records": 0, "kinds": {}, "errors": []}
        try:
            # Decode the physical bytes without universal-newline translation.
            # JSONL uses literal LF delimiters; a bare CR is JSON whitespace
            # inside one physical record, not a second record boundary.
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            entry["errors"].append(f"{rel}: invalid UTF-8: {exc}")
            manifest["files"].append(entry)
            manifest["errors"].extend(entry["errors"])
            continue
        # JSONL is delimited by literal LF bytes.  ``str.splitlines()`` also
        # splits at U+2028/U+2029, which are valid characters inside a JSON
        # string and would turn one valid record into several invalid lines.
        for lineno, line in enumerate(text.split("\n"), 1):
            if not line.strip():
                continue
            where = f"{rel}:{lineno}"
            obj, input_error = _parse_exact_json_record(line)
            if input_error is not None:
                entry["errors"].append(f"{where}: {input_error}")
                continue
            errs, kind = check_line(obj, where)
            entry["records"] += 1
            entry["kinds"][kind] = entry["kinds"].get(kind, 0) + 1
            kind_totals[kind] = kind_totals.get(kind, 0) + 1
            entry["errors"].extend(errs)
        manifest["files"].append(entry)
        manifest["errors"].extend(entry["errors"])

    manifest["totals"] = {
        "files": len(manifest["files"]),
        "records": sum(f["records"] for f in manifest["files"]),
        "by_kind": kind_totals,
        "error_count": len(manifest["errors"]),
    }
    if args.write:
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(json.dumps(manifest["totals"], indent=2))
    for err in manifest["errors"]:
        print("ERROR:", err, file=sys.stderr)
    sys.exit(1 if manifest["errors"] else 0)


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    main()
