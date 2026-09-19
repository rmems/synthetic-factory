#!/usr/bin/env python3
"""Validate a dated factory run under outputs/raw/<date>/.

This is the stable compatibility facade. Cohesive spike, provenance, reward,
thalamic, safety, episode, routing, and CLI stages live in the
``validate_run_*`` modules; the adapters here retain historical signatures
and resolve patch seams per call.

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
    from . import validate_run_routes as _validate_run_routes
    from . import validate_run_cli as _validate_run_cli
    from .validate_run_input import parse_exact_json_record as _parse_exact_json_record
    from .oracle_grounded import parity_contract
    from .validate_run_input import reject_json_constant as _reject_json_constant
else:
    import validate_run_spikes as _validate_run_spikes
    import validate_run_provenance as _validate_run_provenance
    import validate_run_rewards as _validate_run_rewards
    import validate_run_reward_total as _validate_run_reward_total
    import validate_run_thalamic as _validate_run_thalamic
    import validate_run_safety as _validate_run_safety
    import validate_run_episode as _validate_run_episode
    import validate_run_multi_agent as _validate_run_multi_agent
    import validate_run_routes as _validate_run_routes
    import validate_run_cli as _validate_run_cli
    from validate_run_input import parse_exact_json_record as _parse_exact_json_record
    from oracle_grounded import parity_contract
    from validate_run_input import reject_json_constant as _reject_json_constant

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

# Preserve the oracle staging surface after extracting shape routing.
_route_oracle = _validate_run_routes._route_oracle
_oracle_filing_errors = _validate_run_routes._oracle_filing_errors

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
    "check_parity_envelope",
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
OBSERVABLE_BASIS_RE = _validate_run_episode.OBSERVABLE_BASIS_RE
HIDDEN_THOUGHT_KEYS = _validate_run_episode.HIDDEN_THOUGHT_KEYS


def reject_json_constant(value):
    """Reject Python's non-standard NaN and Infinity JSON extensions."""
    return _reject_json_constant(value)


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
_require_reward = _validate_run_rewards.require_reward
terminal_outcome_agrees = _validate_run_rewards.terminal_outcome_agrees
_nonempty_text_field_errors = _validate_run_safety.nonempty_text_field_errors


def _episode_hooks():
    return _validate_run_episode.EpisodeHooks(
        HIDDEN_THOUGHT_KEYS,
        OBSERVABLE_BASIS_RE,
        _require_reward,
        _nonempty_text_field_errors,
        terminal_outcome_agrees,
        THALAMIC_CORE_KEYS,
    )


def episode_like(obj):
    """True when an object is a coding/agent episode rather than Thalamic."""
    return _validate_run_episode.episode_like(obj, THALAMIC_CORE_KEYS)


# Compatibility alias for callers of the pre-split validator surface.
_episode_like = episode_like


def check_episode(obj, where, *flags, **overrides):
    """Adapt legacy positional/keyword flags to the episode option contract."""
    options = _validate_run_episode.EpisodeOptions(*flags, **overrides)
    return _validate_run_episode.check_episode(
        obj,
        where,
        options=options,
        hooks=_episode_hooks(),
    )


def check_multi_agent(obj, where, factory_staging=False):
    """Compatibility facade for multi-agent validation."""
    return _validate_run_multi_agent.check_multi_agent(
        obj, where, factory_staging=factory_staging, hooks=_episode_hooks()
    )


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


def check_parity_envelope(obj, where):
    """Shape layer for the oracle-grounded parity families.

    Only the shared envelope is enforced here, the same way this layer only
    type-checks a thalamic record. Re-deriving parity metrics and re-executing
    NIR runtimes is the deep layer's job (pipelines/check_records.py), because
    it is far too expensive to do once per line of a whole run directory.
    """
    return parity_contract.check_envelope(obj, where)


def _staging_hidden_thought_errors(obj, where):
    return _validate_run_episode.staging_hidden_thought_errors(
        obj, where, keys=HIDDEN_THOUGHT_KEYS
    )


def _line_hooks():
    return _validate_run_routes.LineHooks(
        THALAMIC_CORE_KEYS,
        check_thalamic,
        check_episode,
        check_safety_case,
        check_multi_agent,
        check_spike_order,
        episode_like,
        _require_reward,
        check_provenance_publish,
        _staging_hidden_thought_errors,
        _validate_run_routes.staging_preference_goal_errors,
    )


def check_line(obj, where, factory_staging=False):
    """Route an object to the right checker based on its shape."""
    return _validate_run_routes.check_line(
        obj, where, factory_staging=factory_staging, hooks=_line_hooks()
    )


parse_args = _validate_run_cli.parse_args


def main(argv=None):
    return _validate_run_cli.main(
        argv,
        check_line=check_line,
        parse_record=_parse_exact_json_record,
    )


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    main()
