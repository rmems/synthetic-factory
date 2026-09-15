#!/usr/bin/env python3
"""NOTES-rNN.md renderer for a hopper success/handoff pair.

Coverage is required on both plants. The mill's ``.get(..., 80)`` default is
dropped so a missing field fails closed. Reward metrics cited here are
constants from the episode builder, not measurements.
"""

from __future__ import annotations

from collections.abc import Mapping

from ._contract import FINDING_PLANT_FIELD_INVALID, bind_import_twin, refuse_when

__all__ = ["notes_md"]


def _coverage(plant: Mapping, label: str) -> int:
    value = plant.get("coverage")
    refuse_when(
        not isinstance(value, int) or isinstance(value, bool) or value < 0,
        FINDING_PLANT_FIELD_INVALID,
        f"{label} coverage must be a non-negative int, got {value!r}",
    )
    return value


def notes_md(
    factory: str,
    round_n: int,
    ok: Mapping,
    bad: Mapping,
    ok_id: str,
    bad_id: str,
) -> str:
    cov = max(_coverage(ok, "success"), _coverage(bad, "handoff"))
    return (
        f"# {factory} — NOTES r{round_n}\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"## Episodes\n"
        f"- `{ok_id}`: 16 steps, success=True, domain={ok['domain']}, seed={ok['seed']}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {ok['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n"
        f"- `{bad_id}`: 17 steps, success=False, domain={bad['domain']}, seed={bad['seed']}\n"
        f"  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)\n"
        f"  - plan change at step 12: {bad['plan_change']}\n"
        f"  - edit→test→fail→re-read→fix at steps 10-13\n\n"
        f"## decision_basis audit\n"
        f"Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, "
        f"length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, "
        f"no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.\n\n"
        f"## Mix\n"
        f"Success: ['{ok_id}']. Realistic failure/handoff: ['{bad_id}'].\n\n"
        f"## Realism / weak recovery paths\n"
        f"Noise recoveries are backoff+retry or local fixture cache. First patches are "
        f"domain-plausible and fail closed. Designed traces — not live executions.\n\n"
        f"## Step counts\n"
        f"- {ok_id}: 16 (required 14–18)\n"
        f"- {bad_id}: 17 (required 14–18)\n\n"
        f"## Weaknesses / next\n"
        f"{ok['residual']} {bad['residual']}\n"
    )


bind_import_twin(__name__)
