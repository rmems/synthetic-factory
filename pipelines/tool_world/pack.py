#!/usr/bin/env python3
"""World packs: the pinned, project-authored data a tool-world task runs on.

A pack directory holds ``PACK.json`` (identity, surfaces, license evidence)
and member directories: ``files/`` (the workspace tree), ``tests/`` (declared
suites), ``servers/`` (simulated MCP servers), ``pages/`` (a static site),
``workers/`` (scripted delegates), and ``tasks/`` (task specs). The pack digest
covers every member byte, ``PACK.json`` included, so a catalog pin binds the
exact data a record was generated from. Nothing in a pack is executed, and
everything the loader can check is refused here rather than mid-run.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import faults, predicates, records
from . import vocabulary as cv
from ._contract import (
    bind_import_twin,
    contains_hidden_reasoning_key,
    load_strict_json,
    sha256_bytes,
    sha256_canonical,
    terminal_outcome_agrees,
)

__all__ = ["Action", "Pack", "Task", "action_from_row", "load_pack", "pack_digest"]

Action = faults.Action
action_from_row = faults.action_from_row

PACK_FILENAME = "PACK.json"
_MEMBER_DIRS = ("files", "tests", "servers", "pages", "workers", "tasks")
_PACK_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TASK_ID = re.compile(r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$")


@dataclass(frozen=True)
class Task:
    task_id: str
    factory: str
    surface: str
    surfaces: tuple[str, ...]
    title: str
    goal: str
    max_steps: int
    public_predicates: tuple[tuple[str, Mapping[str, Any]], ...]
    hidden_predicates: tuple[tuple[str, Mapping[str, Any]], ...]
    gold: tuple[Action, ...]
    faults: tuple[faults.FaultSpec, ...]
    perturbations: tuple[str, ...]
    spec_sha256: str


@dataclass(frozen=True)
class Pack:
    pack_id: str
    directory: Path
    surfaces: tuple[str, ...]
    license: Mapping[str, Any]
    files: Mapping[str, str]
    tests: Mapping[str, Any]
    servers: Mapping[str, Any]
    site: Mapping[str, Any] | None
    pages: Mapping[str, str]
    workers: Mapping[str, Any]
    tasks: tuple[Task, ...]
    pack_sha256: str

    def task(self, task_id: str) -> Task:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        cv.refuse(cv.FINDING_TASK_NOT_FOUND, f"task {task_id!r} is not in pack {self.pack_id}")


def pack_digest(directory: Path) -> str:
    """sha256 over ``relative_path:sha256(bytes)`` rows of every file under the pack."""
    rows = []
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            rows.append(
                f"{path.relative_to(directory).as_posix()}:{sha256_bytes(path.read_bytes())}"
            )
    return sha256_bytes("\n".join(rows).encode("utf-8"))


def _read_text(path: Path, where: str) -> str:
    cv.refuse_when(
        not path.is_file(), cv.FINDING_PACK_FILE_MISSING, f"{where}: missing {path.name}"
    )
    payload = path.read_bytes()
    cv.refuse_when(
        len(payload) > cv.MAX_PACK_MEMBER_BYTES,
        cv.FINDING_PACK_MEMBER_INVALID,
        f"{where}: member exceeds {cv.MAX_PACK_MEMBER_BYTES} bytes",
    )
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        cv.refuse(
            cv.FINDING_PACK_MEMBER_INVALID, f"{where}: {path.name} is not UTF-8 ({exc.reason})"
        )


def _read_json(path: Path, where: str) -> Any:
    text = _read_text(path, where)
    try:
        return load_strict_json(text)
    except ValueError as exc:
        cv.refuse(
            cv.FINDING_PACK_MEMBER_INVALID, f"{where}: {path.name} is not strict JSON ({exc})"
        )


def _refuse_hidden_keys(value: Any, where: str, code: str) -> None:
    cv.refuse_when(
        contains_hidden_reasoning_key(value), code, f"{where}: carries a hidden-reasoning key"
    )


def _json_members(directory: Path, where: str) -> dict[str, Any]:
    """Every ``*.json`` member by stem; none may carry a hidden-reasoning key."""
    if not directory.is_dir():
        return {}
    members = {}
    for path in sorted(directory.glob("*.json")):
        label = f"{where}/{path.name}"
        members[path.stem] = _read_json(path, label)
        _refuse_hidden_keys(members[path.stem], label, cv.FINDING_PACK_MEMBER_INVALID)
    return members


def _file_members(directory: Path, where: str) -> dict[str, str]:
    if not directory.is_dir():
        return {}
    members = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            members[path.relative_to(directory).as_posix()] = _read_text(path, where)
    return members


def _require_str(row: Mapping[str, Any], key: str, where: str) -> str:
    value = row.get(key)
    cv.refuse_when(
        not isinstance(value, str) or not value.strip(),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: {key} must be a nonempty string",
    )
    return value


def _predicates(
    rows: Any, where: str, surfaces: tuple[str, ...]
) -> tuple[tuple[str, Mapping[str, Any]], ...]:
    cv.refuse_when(
        not isinstance(rows, list), cv.FINDING_TASK_FIELD_INVALID, f"{where}: must be a list"
    )
    parsed = []
    for index, row in enumerate(rows):
        label = f"{where}[{index}]"
        cv.refuse_when(
            not isinstance(row, Mapping),
            cv.FINDING_TASK_FIELD_INVALID,
            f"{label}: must be an object",
        )
        name = _require_str(row, "name", label)
        params = row.get("params", {})
        cv.refuse_when(
            not isinstance(params, Mapping),
            cv.FINDING_TASK_FIELD_INVALID,
            f"{label}: params must be an object",
        )
        predicates.check_declaration(name, params, surfaces, label)
        parsed.append((name, dict(params)))
    return tuple(parsed)


def _surfaces(row: Mapping[str, Any], where: str, allowed: tuple[str, ...]) -> tuple[str, ...]:
    surfaces = row.get("surfaces")
    cv.refuse_when(
        not isinstance(surfaces, list)
        or not surfaces
        or any(item not in cv.SURFACES for item in surfaces),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: surfaces must be a nonempty list drawn from {list(cv.SURFACES)}",
    )
    cv.refuse_when(
        any(item not in allowed for item in surfaces),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: surfaces {surfaces} are not all declared by the pack ({list(allowed)})",
    )
    return tuple(surfaces)


def _task_id(raw: Mapping[str, Any], where: str) -> str:
    task_id = _require_str(raw, "task_id", where)
    cv.refuse_when(
        not _TASK_ID.match(task_id),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: task_id {task_id!r} is malformed",
    )
    return task_id


def _title(raw: Mapping[str, Any], where: str) -> str:
    """The title ends the outcome prose, so it must read as the verdict under both verdicts."""
    title = _require_str(raw, "title", where)
    for success in (True, False):
        text = records.outcome_text(title, success, False)
        cv.refuse_when(
            not terminal_outcome_agrees(text, success),
            cv.FINDING_TASK_FIELD_INVALID,
            f"{where}: title {title!r} contradicts the verdict in the outcome text {text!r}",
        )
    return title


def _max_steps(raw: Mapping[str, Any], where: str) -> int:
    max_steps = raw.get("max_steps")
    cv.refuse_when(
        not cv.is_genuine_int(max_steps) or not 1 <= max_steps <= cv.MAX_STEPS_CEILING,
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: max_steps must be an integer in [1, {cv.MAX_STEPS_CEILING}]",
    )
    return max_steps


def _gold(raw: Mapping[str, Any], where: str) -> tuple[Action, ...]:
    rows = raw.get("gold")
    cv.refuse_when(
        not isinstance(rows, list) or not rows,
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: gold must be a nonempty list",
    )
    return tuple(action_from_row(row, f"{where}.gold[{index}]") for index, row in enumerate(rows))


def _faults(raw: Mapping[str, Any], where: str) -> tuple[faults.FaultSpec, ...]:
    rows = raw.get("faults", [])
    cv.refuse_when(
        not isinstance(rows, list), cv.FINDING_TASK_FIELD_INVALID, f"{where}: faults must be a list"
    )
    return tuple(
        faults.fault_spec_from_row(row, f"{where}.faults[{index}]")
        for index, row in enumerate(rows)
    )


def _perturbations(raw: Mapping[str, Any], where: str) -> tuple[str, ...]:
    perturbations = raw.get("perturbations", [])
    cv.refuse_when(
        not isinstance(perturbations, list)
        or any(item not in cv.PERTURBATIONS for item in perturbations),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: perturbations must be drawn from {list(cv.PERTURBATIONS)}",
    )
    return tuple(perturbations)


def _task(raw: Any, where: str, pack_surfaces: tuple[str, ...]) -> Task:
    cv.refuse_when(
        not isinstance(raw, Mapping),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: task must be an object",
    )
    task_id = _task_id(raw, where)
    surfaces = _surfaces(raw, where, pack_surfaces)
    return Task(
        task_id=task_id,
        factory=cv.FACTORY_BY_SURFACE[surfaces[0]],
        surface=surfaces[0],
        surfaces=surfaces,
        title=_title(raw, where),
        goal=_require_str(raw, "goal", where),
        max_steps=_max_steps(raw, where),
        public_predicates=_predicates(
            raw.get("public_predicates", []), f"{where}.public_predicates", surfaces
        ),
        hidden_predicates=_predicates(
            raw.get("hidden_predicates", []), f"{where}.hidden_predicates", surfaces
        ),
        gold=_gold(raw, where),
        faults=_faults(raw, where),
        perturbations=_perturbations(raw, where),
        spec_sha256=sha256_canonical(raw),
    )


def _check_case(case: Any, where: str) -> None:
    cv.refuse_when(
        not isinstance(case, Mapping)
        or not isinstance(case.get("id"), str)
        or not case["id"]
        or not isinstance(case.get("check"), Mapping)
        or not isinstance(case["check"].get("kind"), str),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: a case must be an object with a string id and a check carrying a kind",
    )


def _check_suites(suites: Mapping[str, Any], where: str) -> None:
    """The shape every suite shares; the workspace surface owns the check kinds."""
    for name, spec in suites.items():
        label = f"{where}/{name}.json"
        cv.refuse_when(
            not isinstance(spec, Mapping) or not isinstance(spec.get("cases"), list),
            cv.FINDING_PACK_FIELD_INVALID,
            f"{label}: a suite must be an object with a cases list",
        )
        for index, case in enumerate(spec["cases"]):
            _check_case(case, f"{label}.cases[{index}]")


def _header(directory: Path) -> tuple[Mapping[str, Any], str, tuple[str, ...]]:
    where = f"{directory.name}/{PACK_FILENAME}"
    header = _read_json(directory / PACK_FILENAME, where)
    cv.refuse_when(
        not isinstance(header, Mapping),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: must be an object",
    )
    cv.refuse_when(
        header.get("format") != cv.PACK_FORMAT,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: format must be {cv.PACK_FORMAT}",
    )
    pack_id = header.get("pack_id")
    cv.refuse_when(
        not isinstance(pack_id, str) or not _PACK_ID.match(pack_id) or pack_id != directory.name,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: pack_id must be a slug equal to the directory name",
    )
    license_evidence = header.get("license")
    cv.refuse_when(
        not isinstance(license_evidence, Mapping)
        or not all(
            isinstance(license_evidence.get(key), str) and license_evidence[key]
            for key in ("spdx", "source", "authorship")
        ),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: license must carry spdx, source, and authorship strings",
    )
    surfaces = header.get("surfaces")
    cv.refuse_when(
        not isinstance(surfaces, list)
        or not surfaces
        or any(item not in cv.SURFACES for item in surfaces),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: surfaces must be a nonempty list drawn from {list(cv.SURFACES)}",
    )
    return header, pack_id, tuple(surfaces)


def _site(directory: Path, pack_id: str) -> tuple[Mapping[str, Any] | None, dict[str, str]]:
    pages = _file_members(directory / "pages", f"{pack_id}/pages")
    if "site.json" not in pages:
        return None, pages
    where = f"{pack_id}/pages/site.json"
    site = _read_json(directory / "pages" / "site.json", where)
    _refuse_hidden_keys(site, where, cv.FINDING_PACK_MEMBER_INVALID)
    return site, {name: text for name, text in pages.items() if name != "site.json"}


def _tasks(directory: Path, pack_id: str, surfaces: tuple[str, ...]) -> tuple[Task, ...]:
    rows = _json_members(directory / "tasks", f"{pack_id}/tasks")
    tasks = tuple(
        _task(row, f"{pack_id}/tasks/{name}.json", surfaces) for name, row in rows.items()
    )
    cv.refuse_when(
        not tasks, cv.FINDING_PACK_FIELD_INVALID, f"{pack_id}: a pack needs at least one task"
    )
    ids = [task.task_id for task in tasks]
    cv.refuse_when(
        len(set(ids)) != len(ids), cv.FINDING_TASK_FIELD_INVALID, f"{pack_id}: duplicate task ids"
    )
    return tasks


def load_pack(directory: Path) -> Pack:
    """Load and validate one pack directory; never executes a member."""
    directory = Path(directory)
    cv.refuse_when(
        not directory.is_dir(),
        cv.FINDING_PACK_FILE_MISSING,
        f"missing pack directory {directory.name}",
    )
    header, pack_id, surfaces = _header(directory)
    stray = sorted(
        path.name
        for path in directory.iterdir()
        if path.name != PACK_FILENAME and path.name not in _MEMBER_DIRS
    )
    cv.refuse_when(
        bool(stray), cv.FINDING_PACK_MEMBER_INVALID, f"{pack_id}: unexpected members {stray}"
    )
    site, pages = _site(directory, pack_id)
    tests = _json_members(directory / "tests", f"{pack_id}/tests")
    _check_suites(tests, f"{pack_id}/tests")
    return Pack(
        pack_id=pack_id,
        directory=directory,
        surfaces=surfaces,
        license=dict(header["license"]),
        files=_file_members(directory / "files", f"{pack_id}/files"),
        tests=tests,
        servers=_json_members(directory / "servers", f"{pack_id}/servers"),
        site=site,
        pages=pages,
        workers=_json_members(directory / "workers", f"{pack_id}/workers"),
        tasks=_tasks(directory, pack_id, surfaces),
        pack_sha256=pack_digest(directory),
    )


bind_import_twin(__name__)
