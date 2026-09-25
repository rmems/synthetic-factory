#!/usr/bin/env python3
"""Shared review preference step sequences for code-review and code-leftover generators.

Consolidates the chosen and rejected review tail steps across ``crp`` and
``code_leftover3`` generators so review steps are defined once.
"""

from __future__ import annotations

import sys
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("code_review_preference_tail")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "code_review_preference_tail"
    )

__all__ = [
    "chosen_tail",
    "rejected_tail",
]


def _step(
    n: int,
    decision_basis: str,
    tool_call: dict[str, Any],
    audit: tuple[str, str],
) -> dict[str, Any]:
    return {
        "n": n,
        "decision_basis": decision_basis,
        "tool_call": tool_call,
        "observation": audit[0],
        "reflection": audit[1],
    }


def _bash(cmd: str) -> dict[str, Any]:
    return {"name": "bash", "args": {"command": cmd}}


def _step_10_repro(plant: Any, pr: int) -> dict[str, Any]:
    repro_path = f".synthetic-factory/repros/pr{pr}-blocking-repro.txt"
    return _step(
        10,
        "Observation: attach a falsifiable test sketch so the block is not taste.",
        {
            "name": "write_file",
            "args": {
                "path": repro_path,
                "content": (
                    f"issue (blocking): {plant.defect}. {plant.fix}. "
                    f"Add a test that {plant.missing}. Do not merge.\n"
                ),
            },
        },
        (
            f"designed write: {repro_path}. not committed; linked from the review.",
            "The block cites a failing case, not a formatter.",
        ),
    )


def _chosen_blocking_steps(plant: Any, pr: int, rid: int) -> list[dict[str, Any]]:
    repo, core, line = plant.repo, plant.core, plant.line
    return [
        _step(
            8,
            (
                "Observation: the defect is load-bearing and untested. "
                "Post issue (blocking) REQUEST_CHANGES."
            ),
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/reviews -f event=REQUEST_CHANGES -f body=\""
                f"issue (blocking): {plant.defect}. {plant.fix}. "
                f"Add a test that {plant.missing}. Do not merge.\""
            ),
            (
                f"designed: HTTP 200 review {rid} event=REQUEST_CHANGES.",
                "Blocking review names the defect, the missing test, and the fix shape.",
            ),
        ),
        _step(
            9,
            "Observation: review posted. Pin an inline on the exact line.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/comments -f path={core} -F line={line} "
                f"-f side=RIGHT -f body=\"issue: this {plant.defect}\""
            ),
            (
                f"designed: HTTP 201 comment c-{pr}-{line} on {core}:{line}.",
                "Inline is on the defect, not on naming.",
            ),
        ),
        _step_10_repro(plant, pr),
    ]


def _chosen_verification_steps(plant: Any, pr: int) -> list[dict[str, Any]]:
    repo, core = plant.repo, plant.core
    return [
        _step(
            11,
            "Observation: confirm CHANGES_REQUESTED and the inline path:line.",
            _bash(
                f"gh pr view {pr} --repo {repo} --json reviewDecision && "
                f"gh api repos/{repo}/pulls/{pr}/comments --jq '.[].path'"
            ),
            (
                f"designed: reviewDecision=CHANGES_REQUESTED; inline on {core}.",
                "Merge is blocked on the defect.",
            ),
        ),
        _step(
            12,
            "Observation: confirm no accidental APPROVE was also posted.",
            _bash(f"gh api repos/{repo}/pulls/{pr}/reviews --jq '.[] | {{state,event:.event}}'"),
            (
                "designed: one review REQUEST_CHANGES, zero APPROVE.",
                "Verdict is a single blocking review.",
            ),
        ),
        _step(
            13,
            "Observation: final state check — mergeable is blocked.",
            _bash(f"gh pr view {pr} --repo {repo} --json mergeable,reviewDecision"),
            (
                "designed: mergeable=CONFLICTING_OR_BLOCKED reviewDecision=CHANGES_REQUESTED.",
                "Done. Defect named, merge blocked.",
            ),
        ),
    ]


def chosen_tail(plant: Any, pr: int, rid: int) -> list[dict[str, Any]]:
    """Return the merge-blocking review steps identifying a genuine defect."""
    return _chosen_blocking_steps(plant, pr, rid) + _chosen_verification_steps(plant, pr)


def _rejected_nit_steps(plant: Any, pr: int) -> list[dict[str, Any]]:
    repo, core, test, line, nit = plant.repo, plant.core, plant.test, plant.line, plant.nit
    return [
        _step(
            8,
            "Plan: the change reads cleanly. Leave a nit and approve.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/comments -f path={core} -F line={line} "
                f"-f side=RIGHT -f body=\"nit: {nit} could be named {nit}Ident.\""
            ),
            (
                f"designed: HTTP 201 nit c-{pr}-nit on {core}. no mention of the defect.",
                "Comment is a nit. The defect is untouched.",
            ),
        ),
        _step(
            9,
            "Observation: add a second nit so the author has polish work.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/comments -f path={test} -F line=1 "
                f"-f side=RIGHT -f body='nit: add a blank line between tests; "
                f"also consider a more descriptive test name.'"
            ),
            (
                f"designed: HTTP 201 nit c-{pr}-teststyle on {test}. still no defect mention.",
                "Second nit is formatting. Race/authz still unmentioned.",
            ),
        ),
    ]


def _rejected_approval_steps(plant: Any, pr: int) -> list[dict[str, Any]]:
    repo = plant.repo
    return [
        _step(
            10,
            "Observation: nits posted. Approve because the serial suite is green.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/reviews -f event=APPROVE "
                f"-f body=\"LGTM. serial tests pass. nits only.\""
            ),
            (
                "designed: HTTP 200 event=APPROVE. reviewDecision=APPROVED.",
                "Approved past the defect.",
            ),
        ),
        _step(
            11,
            "Observation: approved. Do not add a failing test for the defect.",
            _bash(f"gh pr checks {pr} --repo {repo}"),
            (
                "designed: serial tests passed. mergeable=MERGEABLE.",
                "Green serial tests treated as proof.",
            ),
        ),
        _step(
            12,
            "Observation: confirm mergeable and do not request changes.",
            _bash(f"gh pr view {pr} --repo {repo} --json mergeable,reviewDecision"),
            (
                "designed: mergeable=MERGEABLE reviewDecision=APPROVED. zero REQUEST_CHANGES.",
                "Rejected policy: nits + LGTM.",
            ),
        ),
    ]


def rejected_tail(plant: Any, pr: int) -> list[dict[str, Any]]:
    """Return the approving review steps that overlook the load-bearing defect."""
    return _rejected_nit_steps(plant, pr) + _rejected_approval_steps(plant, pr)


if __package__:
    _expose_package_sibling(__name__)
