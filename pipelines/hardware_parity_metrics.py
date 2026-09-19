#!/usr/bin/env python3
"""Parity metrics: what the two recorded runs actually agree and disagree on.

Every number here is recomputed from the recorded spike and membrane traces
during validation, so this module is the definition of the agreement a record
is allowed to claim, not a summary of one.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_metrics")
    from .hardware_parity_metrics_spikes import (  # noqa: E402,F401  # pylint: disable=unused-import
        _first_spike_steps,
        _rectangular,
        _spike_cell_tally,
        _spike_cells,
        _spike_grid_shape_reason,
        spike_bitmap_metrics,
        timing_metrics,
    )
    from .neuro_oracle import PHYSICAL_TARGETS  # noqa: E402
    from .hardware_parity_terms import MEMBRANE_TOLERANCE, contract  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_metrics"
    )
    from hardware_parity_metrics_spikes import (  # noqa: E402,F401
        _first_spike_steps,
        _rectangular,
        _spike_cell_tally,
        _spike_cells,
        _spike_grid_shape_reason,
        spike_bitmap_metrics,
        timing_metrics,
    )
    from neuro_oracle import PHYSICAL_TARGETS  # noqa: E402
    from hardware_parity_terms import MEMBRANE_TOLERANCE, contract  # noqa: E402

MEMBRANE_UNITS = "mV_model"


def _membrane_field_matches(membranes, field, expected):
    return all((membrane or {}).get(field) == expected for membrane in membranes)


def _same_trace_shape(soft, hard):
    if not all(_rectangular(trace) for trace in (soft, hard)):
        return False
    return (len(soft), len(soft[0])) == (len(hard), len(hard[0]))


def _membrane_incomparable_reason(software_membrane, hardware_membrane, soft, hard):
    """Refuse absent observation, incompatible units, or unequal trace shapes."""
    membranes = (software_membrane, hardware_membrane)
    if not all((membrane or {}).get("observable") for membrane in membranes):
        return "at least one side does not expose membrane state"
    if not _membrane_field_matches(membranes, "units", MEMBRANE_UNITS):
        return f"both membrane traces must be {MEMBRANE_UNITS!r} units"
    if not _same_trace_shape(soft, hard):
        return "membrane traces have different shapes"
    return None


def membrane_metrics(software_membrane, hardware_membrane):
    """Membrane error where both sides expose an observable trace."""
    soft = (software_membrane or {}).get("trace")
    hard = (hardware_membrane or {}).get("trace")
    reason = _membrane_incomparable_reason(
        software_membrane, hardware_membrane, soft, hard
    )
    if reason is not None:
        return {
            "observable": False,
            "reason_code": "MEMBRANE_DIVERGENCE",
            "reason": reason,
        }
    diffs = [abs(a - b) for row_a, row_b in zip(soft, hard) for a, b in zip(row_a, row_b)]
    return _observable_membrane_metrics(diffs)


def _observable_membrane_metrics(diffs):
    """The error aggregates over two already-paired membrane traces."""
    return {
        "observable": True,
        "units": MEMBRANE_UNITS,
        "samples": len(diffs),
        "max_abs_error": max(diffs) if diffs else 0.0,
        "mean_abs_error": (sum(diffs) / len(diffs)) if diffs else 0.0,
        "tolerance": MEMBRANE_TOLERANCE,
        "within_tolerance": (max(diffs) if diffs else 0.0) <= MEMBRANE_TOLERANCE,
    }


def quantization_metrics(deployment_run):
    """Restate the recorded Q8.8 conversion error as parity evidence.

    Two independent kinds of saturation matter and are counted separately:
    *export* saturation, where a parameter does not fit the format, and
    *runtime* saturation, where every parameter fits but a partial sum does
    not. The second kind leaves the exported weights looking perfectly
    faithful, so it has to be reported from the run rather than the export.
    """
    provenance = (deployment_run or {}).get("quantization")
    runtime_saturation = ((deployment_run or {}).get("arithmetic") or {}).get(
        "saturation_events"
    )
    if not provenance:
        return {
            "available": False,
            "reason": "deployment side did not report a quantization provenance",
            "runtime_saturation_events": runtime_saturation,
        }
    return {
        "available": True,
        "format": provenance.get("format"),
        "parameter_count": provenance.get("parameter_count"),
        "max_abs_error": provenance.get("max_abs_error"),
        "mean_abs_error": provenance.get("mean_abs_error"),
        "saturated_parameter_count": provenance.get("saturated_parameter_count"),
        "runtime_saturation_events": runtime_saturation,
        "step": provenance.get("step"),
    }


def repeatability_metrics(software_run, hardware_run):
    """Determinism of each side, kept distinct from hardware repeatability."""
    software_det = software_run.get("determinism", {})
    hardware_det = hardware_run.get("determinism", {})
    return {
        "software": {
            "repeats": software_run.get("repeats"),
            "distinct_digests": software_det.get("distinct_digests"),
            "identical_repeats": software_det.get("identical_repeats"),
        },
        "deployment": {
            "repeats": hardware_run.get("repeats"),
            "distinct_digests": hardware_det.get("distinct_digests"),
            "identical_repeats": hardware_det.get("identical_repeats"),
        },
        "hardware_repeatability_measured": False,
        "meaning": hardware_det.get("meaning"),
    }


def _parity_metrics(scenario, software_run, hardware_run):
    """Every parity measurement for one paired run, before any verdict."""
    dt_ms = scenario["stimulus"]["dt_ms"]
    bitmap = spike_bitmap_metrics(software_run.get("spikes"), hardware_run.get("spikes"))
    timing = timing_metrics(
        software_run.get("spikes"), hardware_run.get("spikes"), dt_ms
    )
    membrane = membrane_metrics(software_run.get("membrane"), hardware_run.get("membrane"))
    quantization = quantization_metrics(hardware_run)
    repeatability = repeatability_metrics(software_run, hardware_run)
    software_action = software_run.get("action", {})
    hardware_action = hardware_run.get("action", {})
    return {
        "spike_bitmap": bitmap,
        "action": {
            "software": software_action.get("label"),
            "deployment": hardware_action.get("label"),
            "software_counts": software_action.get("counts"),
            "deployment_counts": hardware_action.get("counts"),
            "agree": software_action.get("label") == hardware_action.get("label"),
            "decode_rule": software_action.get("rule"),
        },
        "timing": timing,
        "membrane": membrane,
        "quantization": quantization,
        "repeatability": repeatability,
        "verdict_rule": (
            "verdict is `mismatch` iff the spike bitmaps differ or the decoded actions "
            "differ; membrane, quantization, repeatability and latency findings are "
            "always carried as reason codes even when the verdict is `match`"
        ),
    }


def _deployment_qualification_codes(repeatability, hardware_run):
    """What the deployment side leaves unproven, whatever its traces show."""
    codes = []
    if not repeatability["hardware_repeatability_measured"]:
        codes.append("REPEATABILITY_UNPROVEN")
    if not (hardware_run.get("latency") or {}).get("measured"):
        codes.append("LATENCY_NOT_MEASURED")
    if hardware_run.get("execution_target") not in PHYSICAL_TARGETS:
        codes.append("ORACLE_UNAVAILABLE")
    else:
        # Self-contained capture hashes prove neither physical execution nor
        # physical latency. Preserve trace diagnostics without hardware authority.
        codes.extend(("DEPLOYMENT_TRACE_NOT_REDERIVABLE", "PHYSICAL_EXECUTION_UNATTESTED",
                      "LATENCY_NOT_MEASURED"))
    return codes


def _behavioural_reason_codes(parity):
    """Retain independently observed bitmap and decoded-action disagreement."""
    bitmap = parity["spike_bitmap"]
    codes = []
    if not bitmap.get("comparable") or bitmap.get("hamming_distance", 1) > 0:
        codes.append("SPIKE_BITMAP_DISAGREEMENT")
    if not parity["action"]["agree"]:
        codes.append("ACTION_DISAGREEMENT")
    return codes


def _membrane_reason_codes(membrane):
    if membrane.get("observable"):
        return [] if membrane.get("within_tolerance") else ["MEMBRANE_DIVERGENCE"]
    reason = membrane.get("reason_code")
    return [reason] if reason else []


def _quantization_reason_codes(quantization):
    saturated = (quantization.get("saturated_parameter_count")
                 or quantization.get("runtime_saturation_events"))
    return ["QUANTIZATION_SATURATION"] if saturated else []


def _parity_reason_codes(parity, hardware_run):
    """Keep behavioural, numeric, and evidence-authority diagnostics together."""
    return (
        _behavioural_reason_codes(parity)
        + _membrane_reason_codes(parity["membrane"])
        + _quantization_reason_codes(parity["quantization"])
        + _deployment_qualification_codes(parity["repeatability"], hardware_run)
    )


def compute_parity(scenario, software_run, hardware_run):
    """All parity metrics for one paired run, plus the verdict they support."""
    parity = _parity_metrics(scenario, software_run, hardware_run)
    reason_codes = _parity_reason_codes(parity, hardware_run)
    behavioural_mismatch = (
        "SPIKE_BITMAP_DISAGREEMENT" in reason_codes or "ACTION_DISAGREEMENT" in reason_codes
    )
    verdict = contract.VERDICT_MISMATCH if behavioural_mismatch else contract.VERDICT_MATCH
    if "PHYSICAL_EXECUTION_UNATTESTED" in reason_codes:
        verdict = contract.VERDICT_INCONCLUSIVE
        parity["verdict_rule"] = (
            "physical parity is inconclusive without independently authenticated execution; "
            "numeric trace comparisons and mismatch diagnostics remain available"
        )
    return parity, verdict, sorted(set(reason_codes))


if __package__:
    _expose_package_sibling(__name__)
