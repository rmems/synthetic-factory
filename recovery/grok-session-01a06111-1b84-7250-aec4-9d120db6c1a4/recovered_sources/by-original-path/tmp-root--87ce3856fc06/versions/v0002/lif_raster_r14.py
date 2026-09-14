#!/usr/bin/env python3
"""PASS/FAIL harness for TTF r12 + r14 LIF raster budgets.

Uses /tmp/lif_raster.py (CUBA LIF, not a spike_events re-encode). Validates
each raster against raster.schema.json plus the sidecar arithmetic:
energy_pJ = spikes * 23, window_s == window_ms/1000, excerpt sorted integer
t_us, same-neuron gap >= 1000 us, spikes = round(n * rate * window_s) ± 1.

Does not write outputs/raw/.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from lif_raster import (  # noqa: E402
    PJ_PER_SPIKE,
    R12_BUDGETS,
    R14_CANDIDATE_BUDGETS,
    SAME_NEURON_GAP_US,
    SCHEMA_PATH,
    WINDOW_S_TOL,
    _R12_076_KERNEL_MS,
    expected_spikes,
    generate_lif_raster,
    load_r12_kernels,
    raster_issues,
    schema_issues,
)

# Explicit r14 (n, rate, window_ms, expected_spikes) so the printed budget
# cannot silently drift from the requested round(n*rate*window_s) values.
R14_EXPECTED: tuple[tuple[str, int, float, float, int], ...] = (
    ("ttf-r14-c1", 80, 40.0, 30.0, 96),  # round(80*40*0.030)=96
    ("ttf-r14-c2", 96, 20.0, 50.0, 96),  # round(96*20*0.050)=96
    ("ttf-r14-c3", 40, 60.0, 25.0, 60),  # round(40*60*0.025)=60
    ("ttf-r14-c4", 72, 35.0, 36.0, 91),  # round(72*35*0.036)=91
    ("ttf-r14-c5", 56, 45.0, 24.0, 60),  # round(56*45*0.024)=60
)


def _contract_issues(raster: Mapping[str, Any], expected: int) -> list[str]:
    """Extra arithmetic checks the schema description requires at runtime."""

    issues: list[str] = []
    spikes = raster.get("spikes")
    energy = raster.get("energy_pJ")
    window_ms = raster.get("window_ms")
    window_s = raster.get("window_s")
    excerpt = raster.get("excerpt")
    if spikes != expected and abs(int(spikes) - expected) > 1:
        issues.append(f"spikes {spikes} vs expected {expected}")
    if energy != spikes * PJ_PER_SPIKE:
        issues.append(f"energy_pJ {energy} != spikes*{PJ_PER_SPIKE}")
    if abs(float(window_s) - float(window_ms) / 1000.0) > WINDOW_S_TOL:
        issues.append("window_s != window_ms/1000")
    if not isinstance(excerpt, list) or not excerpt:
        issues.append("excerpt empty")
        return issues
    prev_t = -1
    last: dict[int, int] = {}
    for item in excerpt:
        t_us = item.get("t_us")
        nid = item.get("neuron_id")
        if type(t_us) is not int:
            issues.append(f"t_us {t_us!r} is not an integer")
            continue
        if t_us < prev_t:
            issues.append("excerpt not sorted by t_us")
        if nid in last and t_us - last[nid] < SAME_NEURON_GAP_US:
            issues.append(f"same-neuron gap {nid}: {t_us - last[nid]} us")
        last[int(nid)] = t_us
        prev_t = t_us
    issues.extend(schema_issues(raster, SCHEMA_PATH))
    return issues


def _line(
    label: str,
    neurons: int,
    rate: float,
    window_ms: float,
    raster: Mapping[str, Any],
    expected: int,
    issues: Sequence[str],
) -> str:
    status = "PASS" if not issues else "FAIL"
    detail = (
        f"{label} n={neurons} rate={rate:g} window_ms={window_ms:g} "
        f"spikes={raster.get('spikes')} budget={expected} "
        f"energy_pJ={raster.get('energy_pJ')} excerpt={len(raster.get('excerpt') or [])} "
        f"{status}"
    )
    if issues:
        detail += " :: " + "; ".join(issues)
    return detail


def check_one(
    label: str,
    neurons: int,
    rate: float,
    window_ms: float,
    seed: int,
    kernels: Sequence[Any] | None,
    expected: int | None = None,
) -> tuple[bool, str]:
    if expected is None:
        expected = expected_spikes(neurons, rate, window_ms)
    raster = generate_lif_raster(neurons, rate, window_ms, seed, kernels)
    issues = raster_issues(raster, kernelized_event_times=kernels)
    for extra in _contract_issues(raster, expected):
        if extra not in issues:
            issues.append(extra)
    return not issues, _line(label, neurons, rate, window_ms, raster, expected, issues)


def main(argv: Sequence[str] | None = None) -> int:
    _ = argv
    kernels_by_id = load_r12_kernels()
    fallback = list(_R12_076_KERNEL_MS)
    ok = True
    lines: list[str] = []

    declared = {(label, n, rate, window) for label, n, rate, window in R14_CANDIDATE_BUDGETS}
    harness = {(label, n, rate, window) for label, n, rate, window, _exp in R14_EXPECTED}
    if declared != harness:
        print("FAIL r14 budget tables drifted between lif_raster.py and lif_raster_r14.py")
        return 1
    for label, n, rate, window, exp in R14_EXPECTED:
        got = expected_spikes(n, rate, window)
        if got != exp:
            print(f"FAIL {label} expected_spikes={got} != {exp}")
            return 1

    for offset, (label, neurons, rate, window_ms) in enumerate(R12_BUDGETS):
        kernels = kernels_by_id.get(label, fallback)
        passed, detail = check_one(
            label, neurons, rate, window_ms, seed=13000 + offset, kernels=kernels
        )
        ok = ok and passed
        lines.append(detail)
    for offset, (label, neurons, rate, window_ms, expected) in enumerate(R14_EXPECTED):
        passed, detail = check_one(
            label,
            neurons,
            rate,
            window_ms,
            seed=14000 + offset,
            kernels=None,
            expected=expected,
        )
        ok = ok and passed
        lines.append(detail)

    for line in lines:
        print(line)
    print("ALL PASS" if ok else "ALL FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
