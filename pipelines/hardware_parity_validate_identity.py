#!/usr/bin/env python3
"""Is this record the catalog's record?

Input fixture, catalog scenario, naming, and provenance stamps. A record that
passes here is talking about a scenario this repository actually defines, with
the identity the generator would have given it.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_identity")
    from .neuro_oracle import (  # noqa: E402
        PHYSICAL_TARGETS,
        stimulus_fixture,
    )
    from .hardware_parity_terms import (  # noqa: E402
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        SCHEMA_VERSION,
        VALIDATOR,
        contract,
    )
    from .hardware_parity_catalog import (  # noqa: E402
        _SCENARIO_SPEC_BY_ID,
        build_scenario,
    )
    from .hardware_parity_provenance import _catalog_provenance_stamps  # noqa: E402
    from .oracle_grounded.parity_history import reviewed_catalog_stamps
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_identity"
    )
    from neuro_oracle import (  # noqa: E402
        PHYSICAL_TARGETS,
        stimulus_fixture,
    )
    from hardware_parity_terms import (  # noqa: E402
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        SCHEMA_VERSION,
        VALIDATOR,
        contract,
    )
    from hardware_parity_catalog import (  # noqa: E402
        _SCENARIO_SPEC_BY_ID,
        build_scenario,
    )
    from hardware_parity_provenance import _catalog_provenance_stamps  # noqa: E402
    from oracle_grounded.parity_history import reviewed_catalog_stamps

def _fixture_terms(record):
    """``(stimulus, input_fixture, oracle_input_fixture, identical_flag)``."""
    scenario = record.get("scenario") or {}
    oracle = record.get("oracle") or {}
    return (
        scenario.get("stimulus"),
        scenario.get("input_fixture") or {},
        oracle.get("input_fixture") or {},
        oracle.get("identical_input_fixture"),
    )


def _check_input_fixture(record, where):
    """Both sides must provably have run the same encoded input."""
    terms = _fixture_terms(record)
    stimulus = terms[0]
    if not isinstance(stimulus, dict) or not isinstance(stimulus.get("events"), list):
        return [f"{where}: scenario.stimulus.events missing [INPUT_FIXTURE_MISMATCH]"]
    recomputed, shape_error = _recomputed_fixture_sha(stimulus, where)
    if shape_error is not None:
        return shape_error
    return _fixture_binding_errors(terms, recomputed, where)


def _recomputed_fixture_sha(stimulus, where):
    """``(sha256, None)`` or ``(None, errors)`` when the stimulus is not a
    complete finite input the fixture digest can be recomputed from."""
    try:
        return stimulus_fixture(stimulus)["sha256"], None
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return None, [
            f"{where}: scenario.stimulus is not a complete finite input: {exc} "
            "[INPUT_FIXTURE_MISMATCH]"
        ]


def _fixture_binding_errors(terms, recomputed, where):
    """The four-way fixture binding checks, all keyed by the recomputed digest.

    ``terms`` is the ``(stimulus, fixture, oracle_fixture, identical)``
    tuple from ``_fixture_terms``.
    """
    stimulus, fixture, oracle_fixture, identical = terms
    errors = []
    if fixture.get("sha256") != recomputed:
        errors.append(
            f"{where}: scenario.input_fixture.sha256 does not match the complete recorded stimulus "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if not contract.strict_json_equal(oracle_fixture, fixture):
        errors.append(
            f"{where}: oracle.input_fixture must exactly match "
            "scenario.input_fixture; the two sides cannot be shown to have run "
            "the same input "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if identical is not True:
        errors.append(
            f"{where}: oracle.identical_input_fixture must be exactly true "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    if stimulus.get("steps") != len(stimulus["events"]):
        errors.append(f"{where}: stimulus.steps disagrees with the event grid "
                      "[INPUT_FIXTURE_MISMATCH]")
    return errors


def _materialized_catalog_scenario(scenario, where):
    """Rebuild the catalog scenario a record claims, or say why it cannot be.

    Returns ``(expected, errors)``; ``expected`` is None whenever the claim
    cannot even be bound to a catalog entry.
    """
    scenario_id = scenario.get("id")
    spec = _SCENARIO_SPEC_BY_ID.get(scenario_id)
    if spec is None:
        return None, [
            f"{where}: scenario.id {scenario_id!r} is not in the hardware-parity "
            "catalog [SCENARIO_LABEL_MISMATCH]"
        ]
    stimulus = scenario.get("stimulus")
    steps = _catalog_steps(stimulus)
    if steps is None:
        return None, [
            f"{where}: scenario.stimulus.steps must be a positive integer before "
            f"scenario {scenario_id!r} can be bound to the catalog "
            "[SCENARIO_LABEL_MISMATCH]"
        ]
    grid_error = _event_grid_binding_error(scenario_id, stimulus, steps, where)
    if grid_error is not None:
        return None, [grid_error]
    try:
        return build_scenario(spec, steps=steps), []
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return None, [
            f"{where}: catalog scenario {scenario_id!r} cannot be materialized: {exc} "
            "[SCENARIO_LABEL_MISMATCH]"
        ]


def _catalog_steps(stimulus):
    """A positive int step count, or None when the claim cannot be bound."""
    steps = stimulus.get("steps") if isinstance(stimulus, dict) else None
    if type(steps) is not int or steps < 1:  # pylint: disable=unidiomatic-typecheck
        return None
    return steps


def _event_grid_binding_error(scenario_id, stimulus, steps, where):
    """steps must agree with the recorded event grid before it can size the
    catalog rebuild (otherwise it is an untrusted allocation bound)."""
    events = stimulus.get("events") if isinstance(stimulus, dict) else None
    if not isinstance(events, list) or steps != len(events):
        return (
            f"{where}: scenario.stimulus.steps disagrees with the event grid before "
            f"scenario {scenario_id!r} can be bound to the catalog "
            "[SCENARIO_LABEL_MISMATCH]"
        )
    return None


def _catalog_expected_prediction(expected):
    """The candidate_prediction the catalog scenario should carry."""
    return {
        "hypothesis": expected["hypothesis"],
        "expected_verdict": (
            contract.VERDICT_MATCH
            if expected["stress"] == "none"
            else contract.VERDICT_MISMATCH
        ),
    }


def _catalog_prediction_errors(record, expected, scenario_id, where):
    """The generator's prediction and intervention must be the catalog's."""
    prediction = record.get("candidate_prediction")
    errors = [
        f"{where}: candidate_prediction.{key} does not match catalog "
        f"scenario {scenario_id!r} [SCENARIO_LABEL_MISMATCH]"
        for key, expected_value in _catalog_expected_prediction(expected).items()
        if not isinstance(prediction, dict) or not contract.strict_json_equal(
            prediction.get(key), expected_value
        )
    ]
    if not contract.strict_json_equal(record.get("intervention"), expected["intervention"]):
        errors.append(
            f"{where}: intervention does not match catalog scenario {scenario_id!r} "
            "[SCENARIO_LABEL_MISMATCH]"
        )
    return errors


def _check_catalog_scenario(record, where):
    """Bind every prompt- and execution-facing field to the catalog id."""
    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        return [f"{where}: scenario must be an object [SCENARIO_LABEL_MISMATCH]"]
    expected, errors = _materialized_catalog_scenario(scenario, where)
    if expected is None:
        return errors
    scenario_id = scenario.get("id")
    errors += _scenario_binding_errors(scenario, expected, where)
    errors += _catalog_prediction_errors(record, expected, scenario_id, where)
    return errors


def _scenario_binding_errors(scenario, expected, where):
    """Every non-prediction field on the record must equal the catalog's."""
    scenario_id = scenario.get("id")
    return [
        f"{where}: scenario.{key} does not match catalog scenario "
        f"{scenario_id!r} [SCENARIO_LABEL_MISMATCH]"
        for key, expected_value in expected.items()
        if key not in ("hypothesis", "intervention")
        and not contract.strict_json_equal(scenario.get(key), expected_value)
    ]


def _record_round(record):
    """The recorded round number, or None when meta is not an object."""
    meta = record.get("meta")
    return meta.get("round") if isinstance(meta, dict) else None


def _expected_record_id(record):
    """``<scenario_id>-r<NN>``, or None when no valid round is recorded."""
    scenario = record.get("scenario")
    scenario_id = scenario.get("id") if isinstance(scenario, dict) else None
    round_number = _record_round(record)
    if not isinstance(round_number, int) or isinstance(round_number, bool):
        return None
    return f"{scenario_id}-r{round_number:02d}"


def _record_naming_errors(record, where):
    """The id, meta, and generator blocks must name this factory exactly."""
    errors = []
    expected_id = _expected_record_id(record)
    if expected_id is not None and record.get("id") != expected_id:
        errors.append(
            f"{where}: id must be {expected_id!r} for this scenario and round "
            "[ENVELOPE_MALFORMED]"
        )
    if not contract.strict_json_equal(
        record.get("meta"), {"round": _record_round(record), "factory": FACTORY_SLUG}
    ):
        errors.append(
            f"{where}: meta must exactly identify factory {FACTORY_SLUG!r} and its "
            "round [ENVELOPE_MALFORMED]"
        )
    if not contract.strict_json_equal(record.get("generator"), GENERATOR_BLOCK):
        errors.append(
            f"{where}: generator does not match the hardware scenario catalog "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


_PROVENANCE_UNITS = {
    "time": "ms",
    "membrane": "mV_model",
    "weights": "dimensionless",
    "latency": "ms",
}

_EXPECTED_VALIDATION = {
    "validator": VALIDATOR,
    "validator_version": SCHEMA_VERSION,
    "checks": [
        "envelope_contract",
        "identical_input_fixture",
        "q88_conversion_reproducible",
        "parity_metrics_recomputed_from_traces",
        "verdict_consistent_with_traces",
    ],
    "status": "revalidate_on_read",
}


def _expected_provenance_identity(deployment_target, provenance):
    """The provenance identity block this validator would assert."""
    identity = {
        "kind": "unknown" if deployment_target in PHYSICAL_TARGETS else "simulated",
        "tool": VALIDATOR,
        "tool_version": SCHEMA_VERSION,
        "contract_version": contract.CONTRACT_VERSION,
        "units": _PROVENANCE_UNITS,
    }
    identity.update(reviewed_catalog_stamps(provenance, _catalog_provenance_stamps()))
    return identity


def _deployment_target(record):
    """The deployment side's declared execution target, or None."""
    oracle = record.get("oracle")
    deployment = oracle.get("deployment") if isinstance(oracle, dict) else None
    return (
        deployment.get("execution_target") if isinstance(deployment, dict) else None
    )


def _check_record_identity(record, where):
    """Bind the family, round, producer, and validator identities."""
    errors = _record_naming_errors(record, where)
    deployment_target = _deployment_target(record)
    provenance = record.get("provenance")
    expected_identity = _expected_provenance_identity(deployment_target, provenance)
    if not isinstance(provenance, dict) or any(
        not contract.strict_json_equal(provenance.get(key), value)
        for key, value in expected_identity.items()
    ):
        errors.append(
            f"{where}: provenance identity does not match the hardware validator "
            "[ENVELOPE_MALFORMED]"
        )
    if not contract.strict_json_equal(record.get("validation"), _EXPECTED_VALIDATION):
        errors.append(
            f"{where}: validation block does not match the hardware validator contract "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
