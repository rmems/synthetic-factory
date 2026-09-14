#!/usr/bin/env python3
"""The verdict a record's own evidence supports, and the public entry points.

Every `result.parity` number is recomputed here from the recorded traces, so a
record cannot assert an agreement its traces do not show, nor relabel a
mismatch.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_result")
    from .neuro_oracle import (  # noqa: E402
        CAPTURE_DETERMINISM_MEANING,
        REFERENCE_DETERMINISM_MEANING,
        TARGET_FIXED_POINT_MODEL,
        digest,
    )
    from .hardware_parity_terms import (  # noqa: E402
        ORACLE_PAIRING,
        RECORD_KIND,
        VALIDATION_DATA_ERRORS,
        contract,
    )
    from .hardware_parity_metrics import compute_parity  # noqa: E402
    from .hardware_parity_record import _expected_summary  # noqa: E402
    from .hardware_parity_validate_deployment import (  # noqa: E402
        _check_fpga_environment,
        _check_physical_claim,
        _check_unavailable_deployment,
    )
    from .hardware_parity_validate_equality import _metrics_equal  # noqa: E402
    from .hardware_parity_validate_identity import (  # noqa: E402
        _check_catalog_scenario,
        _check_input_fixture,
        _check_record_identity,
    )
    from .hardware_parity_validate_oracle import (  # noqa: E402
        _check_determinism,
        _record_oracle_digests,
        _reexecute_reference_sides,
    )
    from .hardware_parity_validate_quantization import _check_quantization  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_result"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from neuro_oracle import (  # noqa: E402
        CAPTURE_DETERMINISM_MEANING,
        REFERENCE_DETERMINISM_MEANING,
        TARGET_FIXED_POINT_MODEL,
        digest,
    )
    from hardware_parity_terms import (  # noqa: E402
        ORACLE_PAIRING,
        RECORD_KIND,
        VALIDATION_DATA_ERRORS,
        contract,
    )
    from hardware_parity_metrics import compute_parity  # noqa: E402
    from hardware_parity_record import _expected_summary  # noqa: E402
    from hardware_parity_validate_deployment import (  # noqa: E402
        _check_fpga_environment,
        _check_physical_claim,
        _check_unavailable_deployment,
    )
    from hardware_parity_validate_equality import _metrics_equal  # noqa: E402
    from hardware_parity_validate_identity import (  # noqa: E402
        _check_catalog_scenario,
        _check_input_fixture,
        _check_record_identity,
    )
    from hardware_parity_validate_oracle import (  # noqa: E402
        _check_determinism,
        _record_oracle_digests,
        _reexecute_reference_sides,
    )
    from hardware_parity_validate_quantization import _check_quantization  # noqa: E402

def _scenario_binding_errors(record, oracle, scenario, where):
    """provenance.scenario_sha256 must identify the recorded model+stimulus."""
    scenario_evidence = {
        "model": scenario.get("model_float"),
        "stimulus": scenario.get("stimulus"),
    }
    if oracle.get("deployment") is None:
        scenario_evidence["requested_deployment"] = oracle.get(
            "requested_deployment"
        )
    try:
        expected_scenario_digest = digest(scenario_evidence)
    except (TypeError, ValueError, OverflowError) as exc:
        return [
            f"{where}: scenario is not canonical JSON: {exc} [ENVELOPE_MALFORMED]"
        ]
    provenance = record.get("provenance")
    if (
        not isinstance(provenance, dict)
        or provenance.get("scenario_sha256") != expected_scenario_digest
    ):
        return [
            f"{where}: provenance.scenario_sha256 does not identify the recorded "
            "model and stimulus [ENVELOPE_MALFORMED]"
        ]
    return []


def _unpaired_result_errors(record, software, result, where):
    """The result contract for a record whose deployment oracle never ran."""
    if not isinstance(software, dict):
        return [f"{where}: oracle.software missing [ENVELOPE_MALFORMED]"]
    errors = _reexecute_reference_sides(record, where)
    errors += _check_determinism(
        software,
        "software",
        where,
        require_rederived_repeats=True,
        expected_meaning=REFERENCE_DETERMINISM_MEANING,
    )
    if result.get("verdict") != contract.VERDICT_INCONCLUSIVE:
        errors.append(
            f"{where}: no deployment-side run, so the verdict must be "
            f"{contract.VERDICT_INCONCLUSIVE!r} [PARITY_VERDICT_INCONSISTENT]"
        )
    if result.get("parity") is not None:
        errors.append(
            f"{where}: parity metrics present without a deployment-side run "
            "[GENERATOR_SUBSTITUTED_FOR_ORACLE]"
        )
    if result.get("reason_codes") != ["ORACLE_UNAVAILABLE"]:
        errors.append(
            f"{where}: an unpaired record must carry exactly ORACLE_UNAVAILABLE "
            "[ORACLE_UNAVAILABLE]"
        )
    errors += _check_unavailable_deployment(record, where)
    expected_summary = _expected_summary(record)
    if result.get("summary") != expected_summary:
        errors.append(
            f"{where}: result.summary is not derived from the unavailable-oracle "
            "evidence [PARITY_METRIC_MISMATCH]"
        )
    return errors


def _recorded_parity_errors(result, parity, verdict, reason_codes, where):
    """The recorded result must reproduce the freshly recomputed parity."""
    errors = []
    recorded_parity = result.get("parity")
    if not isinstance(recorded_parity, dict):
        errors.append(f"{where}: result.parity must be an object [PARITY_METRIC_MISMATCH]")
    else:
        for section in (
            "spike_bitmap",
            "action",
            "timing",
            "membrane",
            "quantization",
            "repeatability",
            "verdict_rule",
        ):
            errors += _metrics_equal(
                recorded_parity.get(section), parity[section], f"result.parity.{section}",
                where,
            )
    if result.get("verdict") != verdict:
        errors.append(
            f"{where}: result.verdict is {result.get('verdict')!r} but the recorded "
            f"traces support {verdict!r} [PARITY_VERDICT_INCONSISTENT]"
        )
    recorded_codes = result.get("reason_codes")
    if recorded_codes != reason_codes:
        errors.append(
            f"{where}: result.reason_codes records {recorded_codes!r} but re-deriving "
            f"gives {reason_codes!r} [PARITY_VERDICT_INCONSISTENT]"
        )
    return errors


def _paired_result_errors(record, oracle, software, deployment, result, where):
    """The result contract for a record with both oracle legs executed."""
    errors = []
    # A paired record has no unavailable oracle to diagnose; anything but an
    # empty list is either a fabricated diagnostic contradicting the completed
    # deployment or a shape violation consumers cannot rely on.
    if oracle.get("unavailable") != []:
        errors.append(
            f"{where}: a paired record must carry exactly an empty "
            "oracle.unavailable list [ENVELOPE_MALFORMED]"
        )
    errors += _check_quantization(record, where)
    errors += _reexecute_reference_sides(record, where)
    errors += _check_determinism(
        software,
        "software",
        where,
        require_rederived_repeats=True,
        expected_meaning=REFERENCE_DETERMINISM_MEANING,
    )
    # The deployment side binds to its adapter-owned meaning just like both
    # reference sides: a fixed-point reference deployment must describe
    # bit-determinism, and a capture-backed one must describe the measured
    # variability of its recorded runs. Without the bind, a deterministic
    # simulator could relabel its repeats as measured hardware variability
    # and mirror that text into result.parity.repeatability unchallenged.
    # An unknown target is already [HW_TARGET_UNKNOWN]; grading it against
    # the capture text keeps the claim checked rather than skipped.
    errors += _check_determinism(
        deployment,
        "deployment",
        where,
        require_rederived_repeats=(
            deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL
        ),
        expected_meaning=(
            REFERENCE_DETERMINISM_MEANING
            if deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL
            else CAPTURE_DETERMINISM_MEANING
        ),
    )

    scenario = record.get("scenario") or {}
    try:
        parity, verdict, reason_codes = compute_parity(scenario, software, deployment)
    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        return errors + [f"{where}: parity metrics are not recomputable: {exc}"]

    errors += _recorded_parity_errors(result, parity, verdict, reason_codes, where)
    expected_summary = _expected_summary(record)
    if result.get("summary") != expected_summary:
        errors.append(
            f"{where}: result.summary is not derived from the validated parity evidence "
            "[PARITY_METRIC_MISMATCH]"
        )
    return errors


def _validate_record(record, where):
    """Full validation of one hardware-parity record."""
    oracle = record.get("oracle") if isinstance(record, dict) else None
    digests = _record_oracle_digests(oracle) if isinstance(oracle, dict) else None
    errors = contract.check_envelope(record, where, oracle_digests=digests)
    if not isinstance(record, dict) or record.get("record_kind") != RECORD_KIND:
        return errors
    # A truthy non-dict `oracle` would sail past every `(x or {}).get(...)`
    # below and raise deep inside a metric function, so stop it here.
    if not isinstance(oracle, dict):
        return errors + [f"{where}: oracle must be an object [ENVELOPE_MALFORMED]"]
    # Execution-facing oracle metadata is validated, not trusted: free text
    # here could advertise a pairing the checked adapter legs never ran.
    if oracle.get("pairing") != ORACLE_PAIRING:
        errors.append(
            f"{where}: oracle.pairing must be the canonical {ORACLE_PAIRING!r} "
            "[ENVELOPE_MALFORMED]"
        )
    scenario = record.get("scenario")
    if not isinstance(scenario, dict):
        return errors
    errors += _scenario_binding_errors(record, oracle, scenario, where)
    errors += _check_input_fixture(record, where)
    errors += _check_catalog_scenario(record, where)
    errors += _check_record_identity(record, where)
    errors += _check_fpga_environment(record, where)
    errors += _check_physical_claim(record, where)

    result = record.get("result")
    if not isinstance(result, dict):
        return errors
    software = oracle.get("software")
    deployment = oracle.get("deployment")

    if deployment is None:
        return errors + _unpaired_result_errors(record, software, result, where)
    if not isinstance(software, dict):
        errors.append(f"{where}: oracle.software missing [ENVELOPE_MALFORMED]")
        return errors
    if not isinstance(deployment, dict):
        return errors + [
            f"{where}: oracle.deployment must be an object or absent [ENVELOPE_MALFORMED]"
        ]
    return errors + _paired_result_errors(
        record, oracle, software, deployment, result, where
    )


def validate_record(record, where):
    """Validate one record without allowing hostile nesting to abort a scan."""
    try:
        return _validate_record(record, where)
    except VALIDATION_DATA_ERRORS as exc:
        return [
            f"{where}: record contains malformed evidence: "
            f"{exc} [ENVELOPE_MALFORMED]"
        ]


def validate_records(records, source="record"):
    errors = []
    for index, record in enumerate(records, 1):
        errors += validate_record(record, f"{source}:{index}")
    return errors


if __package__:
    _expose_package_sibling(__name__)
