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
        digest,
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
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_identity"
    )
    from neuro_oracle import (  # noqa: E402
        PHYSICAL_TARGETS,
        digest,
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

def _check_input_fixture(record, where):
    """Both sides must provably have run the same encoded input."""
    errors = []
    scenario = record.get("scenario") or {}
    stimulus = scenario.get("stimulus")
    fixture = scenario.get("input_fixture") or {}
    oracle_fixture = (record.get("oracle") or {}).get("input_fixture") or {}
    identical = (record.get("oracle") or {}).get("identical_input_fixture")
    if not isinstance(stimulus, dict) or not isinstance(stimulus.get("events"), list):
        return [f"{where}: scenario.stimulus.events missing [INPUT_FIXTURE_MISMATCH]"]
    try:
        recomputed = digest(stimulus["events"])
    except (TypeError, ValueError, OverflowError) as exc:
        return [
            f"{where}: scenario.stimulus.events is not canonical finite JSON: {exc} "
            "[INPUT_FIXTURE_MISMATCH]"
        ]
    if fixture.get("sha256") != recomputed:
        errors.append(
            f"{where}: scenario.input_fixture.sha256 does not match the recorded events "
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
    steps = stimulus.get("steps") if isinstance(stimulus, dict) else None
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 1:
        return None, [
            f"{where}: scenario.stimulus.steps must be a positive integer before "
            f"scenario {scenario_id!r} can be bound to the catalog "
            "[SCENARIO_LABEL_MISMATCH]"
        ]
    events = stimulus.get("events") if isinstance(stimulus, dict) else None
    if not isinstance(events, list) or steps != len(events):
        # A record-declared `steps` this far out of line with its own event
        # grid is already invalid; bind it to trusted evidence (the actual
        # event count) before using it as an allocation bound below, rather
        # than letting an untrusted huge integer reach build_scenario().
        return None, [
            f"{where}: scenario.stimulus.steps disagrees with the event grid before "
            f"scenario {scenario_id!r} can be bound to the catalog "
            "[SCENARIO_LABEL_MISMATCH]"
        ]
    try:
        return build_scenario(spec, steps=steps), []
    except (ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        return None, [
            f"{where}: catalog scenario {scenario_id!r} cannot be materialized: {exc} "
            "[SCENARIO_LABEL_MISMATCH]"
        ]


def _catalog_prediction_errors(record, expected, scenario_id, where):
    """The generator's prediction and intervention must be the catalog's."""
    errors = []
    prediction = record.get("candidate_prediction")
    expected_prediction = {
        "hypothesis": expected["hypothesis"],
        "expected_verdict": (
            contract.VERDICT_MATCH
            if expected["stress"] == "none"
            else contract.VERDICT_MISMATCH
        ),
    }
    for key, expected_value in expected_prediction.items():
        if not isinstance(prediction, dict) or not contract.strict_json_equal(
            prediction.get(key), expected_value
        ):
            errors.append(
                f"{where}: candidate_prediction.{key} does not match catalog "
                f"scenario {scenario_id!r} [SCENARIO_LABEL_MISMATCH]"
            )
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
    expected_scenario = {
        key: value
        for key, value in expected.items()
        if key not in ("hypothesis", "intervention")
    }
    for key, expected_value in expected_scenario.items():
        if not contract.strict_json_equal(scenario.get(key), expected_value):
            errors.append(
                f"{where}: scenario.{key} does not match catalog scenario "
                f"{scenario_id!r} [SCENARIO_LABEL_MISMATCH]"
            )
    errors += _catalog_prediction_errors(record, expected, scenario_id, where)
    return errors


def _record_naming_errors(record, where):
    """The id, meta, and generator blocks must name this factory exactly."""
    errors = []
    scenario = record.get("scenario")
    meta = record.get("meta")
    scenario_id = scenario.get("id") if isinstance(scenario, dict) else None
    round_number = meta.get("round") if isinstance(meta, dict) else None
    if isinstance(round_number, int) and not isinstance(round_number, bool):
        expected_id = f"{scenario_id}-r{round_number:02d}"
        if record.get("id") != expected_id:
            errors.append(
                f"{where}: id must be {expected_id!r} for this scenario and round "
                "[ENVELOPE_MALFORMED]"
            )
    if not contract.strict_json_equal(
        meta, {"round": round_number, "factory": FACTORY_SLUG}
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


def _check_record_identity(record, where):
    """Bind the family, round, producer, and validator identities."""
    oracle = record.get("oracle")
    errors = _record_naming_errors(record, where)
    deployment = oracle.get("deployment") if isinstance(oracle, dict) else None
    deployment_target = (
        deployment.get("execution_target") if isinstance(deployment, dict) else None
    )
    provenance = record.get("provenance")
    expected_provenance_identity = {
        "kind": "hil" if deployment_target in PHYSICAL_TARGETS else "simulated",
        "tool": VALIDATOR,
        "tool_version": SCHEMA_VERSION,
        "contract_version": contract.CONTRACT_VERSION,
        "units": {
            "time": "ms",
            "membrane": "mV_model",
            "weights": "dimensionless",
            "latency": "ms",
        },
    }
    expected_provenance_identity.update(_catalog_provenance_stamps())
    if not isinstance(provenance, dict) or any(
        not contract.strict_json_equal(provenance.get(key), value)
        for key, value in expected_provenance_identity.items()
    ):
        errors.append(
            f"{where}: provenance identity does not match the hardware validator "
            "[ENVELOPE_MALFORMED]"
        )
    expected_validation = {
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
    if not contract.strict_json_equal(record.get("validation"), expected_validation):
        errors.append(
            f"{where}: validation block does not match the hardware validator contract "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
