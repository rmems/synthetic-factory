#!/usr/bin/env python3
"""Emit code-family prior leftover3 preference pairs into a new destination.

``pair`` is the divergence-point DPO constructor AST-extracted from
``crp-mill-r432`` (PR numbering anchored at ``PAIR_FIRST_ROUND``). The
catalog supplies the prior leftover3 plants, including ``noun``. Writers
refuse an existing destination and any path that names or aliases
``outputs/raw/``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import catalog as cat
from ._contract import (
    FINDING_CRITIQUE_TOO_SHORT,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    bind_import_twin,
    dumps_exact_json,
    is_under_raw,
    refuse,
    refuse_when,
)

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


def _check_destination(out_dir: Path) -> None:
    refuse_when(
        is_under_raw(out_dir),
        FINDING_DESTINATION_UNDER_RAW,
        f"{out_dir} names or aliases the raw tree",
    )
    refuse_when(out_dir.exists(), FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")


@dataclass(frozen=True)
class _CreatedFile:
    """A file this invocation created, addressed by its pinned parent."""

    parent_fd: int
    name: str


def _opened_path(fd: int, fallback: Path) -> Path:
    try:
        return Path(os.readlink(f"/proc/self/fd/{fd}"))
    except OSError:
        return fallback


def _refuse_raw_path(path: Path, origin: Path) -> None:
    refuse_when(
        is_under_raw(path),
        FINDING_DESTINATION_UNDER_RAW,
        f"{origin} names or aliases the raw tree",
    )


def _open_destination_parent(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    return os.open(path.parent, flags)


def _refuse_opened_parent(parent_fd: int, destination: Path) -> None:
    opened = _opened_path(parent_fd, destination.parent)
    _refuse_raw_path(opened, destination)
    _refuse_raw_path(opened / destination.name, destination)


def _create_exclusive_file(
    parent_fd: int, name: str, payload: str, created: list[_CreatedFile]
) -> None:
    descriptor = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
        dir_fd=parent_fd,
    )
    created.append(_CreatedFile(parent_fd, name))
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _fsync_destination(dest_fd: int, parent_fd: int) -> None:
    os.fsync(dest_fd)
    os.fsync(parent_fd)


def _unlink_created(created: list[_CreatedFile]) -> None:
    for entry in created:
        try:
            os.unlink(entry.name, dir_fd=entry.parent_fd)
        except FileNotFoundError:
            pass


def _rmdir_created(parent_fd: int, name: str) -> None:
    try:
        os.rmdir(name, dir_fd=parent_fd)
    except OSError:
        pass


def _write_run(out_dir: Path, files: tuple[tuple[str, str], ...]) -> None:
    """Create ``out_dir`` and its files exclusively; unlink a partial tree."""

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    parent_fd = _open_destination_parent(out_dir)
    dest_fd = -1
    created: list[_CreatedFile] = []
    created_dir = False
    try:
        _refuse_opened_parent(parent_fd, out_dir)
        try:
            os.mkdir(out_dir.name, dir_fd=parent_fd)
        except FileExistsError:
            refuse(FINDING_DESTINATION_EXISTS, f"{out_dir} already exists")
        created_dir = True
        dest_fd = os.open(
            out_dir.name,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        _refuse_raw_path(_opened_path(dest_fd, out_dir), out_dir)
        for name, payload in files:
            _create_exclusive_file(dest_fd, name, payload, created)
        _fsync_destination(dest_fd, parent_fd)
    except BaseException:
        _unlink_created(created)
        if created_dir:
            _rmdir_created(parent_fd, out_dir.name)
        raise
    finally:
        if dest_fd >= 0:
            os.close(dest_fd)
        os.close(parent_fd)


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


def _prefix(plant: cat.Plant, pr: int) -> list[dict[str, Any]]:
    repo, core, boot, test = plant.repo, plant.core, plant.boot, plant.test
    feat = plant.title.split(":", 1)[-1].strip()
    return [
        _step(
            1,
            (
                f"Observation: operator asked for a merge-blocking review of "
                f"{repo} PR {pr} if the change has a real defect."
            ),
            _bash(f"gh pr view {pr} --repo {repo} --json number,title,files,additions,headRefName"),
            (
                f'designed: {{"number":{pr},"title":"{plant.title}","additions":{8},'
                f'"files":[{{"path": "{core}"}}, {{"path": "{boot}"}}, '
                f'{{"path": "{test}"}}],"headRefName":"feat/{plant.slug}"}}'
            ),
            "Inventory the PR before commenting.",
        ),
        _step(
            2,
            "Observation: core file named in the files list. Diff that hunk.",
            _bash(f"gh pr diff {pr} --repo {repo} -- {core}"),
            f"designed: +{feat}  # {plant.defect}",
            "Read the implementation next, not just the hunk.",
        ),
        _step(
            3,
            "Observation: diff shows the suspect pattern. Read the full function.",
            {"name": "read_file", "args": {"path": core}},
            (
                f"designed: {plant.defect}. this is {plant.family}, not the "
                f"{plant.notfam}. serial tests never cover {plant.missing}."
            ),
            "Confirm callers and tests before verdict.",
        ),
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


def _chosen_tail(plant: cat.Plant, pr: int, rid: int) -> list[dict[str, Any]]:
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
            f"designed: HTTP 200 review {rid} event=REQUEST_CHANGES.",
            "Blocking review names the defect, the missing test, and the fix shape.",
        ),
        _step(
            9,
            "Observation: review posted. Pin an inline on the exact line.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/comments -f path={core} -F line={line} "
                f"-f side=RIGHT -f body=\"issue: this {plant.defect}\""
            ),
            f"designed: HTTP 201 comment c-{pr}-{line} on {core}:{line}.",
            "Inline is on the defect, not on naming.",
        ),
        _step(
            10,
            "Observation: attach a falsifiable test sketch so the block is not taste.",
            {
                "name": "write_file",
                "args": {
                    "path": f"/tmp/pr{pr}-blocking-repro.txt",
                    "content": (
                        f"issue (blocking): {plant.defect}. {plant.fix}. "
                        f"Add a test that {plant.missing}. Do not merge.\n"
                    ),
                },
            },
            f"designed write: /tmp/pr{pr}-blocking-repro.txt. not committed; linked from the review.",
            "The block cites a failing case, not a formatter.",
        ),
        _step(
            11,
            "Observation: confirm CHANGES_REQUESTED and the inline path:line.",
            _bash(
                f"gh pr view {pr} --repo {repo} --json reviewDecision && "
                f"gh api repos/{repo}/pulls/{pr}/comments --jq '.[].path'"
            ),
            f"designed: reviewDecision=CHANGES_REQUESTED; inline on {core}.",
            "Merge is blocked on the defect.",
        ),
        _step(
            12,
            "Observation: confirm no accidental APPROVE was also posted.",
            _bash(f"gh api repos/{repo}/pulls/{pr}/reviews --jq '.[] | {{state,event:.event}}'"),
            "designed: one review REQUEST_CHANGES, zero APPROVE.",
            "Verdict is a single blocking review.",
        ),
        _step(
            13,
            "Observation: final state check — mergeable is blocked.",
            _bash(f"gh pr view {pr} --repo {repo} --json mergeable,reviewDecision"),
            "designed: mergeable=CONFLICTING_OR_BLOCKED reviewDecision=CHANGES_REQUESTED.",
            "Done. Defect named, merge blocked.",
        ),
    ]


def _rejected_tail(plant: cat.Plant, pr: int) -> list[dict[str, Any]]:
    repo, core, test, line, nit = plant.repo, plant.core, plant.test, plant.line, plant.nit
    return [
        _step(
            8,
            "Plan: the change reads cleanly. Leave a nit and approve.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/comments -f path={core} -F line={line} "
                f"-f side=RIGHT -f body=\"nit: {nit} could be named {nit}Ident.\""
            ),
            f"designed: HTTP 201 nit c-{pr}-nit on {core}. no mention of the defect.",
            "Comment is a nit. The defect is untouched.",
        ),
        _step(
            9,
            "Observation: add a second nit so the author has polish work.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/comments -f path={test} -F line=1 "
                f"-f side=RIGHT -f body='nit: add a blank line between tests; "
                f"also consider a more descriptive test name.'"
            ),
            f"designed: HTTP 201 nit c-{pr}-teststyle on {test}. still no defect mention.",
            "Second nit is formatting. Race/authz still unmentioned.",
        ),
        _step(
            10,
            "Observation: nits posted. Approve because the serial suite is green.",
            _bash(
                f"gh api repos/{repo}/pulls/{pr}/reviews -f event=APPROVE "
                f"-f body=\"LGTM. serial tests pass. nits only.\""
            ),
            "designed: HTTP 200 event=APPROVE. reviewDecision=APPROVED.",
            "Approved past the defect.",
        ),
        _step(
            11,
            "Observation: approved. Do not add a failing test for the defect.",
            _bash(f"gh pr checks {pr} --repo {repo}"),
            "designed: serial tests passed. mergeable=MERGEABLE.",
            "Green serial tests treated as proof.",
        ),
        _step(
            12,
            "Observation: confirm mergeable and do not request changes.",
            _bash(f"gh pr view {pr} --repo {repo} --json mergeable,reviewDecision"),
            "designed: mergeable=MERGEABLE reviewDecision=APPROVED. zero REQUEST_CHANGES.",
            "Rejected policy: nits + LGTM.",
        ),
    ]


def pair(plant: cat.Plant, round_n: int, slot: int) -> dict[str, Any]:
    """One prior leftover3 preference pair. Catalog ``noun`` is in ``meta``."""

    pr = 1900 + (round_n - cat.PAIR_FIRST_ROUND) * 3 + slot
    rid = 900000 + pr
    pq = round(0.86 + (slot * 0.02) + ((round_n % 5) * 0.002), 3)
    vr = round(0.87 + (slot * 0.01) + ((round_n % 7) * 0.001), 3)
    ds = round(0.88 + (slot * 0.015), 3)
    margin = round(0.72 + (slot * 0.03) + ((round_n % 4) * 0.01), 3)
    feat = plant.title.split(":", 1)[-1].strip()
    prefix = _prefix(plant, pr)
    prefix[0]["observation"] = (
        f'designed: {{"number":{pr},"title":"{plant.title}","additions":{8 + slot},'
        f'"files":[{{"path": "{plant.core}"}}, {{"path": "{plant.boot}"}}, '
        f'{{"path": "{plant.test}"}}],"headRefName":"feat/{plant.slug}"}}'
    )
    chosen_steps = prefix + _chosen_tail(plant, pr, rid)
    rejected_steps = prefix + _rejected_tail(plant, pr)
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
            "reward": {
                "success": True,
                "process_quality": pq,
                "verify_rigor": vr,
                "defect_specificity": ds,
            },
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
        "meta": {
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
        },
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
