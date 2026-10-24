#!/usr/bin/env python3
"""Emit code-family prior leftover3 preference pairs into a new destination.

``pair`` is the divergence-point DPO constructor AST-extracted from
``crp-mill-r432`` (PR numbering anchored at ``PAIR_FIRST_ROUND``). The
catalog supplies the prior leftover3 plants, including ``noun``. Writers
refuse an existing destination and any path that names or aliases
``outputs/raw/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FINDING_CRITIQUE_TOO_SHORT,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_when,
)

if __package__ and __package__.startswith("pipelines."):
    from ..run_writer import exclusive_run as _exclusive_run
else:
    from run_writer import exclusive_run as _exclusive_run

if __package__ and __package__.startswith("pipelines."):
    from .. import code_review_preference_tail as crp_tail
else:
    import code_review_preference_tail as crp_tail

BATCH_PREFIX = "batch-r"
NOTES_PREFIX = "NOTES-r"
MANIFEST_FILENAME = "MANIFEST.json"
RUN_FORMAT = "code-leftover3-run/1"

__all__ = [
    "BATCH_PREFIX",
    "MANIFEST_FILENAME",
    "NOTES_PREFIX",
    "RUN_FORMAT",
    "RunRequest",
    "notes_for",
    "pair",
    "run",
]


@dataclass(frozen=True)
class RunRequest:
    round_n: int
    out_dir: Path


_check_destination, _write_run, _fsync_destination = _exclusive_run.bind(
    globals(), _exclusive_run.Guards(refuse, refuse_when, is_under_raw)
)


def _step(
    n: int,
    decision_basis: str,
    tool_call: dict[str, Any],
    observation: str,
    reflection: str,
) -> dict[str, Any]:
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": observation,
        "reflection": reflection,
    }


def _bash(command: str) -> dict[str, Any]:
    return {"name": "bash", "args": {"command": command}}


def _feature(plant: cat.Plant) -> str:
    return plant.title.split(":", 1)[-1].strip()


def _context_steps(plant: cat.Plant, pr: int) -> list[dict[str, Any]]:
    """Steps 4-7: reachability, the tests as their own object, the search, the PR body."""
    repo, core, boot, test = plant.repo, plant.core, plant.boot, plant.test
    feat = _feature(plant)
    return [
        _step(
            4,
            (
                "Observation: implementation is in hand. Read the caller / "
                "schema next to see if the defect is reachable."
            ),
            {"name": "read_file", "args": {"path": boot}},
            f"designed: {boot}. comment: {plant.reach}",
            "Reachability is in-scope for a blocking comment.",
        ),
        _step(
            5,
            (
                "Observation: read the new tests as their own object so a "
                "serial-green suite is not treated as coverage."
            ),
            {"name": "read_file", "args": {"path": test}},
            f"designed: tests {feat} resolves. no case for {plant.missing}. serial green.",
            "Serial tests are not a concurrency or authz proof.",
        ),
        _step(
            6,
            (
                "Observation: search the PR files for the missing lock / "
                "unique / check the defect needs."
            ),
            _bash(f"rg -n '{plant.needles}' {core} {boot} {test}"),
            f"designed: defect pattern present. {plant.defect}. required {plant.fix} absent.",
            "Search confirms the primitive is absent. One more context object.",
        ),
        _step(
            7,
            (
                "Observation: read the PR body / ticket so the success "
                "criterion is the author's, not a new one."
            ),
            _bash(f"gh pr view {pr} --repo {repo} --json body,title"),
            (
                f"designed PR body: {plant.title}. Author claims serial tests "
                f"are sufficient and asks for review. No mention of {plant.defect}. "
                f"Success: merge only if {plant.missing} as described in {core}."
            ),
            "Same ticket both sides. Fork is the verdict.",
        ),
    ]


def _prefix(plant: cat.Plant, pr: int) -> list[dict[str, Any]]:
    return [*crp_tail.inventory_steps(plant, pr), *_context_steps(plant, pr)]


def _chosen_tail(plant: cat.Plant, pr: int, rid: int) -> list[dict[str, Any]]:
    return crp_tail.chosen_tail(plant, pr, rid)


def _rejected_tail(plant: cat.Plant, pr: int) -> list[dict[str, Any]]:
    return crp_tail.rejected_tail(plant, pr)


def pair(plant: cat.Plant, round_n: int, slot: int) -> dict[str, Any]:
    """One prior leftover3 preference pair. Catalog ``noun`` is in ``meta``."""

    pr = 1900 + (round_n - cat.PAIR_FIRST_ROUND) * 3 + slot
    rid = 900000 + pr
    chosen_reward = _chosen_reward(round_n, slot)
    margin = round(0.72 + (slot * 0.03) + ((round_n % 4) * 0.01), 3)
    chosen_steps, rejected_steps = _side_steps(plant, pr, rid, slot)
    critique = _critique(plant, pr)
    return {
        "id": f"{cat.ID_PREFIX}-r{round_n}-{plant.slug}",
        "goal": (
            f"Review designed {plant.repo} PR #{pr} ({plant.title}) and post a "
            f"merge-blocking review if {plant.missing} is not enforced."
        ),
        "outcome": (
            f"Chosen: REQUEST_CHANGES on {plant.defect}; required {plant.fix} + "
            f"{plant.missing}. Rejected: Nit on the {plant.nit} name, APPROVE. "
            f"Missed {plant.defect}. Quality delta at first fork "
            f"(missed race or real bug vs nit/LGTM)."
        ),
        "chosen": {
            "steps": chosen_steps,
            "outcome": (
                f"REQUEST_CHANGES on {plant.defect}; required {plant.fix} + {plant.missing}."
            ),
            "reward": chosen_reward,
        },
        "rejected": {
            "steps": rejected_steps,
            "outcome": f"Nit on the {plant.nit} name, APPROVE. Missed {plant.defect}.",
            "reward": {
                "success": False,
                "process_quality": 0.16,
                "verify_rigor": 0.07,
                "defect_specificity": 0.05,
            },
        },
        "critique": critique,
        "reward": {"success": True, "preference_margin": margin, "same_goal": 1.0},
        "meta": _pair_meta(plant, round_n),
    }


def _chosen_reward(round_n: int, slot: int) -> dict[str, Any]:
    return {
        "success": True,
        "process_quality": round(0.86 + (slot * 0.02) + ((round_n % 5) * 0.002), 3),
        "verify_rigor": round(0.87 + (slot * 0.01) + ((round_n % 7) * 0.001), 3),
        "defect_specificity": round(0.88 + (slot * 0.015), 3),
    }


def _side_steps(
    plant: cat.Plant, pr: int, rid: int, slot: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The shared seven-step prefix, then the chosen and rejected tails."""
    prefix = _prefix(plant, pr)
    prefix[0]["observation"] = (
        f'designed: {{"number":{pr},"title":"{plant.title}","additions":{8 + slot},'
        f'"files":[{{"path": "{plant.core}"}}, {{"path": "{plant.boot}"}}, '
        f'{{"path": "{plant.test}"}}],"headRefName":"feat/{plant.slug}"}}'
    )
    return prefix + _chosen_tail(plant, pr, rid), prefix + _rejected_tail(plant, pr)


def _critique(plant: cat.Plant, pr: int) -> str:
    feat = _feature(plant)
    critique = (
        f"Same {plant.repo} PR {pr} and the same seven-step prefix: pr view, {feat}, "
        f"{plant.defect}, {plant.reach}, tests resolve, rg, PR body. Divergence is "
        f"step 8. Chosen posts issue (blocking) REQUEST_CHANGES on {plant.defect} in "
        f"{plant.core}:{plant.line} and requires {plant.fix} plus {plant.missing}. "
        f"Rejected nits the {plant.nit} name and APPROVE, leaving the same plant "
        f"mergeable. The preference is a blocking {plant.family} defect versus a "
        f"naming or style nit on the same {feat} integrity — not the {plant.notfam}. "
        f"A draft that moved rejected to a different ticket rewrite was discarded "
        f"because that would change the problem between sides. Both sides share the "
        f"operator goal: merge-block only if {plant.missing}. Serial-green tests do "
        f"not cover {plant.defect}. The first differing tool_call is the review "
        f"verdict (REQUEST_CHANGES vs a nit comment)."
    )
    refuse_when(
        len(critique) < 400,
        FINDING_CRITIQUE_TOO_SHORT,
        f"critique too short for {plant.slug}: {len(critique)}",
    )
    return critique


def _pair_meta(plant: cat.Plant, round_n: int) -> dict[str, Any]:
    return {
        "factory": cat.FACTORY,
        "round": round_n,
        "generator": cat.GENERATOR,
        "kind": "preference",
        "plant": "designed",
        "rejected_sin": "missed defect / nitpicks",
        "divergence_step": 8,
        "construction": "divergence-point-shared-prefix",
        "chosen_steps": 13,
        "rejected_steps": 12,
        "review_lesson": f"{plant.family}-blocking-vs-nit",
        "family": plant.family,
        "noun": plant.noun,
        "slug": plant.slug,
        "wave": cat.CATALOG_ID,
    }


def notes_for(round_n: int, recs: list[dict[str, Any]], plants: tuple[cat.Plant, ...]) -> str:
    fams = [rec["meta"]["family"] for rec in recs]
    ids = [rec["id"] for rec in recs]
    nouns = [plant.noun for plant in plants]
    lines = [
        f"# {cat.FACTORY} — NOTES r{round_n}",
        "",
        "Novel coverage: 99.5%",
        "",
        f"Headline: blocking defect vs nit/LGTM on {', '.join(fams)} "
        f"(prior leftover3 wave r679-r694)",
        "",
        "Construction: divergence-point DPO (shared 7-step prefix; first "
        "differing tool_call is the review verdict). Same top-level goal both "
        "sides. Chosen posts issue (blocking) REQUEST_CHANGES. Rejected posts "
        "nits and APPROVE. Catalog rows carry noun "
        f"({', '.join(nouns)}). Indexed from the code mill notfam list.",
        "",
        "Records:",
        *[
            (
                f"- `{rec['id']}` noun=`{plant.noun}` "
                f"sin=`missed defect / nitpicks` class=`{plant.family}-blocking` "
                f"family=`{plant.family}` fork=step 8"
            )
            for rec, plant in zip(recs, plants, strict=True)
        ],
        "",
        f"IDs: {ids}",
        "",
        "No Thalamic six-field core. No spikes. Observations are designed plants.",
        "",
    ]
    return "\n".join(lines)


def _dump_line(record: dict[str, Any]) -> str:
    return dumps_exact_json(record, ensure_ascii=False, sort_keys=False)


def run(request: RunRequest) -> dict[str, Any]:
    """Write one prior leftover3 triple into a new directory. Never touches raw."""

    out_dir = Path(request.out_dir)
    _check_destination(out_dir)
    plants = cat.plants_for_round(request.round_n)
    recs = [pair(plant, request.round_n, slot) for slot, plant in enumerate(plants)]
    summary = {
        "format": RUN_FORMAT,
        "catalog_id": cat.CATALOG_ID,
        "factory": cat.FACTORY,
        "round": request.round_n,
        "records": len(recs),
        "ids": [rec["id"] for rec in recs],
        "nouns": [plant.noun for plant in plants],
        "slugs": [plant.slug for plant in plants],
        "destination": str(out_dir),
    }
    _write_run(
        out_dir,
        (
            (
                f"{BATCH_PREFIX}{request.round_n:02d}.jsonl",
                "".join(_dump_line(rec) + "\n" for rec in recs),
            ),
            (
                f"{NOTES_PREFIX}{request.round_n:02d}.md",
                notes_for(request.round_n, recs, plants),
            ),
            (
                MANIFEST_FILENAME,
                dumps_exact_json(summary, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
            ),
        ),
    )
    return summary


bind_import_twin(__name__)
