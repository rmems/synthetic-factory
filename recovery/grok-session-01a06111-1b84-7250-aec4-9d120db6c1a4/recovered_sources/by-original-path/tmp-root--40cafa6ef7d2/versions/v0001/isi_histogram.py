#!/usr/bin/env python3
"""NELB ``raster.isi_histogram`` helper (Python stdlib only).

Contract: ``prompts/03-neuromorphic-event-language-bridge.md`` section D and
the published Bridge sidecar shape (``isi_histogram`` bins of
``{lo_ms, hi_ms, count}``).

The histogram is derived from the FULL window's per-neuron inter-spike
intervals. ``raster.excerpt`` is a display subset (schema max 16 events) and
is NOT the source.

JSON shape to embed on a Bridge record
--------------------------------------
Canonical key: ``raster.isi_histogram``. Alias: ``raster.isi_ms_histogram``
(emit one; if both are present they must be identical).

Companion fields used by published NELB rasters (not schema-required, but
needed for the count identity):

.. code-block:: json

    {
      "raster": {
        "window_ms": 32,
        "window_s": 0.032,
        "neurons": 8,
        "mean_rate_hz": 93.75,
        "spikes": 20,
        "excerpt": [{"t_us": 0, "neuron_id": 0}],
        "isi_histogram": [
          {"lo_ms": 1.0, "hi_ms": 2.0, "count": 5},
          {"lo_ms": 2.0, "hi_ms": 4.0, "count": 2},
          {"lo_ms": 4.0, "hi_ms": 8.0, "count": 3},
          {"lo_ms": 8.0, "hi_ms": 16.0, "count": 3},
          {"lo_ms": 16.0, "hi_ms": 32.0, "count": 1}
        ],
        "isi_count_identity": {
          "spikes": 20,
          "distinct_active_neurons": 6,
          "isi_total": 14
        },
        "isi_source": "per-neuron inter-spike intervals over the FULL window; raster.excerpt may be a display subset and is NOT the histogram source"
      }
    }

Binning (matches all published 2026-08-30 NELB rasters)
-------------------------------------------------------
- Explicit bins, each width ``>= 1 ms``, first edge ``lo_ms = 1.0`` (refractory).
- Dyadic interior: ``[1, 2), [2, 4), [4, 8), [8, 16)`` milliseconds.
- Last bin ``[16, window_ms]`` (right-closed so an ISI of exactly ``window_ms``
  is counted). ``hi_ms`` of the last bin is the raster window, not 50 unless
  the window is 50 ms.
- Counts sum to ``spikes - distinct_active_neurons`` over the full window
  (one ISI per extra spike on each active neuron; silent neurons contribute 0).
- Same-neuron ``Δt < 1000 µs`` is a refractory breach: no sub-1 ms bin exists.

Usage::

    from isi_histogram import isi_histogram, raster_isi_fields
    hist = isi_histogram(full_window_spikes, window_ms=32)
    raster.update(raster_isi_fields(full_window_spikes, window_ms=32))
"""

from __future__ import annotations

import json
import sys
from typing import Any, Iterable, Mapping, Sequence

US_PER_MS = 1000
REFRACTORY_US = 1000
WINDOW_MS_MIN = 20
WINDOW_MS_MAX = 50
# Interior dyadic edges in ms. Last edge is the raster window.
DYADIC_LO_MS = (1.0, 2.0, 4.0, 8.0, 16.0)

ISI_SOURCE = (
    "per-neuron inter-spike intervals over the FULL window; "
    "raster.excerpt may be a display subset and is NOT the histogram source"
)


def _json_int(value: Any, name: str) -> int:
    """Accept a JSON integer (Python int, or integral float)."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a JSON integer, got {type(value).__name__}")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"{name} must be integral, got {value!r}")
        value = int(value)
    return value


def _window_ms(window_ms: Any) -> float:
    if isinstance(window_ms, bool) or not isinstance(window_ms, (int, float)):
        raise TypeError("window_ms must be a number")
    window = float(window_ms)
    if window < WINDOW_MS_MIN or window > WINDOW_MS_MAX:
        raise ValueError(
            f"window_ms must be in [{WINDOW_MS_MIN}, {WINDOW_MS_MAX}], got {window_ms!r}"
        )
    return window


def _window_us(window_ms: float) -> int:
    us = window_ms * US_PER_MS
    rounded = round(us)
    if abs(us - rounded) > 1e-9:
        raise ValueError(f"window_ms {window_ms!r} is not an integer number of microseconds")
    return int(rounded)


def bin_edges_ms(window_ms: float) -> list[float]:
    """Return explicit ``>= 1 ms`` dyadic edges ending at ``window_ms``."""

    window = _window_ms(window_ms)
    if window <= DYADIC_LO_MS[-1]:
        raise ValueError(
            f"window_ms {window} is too short for the 16 ms dyadic last-bin start"
        )
    return [float(edge) for edge in DYADIC_LO_MS] + [float(window)]


def _times_by_neuron(
    spikes: Sequence[Mapping[str, Any]],
    *,
    window_us: int,
) -> dict[int, list[int]]:
    times: dict[int, list[int]] = {}
    for index, spike in enumerate(spikes):
        if not isinstance(spike, Mapping):
            raise TypeError(f"spikes[{index}] must be a mapping with t_us and neuron_id")
        t_us = _json_int(spike.get("t_us"), f"spikes[{index}].t_us")
        neuron_id = _json_int(spike.get("neuron_id"), f"spikes[{index}].neuron_id")
        if t_us < 0 or t_us > window_us:
            raise ValueError(
                f"spikes[{index}].t_us={t_us} is outside [0, {window_us}]"
            )
        if neuron_id < 0:
            raise ValueError(f"spikes[{index}].neuron_id={neuron_id} is negative")
        times.setdefault(neuron_id, []).append(t_us)
    for neuron_id in times:
        times[neuron_id].sort()
    return times


def per_neuron_isis_us(
    spikes: Sequence[Mapping[str, Any]],
    *,
    window_ms: float,
) -> list[int]:
    """Full-window per-neuron ISIs in integer microseconds (sorted per neuron)."""

    window = _window_ms(window_ms)
    times = _times_by_neuron(spikes, window_us=_window_us(window))
    intervals: list[int] = []
    for neuron_id, ts in times.items():
        for earlier, later in zip(ts, ts[1:]):
            dt = later - earlier
            if dt < REFRACTORY_US:
                raise ValueError(
                    f"refractory 1 ms violated for neuron_id={neuron_id}: "
                    f"Δt={dt} µs < {REFRACTORY_US}"
                )
            intervals.append(dt)
    return intervals


def isi_count_identity(spikes: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """``spikes - distinct_active_neurons`` identity over the full window."""

    n_spikes = len(spikes)
    active = {
        _json_int(spike.get("neuron_id"), "neuron_id")
        for spike in spikes
        if isinstance(spike, Mapping)
    }
    n_active = len(active)
    return {
        "spikes": n_spikes,
        "distinct_active_neurons": n_active,
        "isi_total": n_spikes - n_active,
    }


def _place(isi_us: int, edges_us: Sequence[int]) -> int:
    """Return bin index for an ISI. Interior bins are half-open; last is closed."""

    last = len(edges_us) - 2
    for index in range(last):
        if edges_us[index] <= isi_us < edges_us[index + 1]:
            return index
    if edges_us[last] <= isi_us <= edges_us[last + 1]:
        return last
    raise ValueError(
        f"ISI {isi_us} µs does not fall in {[e / US_PER_MS for e in edges_us]} ms"
    )


def isi_histogram(
    spikes: Sequence[Mapping[str, Any]],
    window_ms: float,
) -> list[dict[str, float | int]]:
    """Return ``raster.isi_histogram`` from a FULL-window ``{t_us, neuron_id}`` list.

    ``spikes`` must be the complete window train, not ``raster.excerpt``.
    """

    window = _window_ms(window_ms)
    edges_ms = bin_edges_ms(window)
    edges_us = [_window_us(edge) for edge in edges_ms]
    counts = [0] * (len(edges_ms) - 1)
    for isi_us in per_neuron_isis_us(spikes, window_ms=window):
        counts[_place(isi_us, edges_us)] += 1
    identity = isi_count_identity(spikes)
    if sum(counts) != identity["isi_total"]:
        raise RuntimeError(
            "histogram counts do not sum to spikes - distinct_active_neurons: "
            f"{sum(counts)} != {identity['isi_total']}"
        )
    return [
        {"lo_ms": edges_ms[i], "hi_ms": edges_ms[i + 1], "count": counts[i]}
        for i in range(len(counts))
    ]


def raster_isi_fields(
    spikes: Sequence[Mapping[str, Any]],
    window_ms: float,
) -> dict[str, Any]:
    """Fields to merge into ``raster`` (canonical key, identity, source note)."""

    histogram = isi_histogram(spikes, window_ms)
    return {
        "isi_histogram": histogram,
        "isi_count_identity": isi_count_identity(spikes),
        "isi_source": ISI_SOURCE,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

EXCERPT_MAX = 16  # schemas/raster.schema.json excerpt is a display subset


def _train_1050us_min_gap() -> tuple[list[dict[str, int]], float, list[int]]:
    """Three neurons, 5 spikes each, every ISI = 1.05 ms (1050 µs)."""

    spikes: list[dict[str, int]] = []
    for neuron_id in range(3):
        t0 = neuron_id * 40
        for k in range(5):
            spikes.append({"t_us": t0 + k * 1050, "neuron_id": neuron_id})
    # 15 spikes, 3 active neurons, 12 ISIs all in [1, 2)
    return spikes, 32.0, [12, 0, 0, 0, 0]


def _train_single_spike_per_neuron() -> tuple[list[dict[str, int]], float, list[int]]:
    """One spike per neuron: zero ISIs, histogram is all zeros."""

    spikes = [{"t_us": 2000 * n + 500, "neuron_id": n} for n in range(6)]
    return spikes, 40.0, [0, 0, 0, 0, 0]


def _train_mixed_full_window() -> tuple[list[dict[str, int]], float, list[int]]:
    """Varied ISIs across all five dyadic bins; longer than a 16-event excerpt."""

    spikes = [
        # neuron 0: four 1.05 ms ISIs -> [1, 2)
        {"t_us": 0, "neuron_id": 0},
        {"t_us": 1050, "neuron_id": 0},
        {"t_us": 2100, "neuron_id": 0},
        {"t_us": 3150, "neuron_id": 0},
        {"t_us": 4200, "neuron_id": 0},
        # neuron 1: two 2.5 ms ISIs -> [2, 4)
        {"t_us": 0, "neuron_id": 1},
        {"t_us": 2500, "neuron_id": 1},
        {"t_us": 5000, "neuron_id": 1},
        # neuron 2: two 6.0 ms ISIs -> [4, 8)
        {"t_us": 1000, "neuron_id": 2},
        {"t_us": 7000, "neuron_id": 2},
        {"t_us": 13000, "neuron_id": 2},
        # neuron 3: two 12.0 ms ISIs -> [8, 16)
        {"t_us": 2000, "neuron_id": 3},
        {"t_us": 14000, "neuron_id": 3},
        {"t_us": 26000, "neuron_id": 3},
        # neuron 4: one 18.0 ms ISI -> [16, 32]
        {"t_us": 3000, "neuron_id": 4},
        {"t_us": 21000, "neuron_id": 4},
        # neuron 5: 1.0 ms, 13.0 ms, 6.0 ms -> [1,2), [8,16), [4,8)
        {"t_us": 8000, "neuron_id": 5},
        {"t_us": 9000, "neuron_id": 5},
        {"t_us": 22000, "neuron_id": 5},
        {"t_us": 28000, "neuron_id": 5},
    ]
    # counts: [1,2)=5, [2,4)=2, [4,8)=3, [8,16)=3, [16,32]=1
    return spikes, 32.0, [5, 2, 3, 3, 1]


def _counts(histogram: Sequence[Mapping[str, Any]]) -> list[int]:
    return [int(bin["count"]) for bin in histogram]


def _check_bins_explicit(histogram: Sequence[Mapping[str, Any]], window_ms: float) -> list[str]:
    errors: list[str] = []
    if len(histogram) < 1:
        return ["histogram is empty"]
    expected_edges = bin_edges_ms(window_ms)
    if len(histogram) != len(expected_edges) - 1:
        errors.append(
            f"expected {len(expected_edges) - 1} explicit bins, got {len(histogram)}"
        )
    prev_hi = None
    for index, bin_ in enumerate(histogram):
        keys = set(bin_)
        if keys != {"lo_ms", "hi_ms", "count"}:
            errors.append(f"bin[{index}] keys {sorted(keys)} != ['count', 'hi_ms', 'lo_ms']")
            continue
        lo = bin_["lo_ms"]
        hi = bin_["hi_ms"]
        if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
            errors.append(f"bin[{index}] edges are not numeric")
            continue
        width = float(hi) - float(lo)
        if width < 1.0 - 1e-12:
            errors.append(f"bin[{index}] width {width} ms is < 1 ms")
        if float(lo) < 1.0 - 1e-12:
            errors.append(f"bin[{index}] lo_ms {lo} is < 1 ms (refractory floor)")
        if prev_hi is not None and abs(float(lo) - prev_hi) > 1e-12:
            errors.append(f"bin[{index}] lo_ms {lo} does not abut previous hi_ms {prev_hi}")
        prev_hi = float(hi)
        if index < len(expected_edges) - 1:
            if abs(float(lo) - expected_edges[index]) > 1e-12:
                errors.append(f"bin[{index}] lo_ms {lo} != {expected_edges[index]}")
            if abs(float(hi) - expected_edges[index + 1]) > 1e-12:
                errors.append(f"bin[{index}] hi_ms {hi} != {expected_edges[index + 1]}")
    if prev_hi is not None and abs(prev_hi - float(window_ms)) > 1e-12:
        errors.append(f"last hi_ms {prev_hi} != window_ms {window_ms}")
    return errors


def _check_identity(
    spikes: Sequence[Mapping[str, Any]],
    histogram: Sequence[Mapping[str, Any]],
) -> list[str]:
    identity = isi_count_identity(spikes)
    total = sum(_counts(histogram))
    errors = []
    if total != identity["isi_total"]:
        errors.append(
            f"sum(counts)={total} != spikes-distinct_active_neurons="
            f"{identity['spikes']}-{identity['distinct_active_neurons']}="
            f"{identity['isi_total']}"
        )
    return errors


def _display_excerpt(spikes: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    ordered = sorted(
        spikes,
        key=lambda spike: (
            _json_int(spike.get("t_us"), "t_us"),
            _json_int(spike.get("neuron_id"), "neuron_id"),
        ),
    )
    return list(ordered[:EXCERPT_MAX])


def _run(name: str, fn) -> tuple[str, list[str]]:
    try:
        errors = list(fn())
    except Exception as exc:  # noqa: BLE001 — test harness prints FAIL
        return name, [f"raised {type(exc).__name__}: {exc}"]
    return name, errors


def test_1050us_min_gap() -> Iterable[str]:
    spikes, window_ms, expected = _train_1050us_min_gap()
    histogram = isi_histogram(spikes, window_ms)
    yield from _check_bins_explicit(histogram, window_ms)
    yield from _check_identity(spikes, histogram)
    if _counts(histogram) != expected:
        yield f"counts {_counts(histogram)} != {expected} (all ISIs are 1.05 ms)"
    min_dt = min(per_neuron_isis_us(spikes, window_ms=window_ms))
    if min_dt != 1050:
        yield f"min ISI {min_dt} µs != 1050"
    if histogram[0]["count"] != 12:
        yield "1.05 ms ISIs must land in the explicit [1, 2) ms bin, not a sub-ms bin"


def test_single_spike_all_zeros() -> Iterable[str]:
    spikes, window_ms, expected = _train_single_spike_per_neuron()
    histogram = isi_histogram(spikes, window_ms)
    yield from _check_bins_explicit(histogram, window_ms)
    yield from _check_identity(spikes, histogram)
    if _counts(histogram) != expected:
        yield f"counts {_counts(histogram)} != all-zeros {expected}"
    if any(bin_["count"] != 0 for bin_ in histogram):
        yield "single-spike-per-neuron histogram must be all zeros"
    identity = isi_count_identity(spikes)
    if identity["spikes"] != identity["distinct_active_neurons"]:
        yield f"expected one spike per neuron, got {identity}"


def test_mixed_full_window_not_excerpt() -> Iterable[str]:
    spikes, window_ms, expected = _train_mixed_full_window()
    if len(spikes) <= EXCERPT_MAX:
        yield f"mixed train has {len(spikes)} spikes; need more than excerpt max {EXCERPT_MAX}"
    histogram = isi_histogram(spikes, window_ms)
    yield from _check_bins_explicit(histogram, window_ms)
    yield from _check_identity(spikes, histogram)
    if _counts(histogram) != expected:
        yield f"full-window counts {_counts(histogram)} != {expected}"
    excerpt = _display_excerpt(spikes)
    excerpt_hist = isi_histogram(excerpt, window_ms)
    if _counts(excerpt_hist) == _counts(histogram):
        yield (
            "excerpt histogram matched the full-window histogram; "
            "the mixed train must show excerpt is not the source"
        )
    if sum(_counts(excerpt_hist)) != isi_count_identity(excerpt)["isi_total"]:
        yield "excerpt histogram identity failed (control)"
    fields = raster_isi_fields(spikes, window_ms)
    if fields["isi_histogram"] != histogram:
        yield "raster_isi_fields.isi_histogram diverged from isi_histogram()"
    if fields["isi_count_identity"]["isi_total"] != sum(expected):
        yield "isi_count_identity.isi_total does not match full-window ISI count"
    if fields["isi_source"] != ISI_SOURCE:
        yield "isi_source does not state that excerpt is not the histogram source"


def main() -> int:
    results = [
        _run("1.05ms_min_gap", test_1050us_min_gap),
        _run("single_spike_per_neuron_zeros", test_single_spike_all_zeros),
        _run("mixed_full_window_not_excerpt", test_mixed_full_window_not_excerpt),
    ]
    failed = 0
    for name, errors in results:
        if errors:
            failed += 1
            print(f"FAIL {name}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {name}")
    print()
    print("JSON shape to embed in a Bridge record (canonical key raster.isi_histogram):")
    demo_spikes, demo_window, _expected = _train_mixed_full_window()
    print(
        json.dumps(
            {
                "raster": {
                    "window_ms": demo_window,
                    "window_s": demo_window / 1000.0,
                    **raster_isi_fields(demo_spikes, demo_window),
                }
            },
            indent=2,
        )
    )
    print()
    print("FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
