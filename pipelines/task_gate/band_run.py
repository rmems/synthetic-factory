#!/usr/bin/env python3
"""Orchestrate one band run: refuse early, measure every kept task, write a new destination.

Refusals all happen before the solver is called: a missing or malformed contract, an existing
or raw-tree destination, an unreadable tasks file, no kept tasks, a catalog that does not
rebuild a kept task to its verified digest, or a harness that cannot tell pass from fail. The
contract is the only source of ``attempts_per_task`` and the band bounds.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

from . import band_tasks
from . import band_vocabulary as bv
from . import vocabulary as cv
from ._contract import bind_import_twin
from .band_contract import BandContract, load_contract
from .band_report import BandOutcome, BandRow, write_band_run
from .band_solver import BandTask, Scorer, Solver, attempt_all
from .checks import is_identifier
from .gate import Harness
from .harness import SubprocessHarness
from .proposal import GateProgram
from .report import check_destination

__all__ = ["BandRequest", "run"]


@dataclass(frozen=True)
class BandRequest:
    """Everything one run needs. ``contract`` has no default: it is a required input."""

    programs: Mapping[str, GateProgram]
    tasks_path: Path
    contract: BandContract | Path | str | None
    out: Path
    generator: str
    timeout_s: float = cv.DEFAULT_TIMEOUT_S


def _loaded_contract(request: BandRequest) -> BandContract:
    if isinstance(request.contract, BandContract):
        return request.contract
    return load_contract(request.contract)


class Prepared(NamedTuple):
    row: band_tasks.KeptTask
    task: BandTask
    program: GateProgram


def _measure(item: Prepared, request: BandRequest, parts: tuple[Solver, Harness, BandContract]) -> BandRow:
    solver, harness, contract = parts
    attempts = contract.attempts_per_task
    successes = attempt_all(solver, item.task, Scorer(item.program, harness), attempts)
    return BandRow(
        item.row, request.generator, attempts, successes, contract.classify(successes, attempts),
    )


def _selfchecked(harness: Harness) -> Harness:
    selfcheck = getattr(harness, "selfcheck", None)
    if callable(selfcheck):
        selfcheck()
    return harness


def _prepare(request: BandRequest, loaded: band_tasks.LoadedTasks) -> list[Prepared]:
    """Rebuild every kept task first, so a catalog mismatch refuses before any attempt runs."""

    cv.refuse_when(not loaded.kept, bv.REFUSE_NO_TASKS, "the tasks file has no kept task")
    return [Prepared(row, *band_tasks.rebuild(row, request.programs)) for row in loaded.kept]


def run(request: BandRequest, solver: Solver, harness: Harness | None = None) -> dict[str, Any]:
    """Run the band stage and return the summary that was written to ``band-summary.json``."""

    check_destination(Path(request.out))
    cv.refuse_when(
        not is_identifier(request.generator), bv.REFUSE_REQUEST_INVALID, "generator must be named",
    )
    contract = _loaded_contract(request)
    loaded = band_tasks.load_kept(request.tasks_path)
    prepared = _prepare(request, loaded)
    active = _selfchecked(harness if harness is not None else SubprocessHarness(request.timeout_s))
    rows = [_measure(item, request, (solver, active, contract)) for item in prepared]
    meta = {
        "tasks": {"sha256": loaded.sha256, "skipped_not_kept": loaded.skipped},
        "generator": request.generator,
    }
    return write_band_run(Path(request.out), BandOutcome(rows, contract, meta))


bind_import_twin(__name__)
