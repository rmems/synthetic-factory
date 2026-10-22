#!/usr/bin/env python3
"""Adapt the procedural mutator to the gate's proposal shape; the gate itself is unchanged.

``code_repair.planning.ProposalPlan`` draws seeded single-span sites from a pinned catalog.
Each becomes a :class:`GateProposal` carrying the site's byte span, original text and
replacement text, and then goes through the same :class:`Gate` as a model-backed proposal:
nothing here pre-judges a proposal, and the gate never looks at ``source``.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from . import vocabulary as cv
from ._contract import bind_import_twin
from .checks import is_count
from .proposal import GateProgram, GateProposal

if __name__.startswith("pipelines."):
    from ..code_repair import catalog as _catalog
    from ..code_repair import planning as _planning
    from ..code_repair import vocabulary as _repair_vocabulary
else:
    from code_repair import catalog as _catalog
    from code_repair import planning as _planning
    from code_repair import vocabulary as _repair_vocabulary

SOURCE = "procedural"
_TRAIN_SPLIT = "train"
EVAL_SPLITS = frozenset({"validation", "held_out"})

__all__ = [
    "EVAL_SPLITS", "SOURCE", "eval_program_ids", "load_catalog",
    "programs_from_catalog", "proposals_from_plan",
]


def _train_catalog(catalog: _catalog.Catalog) -> _catalog.Catalog:
    """Only train-split programs may feed the procedural mutator (#508)."""

    return replace(
        catalog,
        programs=tuple(program for program in catalog.programs if program.split == _TRAIN_SPLIT),
    )


def load_catalog(directory: Path) -> _catalog.Catalog:
    """The ``code_repair`` catalog; its own refusals become the gate's coded refusal."""

    try:
        return _catalog.load_catalog(Path(directory))
    except _repair_vocabulary.RepairRefusal as exc:
        raise cv.GateRefusal(cv.REFUSE_PROGRAM_INVALID, f"{directory}: {exc}") from exc


def eval_program_ids(catalog: _catalog.Catalog) -> frozenset[str]:
    """Validation and held-out program ids the verify step must never keep."""

    return frozenset(
        program.program_id for program in catalog.programs if program.split in EVAL_SPLITS
    )


def programs_from_catalog(catalog: _catalog.Catalog) -> dict[str, GateProgram]:
    """Every catalog program as a gate program, keyed by program id."""

    return {
        program.program_id: GateProgram(program.program_id, program.text, program.function)
        for program in catalog.programs
    }


def proposals_from_plan(
    catalog: _catalog.Catalog, seed: int, count: int, per_program_cap: int = 3,
) -> list[GateProposal]:
    """The procedural mutator's seeded proposals, in draw order, as gate proposals."""

    cv.refuse_when(not is_count(count) or count < 1, cv.REFUSE_INPUT_INVALID,
                   "count must be a positive integer")
    cv.refuse_when(not is_count(per_program_cap) or per_program_cap < 1, cv.REFUSE_INPUT_INVALID,
                   "per_program_cap must be a positive integer")
    plan = _planning.ProposalPlan(_train_catalog(catalog), seed, per_program_cap)
    return [
        GateProposal(
            proposal_id=proposal.record_id, program_id=proposal.program.program_id,
            replacement_text=proposal.mutation.site.replacement_text, source=SOURCE,
            original_text=proposal.mutation.site.original_text,
            start_byte=proposal.mutation.site.start, end_byte=proposal.mutation.site.end,
        )
        for proposal in plan.proposals(count)
    ]


bind_import_twin(__name__)
