#!/usr/bin/env python3
"""Re-executing the in-repo oracles and cross-checking determinism.

Both in-repo simulators are deterministic, so their traces are re-derivable and
are re-derived. A physical target cannot be, which is why its evidence rests on
the capture chain instead and the record says so.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_oracle")
    from .hardware_parity_validate_determinism import (  # noqa: E402,F401  # pylint: disable=unused-import
        _check_determinism,
        _determinism_claim_errors,
        _record_oracle_digests,
        _repeat_digest_evidence_errors,
    )
    from .neuro_oracle import (  # noqa: E402
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
        TARGET_FIXED_POINT_MODEL,
        run_digest,
    )
    from .hardware_parity_validate_equality import _metrics_equal  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_oracle"
    )
    from hardware_parity_validate_determinism import (  # noqa: E402,F401
        _check_determinism,
        _determinism_claim_errors,
        _record_oracle_digests,
        _repeat_digest_evidence_errors,
    )
    from neuro_oracle import (  # noqa: E402
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
        TARGET_FIXED_POINT_MODEL,
        run_digest,
    )
    from hardware_parity_validate_equality import _metrics_equal  # noqa: E402

def _compare_section(recorded, fresh, key, loc):
    """One metric section of a re-simulation comparison; ``loc`` is
    ``(label, where)``."""
    label, where = loc
    section_errors = _metrics_equal(
        recorded.get(key), fresh[key], f"oracle.{label}.{key}", where
    )
    errors = []
    if section_errors:
        reason_code = (
            "MEMBRANE_DIVERGENCE"
            if key == "membrane"
            else "PARITY_METRIC_MISMATCH"
        )
        errors.append(
            f"{where}: oracle.{label}.{key} does not match a re-simulation "
            f"[{reason_code}]"
        )
    if key == "membrane":
        section_errors = [
            error.replace("[PARITY_METRIC_MISMATCH]", "[MEMBRANE_DIVERGENCE]")
            for error in section_errors
        ]
    return errors + section_errors


def _compare_side(recorded, fresh, loc):
    """Compare one recorded oracle run against a fresh re-simulation.
    ``loc`` is ``(label, where)``."""
    label, where = loc
    errors = []
    for key in (
        "spikes",
        "spike_events",
        "action",
        "membrane",
        "arithmetic",
        "latency",
    ):
        errors += _compare_section(recorded, fresh, key, loc)
    expected = run_digest(fresh)
    if recorded.get("output_digest") != expected:
        errors.append(
            f"{where}: oracle.{label}.output_digest is not the digest of a "
            "re-simulation [PARITY_METRIC_MISMATCH]"
        )
    return errors


def _check_reference_identity(run, adapter_type, loc):
    """Bind a reference result to the exact in-repo adapter that produced it.
    ``loc`` is ``(label, where)``."""
    label, where = loc
    errors = []
    expected = {
        "adapter": adapter_type.name,
        "execution_target": adapter_type.execution_target,
        "runtime_class": adapter_type.runtime_class,
    }
    for key, value in expected.items():
        if run.get(key) != value:
            reason_code = (
                "HW_TARGET_UNKNOWN"
                if key == "execution_target"
                else "HW_PROVENANCE_MISSING"
            )
            errors.append(
                f"{where}: oracle.{label}.{key} must be {value!r}, got "
                f"{run.get(key)!r} [{reason_code}]"
            )
    return errors


def _reexecute_reference_sides(record, where):
    """Re-run every in-repo simulator and compare against what was recorded.

    This is the anti-fabrication gate for this family. Recomputing the parity
    metrics from the record's own traces is not enough on its own: copying one
    side's traces onto the other would then produce a self-consistent record
    asserting a match that never happened. Both in-repo simulators are
    deterministic, so the traces themselves are re-derivable and are re-derived.

    A physical deployment target cannot be re-simulated -- that is the whole
    point of running on hardware -- so for those the software leg is re-derived
    and the deployment leg rests on the capture digest chain and the board
    provenance that :func:`_check_physical_claim` demands. The record says
    which of the two it is, and never implies more.
    """
    errors = []
    scenario = record.get("scenario") or {}
    model = scenario.get("model_float")
    stimulus = scenario.get("stimulus")
    if not isinstance(model, dict) or not isinstance(stimulus, dict):
        return [
            f"{where}: scenario.model_float and scenario.stimulus are required to "
            "re-derive the recorded runs [ENVELOPE_MALFORMED]"
        ]
    oracle = record.get("oracle") or {}

    side_errors, fatal = _reexecute_side(
        oracle.get("software"),
        (
            SoftwareFloatAdapter,
            "software",
            model,
            stimulus,
            "the recorded model and stimulus are not simulable",
        ),
        where,
    )
    errors += side_errors
    if fatal:
        return errors

    return errors + _reference_deployment_errors(oracle, (model, stimulus), where)


def _reference_deployment_errors(oracle, case, where):
    """The fixed-point deployment leg — only when the record names it.
    ``case`` is ``(model, stimulus)``."""
    model, stimulus = case
    deployment = oracle.get("deployment")
    is_reference_target = (
        isinstance(deployment, dict)
        and deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL
    )
    if not is_reference_target:
        return []
    side_errors, _ = _reexecute_side(
        deployment,
        (
            FixedPointReferenceAdapter,
            "deployment",
            model,
            stimulus,
            "the recorded model is not quantizable/simulable",
        ),
        where,
    )
    return side_errors


def _reexecute_side(side, check, where):
    """Re-run one in-repo reference side against the recorded model/stimulus.

    ``check`` is ``(adapter_cls, label, model, stimulus, failure)``.
    Returns ``(errors, fatal)`` — ``fatal`` means the recorded inputs could
    not even be simulated, so no further side can be graded.
    """
    adapter_cls, label, model, stimulus, failure = check
    if not isinstance(side, dict):
        return [], False
    errors = _check_reference_identity(side, adapter_cls, (label, where))
    try:
        fresh = adapter_cls().run(model, stimulus, repeats=1)
    except (
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        errors.append(f"{where}: {failure}: {exc}")
        return errors, True
    errors += _compare_side(side, fresh, (label, where))
    return errors, False


if __package__:
    _expose_package_sibling(__name__)
