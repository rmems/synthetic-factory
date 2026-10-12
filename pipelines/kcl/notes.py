"""NOTES text for one KCL leftover pair: coverage, seeds, step counts and the
``decision_basis`` audit line. A NOTES text without its coverage line is refused.
"""

from __future__ import annotations

from collections.abc import Mapping

from ._contract import (
    FACTORY,
    FINDING_USAGE,
    GENERATOR,
    HANDOFF_STEPS,
    SUCCESS_STEPS,
    bind_import_twin,
    refuse_when,
)
from ._steps import BASIS_LIMIT

__all__ = ["notes_markdown"]


def notes_markdown(
    spec: Mapping[str, str],
    ok_id: str,
    bad_id: str,
    round_n: int,
) -> str:
    coverage = 82 + (round_n % 7)
    notes = (
        f"# NOTES-r{round_n} {FACTORY}\n\n"
        f"Novel coverage: {coverage}%\n\n"
        f"Quota 2. Unique CrashLoopBackOff pair. New: {spec['new_vs']}. "
        f"Plant `{spec['plant']}`.\n\n"
        f"| id | seed | clean-plan then fail | leftover | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {ok_id} | {spec['seed']} | kubeconform 0; apply --wait fail | "
        f"wrong first hide then plan change | success 2/2 pytest 6/6 |\n"
        f"| {bad_id} | {spec['n2']} | kubeconform 0; --force mixed | "
        f"leftover on n2; SSA spec only | partial 1/2 handoff |\n\n"
        f"## Step counts\n"
        f"- ep1: {SUCCESS_STEPS}. Clean template 5; apply fail 6,8; plan change 9; "
        f"verify 12–16.\n"
        f"- ep2: {HANDOFF_STEPS}. Clean template 5; apply fail 6–8; plan change 9; "
        f"leftover 11–18.\n\n"
        f"## decision_basis audit\n"
        f"Plan:/Observation:/Reflection:/Tool call: ≤{BASIS_LIMIT}. No hidden CoT. "
        f"No spike_events. Generator {GENERATOR}. Invented plant `{spec['plant']}`.\n"
    )
    refuse_when("Novel coverage:" not in notes, FINDING_USAGE, "NOTES missing Novel coverage")
    return notes


bind_import_twin(__name__)
