#!/usr/bin/env python3
"""Re-executing the in-repo oracles and cross-checking determinism.

Both in-repo simulators are deterministic, so their traces are re-derivable and
are re-derived. A physical target cannot be, which is why its evidence rests on
the capture chain instead and the record says so.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_oracle")
    from .hardware_parity_validate_determinism import (  # noqa: E402,F401
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
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
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

def _compare_side(recorded, fresh, label, where):
    """Compare one recorded oracle run against a fresh re-simulation."""
    errors = []
    for key in (
        "spikes",
        "spike_events",
        "action",
        "membrane",
        "arithmetic",
        "latency",
    ):
        section_errors = _metrics_equal(
            recorded.get(key), fresh[key], f"oracle.{label}.{key}", where
        )
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
        errors += section_errors
    expected = run_digest(fresh)
    if recorded.get("output_digest") != expected:
        errors.append(
            f"{where}: oracle.{label}.output_digest is not the digest of a "
            "re-simulation [PARITY_METRIC_MISMATCH]"
        )
    return errors


def _check_reference_identity(run, adapter_type, label, where):
    """Bind a reference result to the exact in-repo adapter that produced it."""
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

    software = oracle.get("software")
    if isinstance(software, dict):
        errors += _check_reference_identity(
            software, SoftwareFloatAdapter, "software", where
        )
        try:
            fresh = SoftwareFloatAdapter().run(model, stimulus, repeats=1)
        except (
            ValueError,
            KeyError,
            TypeError,
            IndexError,
            AttributeError,
            OverflowError,
        ) as exc:
            return errors + [
                f"{where}: the recorded model and stimulus are not simulable: {exc}"
            ]
        errors += _compare_side(software, fresh, "software", where)

    deployment = oracle.get("deployment")
    if isinstance(deployment, dict):
        if deployment.get("execution_target") == TARGET_FIXED_POINT_MODEL:
            errors += _check_reference_identity(
                deployment, FixedPointReferenceAdapter, "deployment", where
            )
            try:
                fresh = FixedPointReferenceAdapter().run(
                    model, stimulus, repeats=1
                )
            except (
                ValueError,
                KeyError,
                TypeError,
                IndexError,
                AttributeError,
                OverflowError,
            ) as exc:
                return errors + [
                    f"{where}: the recorded model is not quantizable/simulable: {exc}"
                ]
            errors += _compare_side(deployment, fresh, "deployment", where)
    return errors


if __package__:
    _expose_package_sibling(__name__)
