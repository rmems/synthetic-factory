#!/usr/bin/env python3
"""The seeded programmatic generator of the fault-recovery family (F1).

A proposal carries a scenario, an intervention and a shallow candidate
prediction -- nothing an oracle owns. The family draws from the shared
``oracle_grounded.rng.DrawStream`` (SHA-256 over seed and draw counter, no
``random`` module) behind its own seed codes, with #138's draw order and menus
kept exactly, so a seed reproduces its proposal stream on every platform and
Python version. Every generated
configuration satisfies D7 rows 1, 2, 4, 5 and 8 by construction: only
``min_healthy_channels`` (2 or 3) and ``fallback_source`` (the redundant relay
or null) vary from ``DEFAULT_SYSTEM``, and every drawn ``peak_c`` sits above
ambient.
"""

from __future__ import annotations

from typing import Any

from . import distill_vocabulary as vocab
from . import fault_vocabulary as fv
from . import rng as shared_rng
from .import_twins import bind_import_twin


class DrawStream(shared_rng.DrawStream):
    """The family's draw stream: the shared ``rng.DrawStream`` behind the family's seed codes.

    The stream itself (SHA-256 over ``"{seed}:{counter}"``, 64 bits per draw) is
    the shared primitive, so the pinned proposal streams are unchanged; only
    the seed refusal is family-coded (``FINDING_SEED_*``) and runs first.
    """

    def __init__(self, seed: int) -> None:
        _check_seed(seed)
        super().__init__(seed)


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


def _disturbance(rng: DrawStream, kind: str, channels: list[str]) -> dict[str, Any]:
    """One proposed disturbance: parameters only, no labels."""
    picked = rng.sample(channels, rng.randint(1, max(1, len(channels) - 1)))
    return {"kind": kind, "parameters": _DISTURBANCE_BUILDERS[kind](rng, channels, picked)}


def _system_draw(rng: DrawStream) -> dict[str, Any]:
    """A private copy of the default relay with the two generator-varied controls."""
    system = fv.default_system()
    system["min_healthy_channels"] = rng.choice([2, 3])
    if rng.chance(0.2):
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


def _check_seed(seed: Any) -> None:
    """A genuine integer in ``[0, MAX_SEED]`` (64 bits); bool is refused.

    The same rule guards ``propose_scenarios`` and ``DrawStream`` itself, so
    the seed in a record id and in ``generator.seed`` is one unambiguous
    integer the stream can format, and no two accepted seeds share a stream.
    """
    is_seed = vocab.is_genuine_int(seed)
    fv.refuse_first(
        (
            (not is_seed, fv.FINDING_SEED_NOT_AN_INTEGER, f"seed must be an integer, got {fv.shown(seed)}"),
            (
                is_seed and not 0 <= seed <= fv.MAX_SEED,
                fv.FINDING_SEED_OUT_OF_DOMAIN,
                f"seed must lie in [0, {fv.MAX_SEED}] (a 64-bit integer), got {fv.shown(seed)}",
            ),
        )
    )


def _check_request(seed: Any, count: Any) -> None:
    """The seed rule above, then a genuine integer count in ``[1, MAX_COUNT]``."""
    _check_seed(seed)
    fv.refuse_when(
        not vocab.is_genuine_int(count) or not 1 <= count <= fv.MAX_COUNT,
        fv.FINDING_COUNT_OUT_OF_DOMAIN,
        f"count must be >= 1 and an integer at most {fv.MAX_COUNT}, got {fv.shown(count)}",
    )


def propose_scenarios(seed: int, count: int) -> list[dict[str, Any]]:
    """``count`` proposals from one :class:`DrawStream`, kinds cycling in order."""
    _check_request(seed, count)
    rng = DrawStream(seed)
    proposals = []
    for index in range(count):
        kind = fv.DISTURBANCES[index % len(fv.DISTURBANCES)]
        system = _system_draw(rng)
        proposals.append(_proposal(index, system, _disturbance(rng, kind, system["channels"])))
    return proposals


bind_import_twin(__name__)
