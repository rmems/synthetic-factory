#!/usr/bin/env python3
"""The seeded programmatic generator of the fault-recovery family (F1).

A proposal carries a scenario, an intervention and a shallow candidate
prediction -- nothing an oracle owns. This is the family's only module that
imports ``random``: one ``random.Random(seed)`` per batch with #138's draw
order and menus kept exactly, so a seed reproduces its proposal stream (seed
20260823, index 15 is still the fixture-0015 stream). Every generated
configuration satisfies D7 rows 1, 2, 4, 5 and 8 by construction: only
``min_healthy_channels`` (2 or 3) and ``fallback_source`` (the redundant relay
or null) vary from ``DEFAULT_SYSTEM``, and every drawn ``peak_c`` sits above
ambient.
"""

from __future__ import annotations

import random
from typing import Any

from . import distill_vocabulary as vocab
from . import fault_vocabulary as fv
from .import_twins import bind_import_twin

# kind -> (rng, channels, picked) -> parameters, drawing in #138's order.
_DISTURBANCE_BUILDERS: dict[str, Any] = {
    fv.SENSOR_LOSS: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": float(rng.choice([4.0, 8.0, 12.0])),
        "duration_ms": float(rng.choice([6.0, 14.0, 30.0])),
    },
    fv.STALE_SENSOR: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": float(rng.choice([2.0, 6.0])),
        "duration_ms": float(rng.choice([4.0, 9.0, 22.0])),
    },
    fv.EVENT_JITTER: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 2.0,
        "duration_ms": float(rng.choice([10.0, 40.0])),
        "jitter_ms": float(rng.choice([0.4, 1.2, 3.0])),
    },
    fv.BURST_CORRUPTION: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 4.0,
        "duration_ms": float(rng.choice([10.0, 40.0])),
        "corrupt_ratio": float(rng.choice([0.2, 0.5, 0.8])),
    },
    fv.THERMAL_EXCURSION: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 6.0,
        "ramp_ms": float(rng.choice([8.0, 20.0])),
        "peak_c": float(rng.choice([58.0, 70.0, 84.0, 96.0])),
    },
    fv.MISSING_CHANNEL: lambda rng, channels, picked: {"channels": [rng.choice(channels)]},
    fv.MALFORMED_SPIKE_BURST: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "malformed_count": rng.randint(1, 4),
        "malformed_kind": rng.choice(fv.MALFORMED_KINDS),
    },
    fv.DELAYED_RESULT: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "delay_ms": float(rng.choice([6.0, 18.0, 44.0])),
    },
    fv.TEMPORARY_SATURATION: lambda rng, channels, picked: {
        "channels": sorted(picked),
        "onset_ms": 2.0,
        "duration_ms": float(rng.choice([4.0, 16.0])),
    },
}


def _disturbance(rng: random.Random, kind: str, channels: list[str]) -> dict[str, Any]:
    """One proposed disturbance: parameters only, no labels."""
    picked = rng.sample(channels, rng.randint(1, max(1, len(channels) - 1)))
    return {"kind": kind, "parameters": _DISTURBANCE_BUILDERS[kind](rng, channels, picked)}


def _system_draw(rng: random.Random) -> dict[str, Any]:
    """A private copy of the default relay with the two generator-varied controls."""
    system = fv.default_system()
    system["min_healthy_channels"] = rng.choice([2, 3])
    if rng.random() < 0.2:
        system["fallback_source"] = None
    return system


def _prediction(kind: str) -> dict[str, Any]:
    predicted = fv.PREDICTION_BY_KIND[kind]
    return {
        "predicted_outcome": predicted,
        "predicted_outcome_label": fv.OUTCOME_LABELS[predicted],
        "method": fv.PREDICTION_METHOD,
        "confidence": fv.PREDICTION_CONFIDENCE,
    }


def _proposal(index: int, system: dict[str, Any], disturbance: dict[str, Any]) -> dict[str, Any]:
    kind = disturbance["kind"]
    return {
        "index": index,
        "scenario": {"system": system, "mission": fv.MISSION, "disturbance_kind": kind},
        "intervention": disturbance,
        "candidate_prediction": _prediction(kind),
    }


def _check_request(seed: Any, count: Any) -> None:
    """A genuine non-negative integer seed and a genuine integer count >= 1.

    Bool is refused for both. A negative seed is refused because
    ``random.Random(n)`` seeds from ``abs(n)``: seeds ``-n`` and ``n`` would
    yield one proposal stream under two ids, so two corpora an agent picked
    as ``+n``/``-n`` would carry identical content.
    """
    fv.refuse_first(
        (
            (
                not vocab.is_genuine_int(seed) or seed < 0,
                fv.FINDING_SEED_NOT_AN_INTEGER,
                f"seed must be a non-negative integer, got {seed!r}",
            ),
            (
                not vocab.is_genuine_int(count) or count < 1,
                fv.FINDING_COUNT_OUT_OF_DOMAIN,
                f"count must be >= 1 and an integer, got {count!r}",
            ),
        )
    )


def propose_scenarios(seed: int, count: int) -> list[dict[str, Any]]:
    """``count`` proposals from one ``random.Random(seed)``, kinds cycling in order."""
    _check_request(seed, count)
    rng = random.Random(seed)
    proposals = []
    for index in range(count):
        kind = fv.DISTURBANCES[index % len(fv.DISTURBANCES)]
        system = _system_draw(rng)
        proposals.append(_proposal(index, system, _disturbance(rng, kind, system["channels"])))
    return proposals


bind_import_twin(__name__)
