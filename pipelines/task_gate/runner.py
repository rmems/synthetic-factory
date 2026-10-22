#!/usr/bin/env python3
"""Orchestrate one gate run: refuse early, decide every proposal, write a new destination.

Every refusal happens before any proposal is executed: an existing or raw-tree destination,
a missing or malformed denylist, an unreadable or malformed prior index, an out-of-domain
timeout, a harness that cannot tell a passing program from a failing one, no proposals,
or provenance that replaces computed denylist, prior-index, program, or harness evidence.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin
from .dedup_index import PriorIndex, load_prior
from .denylist import Denylist, load_denylist
from .gate import Gate, Harness, Rules
from .harness import SubprocessHarness
from .proposal import GateProgram, GateProposal, MalformedProposal
from .report import RunOutcome, check_destination, write_run

__all__ = ["GateRequest", "run"]


@dataclass(frozen=True)
class GateRequest:
    """Everything one run needs. ``denylist`` has no default: it is a required input."""

    programs: Mapping[str, GateProgram]
    proposals: Sequence[GateProposal | MalformedProposal]
    denylist: Denylist | Path | str | None
    out: Path
    prior_index_paths: Sequence[Path | str] = ()
    timeout_s: float = cv.DEFAULT_TIMEOUT_S
    provenance: Mapping[str, Any] = field(default_factory=dict)
    eval_program_ids: frozenset[str] = frozenset()


def _programs_digest(programs: Mapping[str, GateProgram]) -> str:
    digest = hashlib.sha256()
    for program_id in sorted(programs):
        program = programs[program_id]
        for part in (program_id, program.function, program.text):
            data = part.encode("utf-8")
            digest.update(len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def _loaded_denylist(request: GateRequest) -> Denylist:
    if isinstance(request.denylist, Denylist):
        return request.denylist
    return load_denylist(request.denylist)


def _loaded_prior(request: GateRequest) -> PriorIndex:
    return load_prior(request.prior_index_paths) if request.prior_index_paths else PriorIndex.empty()


_COMPUTED_EVIDENCE = ("denylist", "prior_indexes", "programs", "harness")


def _harness_evidence(harness: Harness) -> dict[str, Any]:
    describe = getattr(harness, "describe", None)
    if callable(describe):
        return describe()
    return {"protocol": cv.HARNESS_PROTOCOL}


def _evidence(request: GateRequest, rules: Rules, harness: Harness) -> dict[str, Any]:
    return {
        "denylist": {"sha256": rules.denylist.sha256, "entries": len(rules.denylist)},
        "prior_indexes": list(rules.prior.files),
        "programs": {"count": len(request.programs), "sha256": _programs_digest(request.programs)},
        "harness": _harness_evidence(harness),
    }


def _colliding_key(provenance: Mapping[str, Any]) -> str | None:
    for key in _COMPUTED_EVIDENCE:
        if key in provenance:
            return key
    return None


def _provenance(request: GateRequest) -> dict[str, Any]:
    """Caller provenance may add keys. A key the run computes itself is a refusal."""

    extra = dict(request.provenance)
    collision = _colliding_key(extra)
    cv.refuse_when(
        collision is not None, cv.REFUSE_INPUT_INVALID,
        f"provenance collides with computed evidence: {collision}",
    )
    return extra


def _meta(request: GateRequest, rules: Rules, harness: Harness) -> dict[str, Any]:
    return {**_evidence(request, rules, harness), **_provenance(request)}


def run(request: GateRequest, harness: Harness | None = None) -> dict[str, Any]:
    """Run the gate and return the summary that was written to ``summary.json``."""

    check_destination(Path(request.out))
    rules = Rules(
        _loaded_denylist(request), _loaded_prior(request), frozenset(request.eval_program_ids),
    )
    cv.refuse_when(not request.proposals, cv.REFUSE_NO_PROPOSALS, "no proposals to verify")
    cv.refuse_when(not request.programs, cv.REFUSE_PROGRAM_INVALID, "no programs")
    active = harness if harness is not None else SubprocessHarness(request.timeout_s)
    meta = _meta(request, rules, active)
    gate = Gate(request.programs, rules, active)
    decisions = gate.run(request.proposals)
    return write_run(Path(request.out), RunOutcome(decisions, gate.kept, rules.prior, meta))


bind_import_twin(__name__)
