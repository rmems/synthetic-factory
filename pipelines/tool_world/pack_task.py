#!/usr/bin/env python3
"""One task member of a pack: identity, surfaces, title, plan, faults and predicates.

Every field is checked when the pack loads, so a task the environment runs
has a well-formed id that its file names, surfaces the pack declares, a title
that reads as the verdict under either outcome, a bounded step budget, a
nonempty gold plan, parsed fault specs and declared perturbations, and
predicate declarations the registry knows. ``spec_sha256`` is the digest of
the raw task object, so a record can pin the exact spec it was drawn from.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeGuard

from . import faults, predicates, records
from . import vocabulary as cv
from ._contract import bind_import_twin, sha256_canonical, terminal_outcome_agrees

__all__ = ["Task", "is_slug", "parse_task", "surface_list"]

_SLUG_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789")
_TASK_ID_SEPARATORS = "-."
# Named here so the ``faults`` field below does not shadow the module inside the class body.
Action = faults.Action
FaultSpec = faults.FaultSpec


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
    faults: tuple[FaultSpec, ...]
    perturbations: tuple[str, ...]
    spec_sha256: str


def _is_slug_run(part: str) -> bool:
    return bool(part) and set(part) <= _SLUG_CHARS


def is_slug(value: str, separators: str) -> bool:
    """``[a-z0-9]+`` runs joined by single separators: none leading, trailing, or doubled.

    The language of ``^[a-z0-9]+(?:[<separators>][a-z0-9]+)*$``, decided by
    splitting on the separators rather than by a backtracking regex.
    """
    for separator in separators[1:]:
        value = value.replace(separator, separators[0])
    return all(_is_slug_run(part) for part in value.split(separators[0]))


def _is_surface_list(value: Any) -> TypeGuard[list[str]]:
    """A nonempty list drawn from the surface vocabulary."""
    return isinstance(value, list) and bool(value) and all(item in cv.SURFACES for item in value)


def _require_str(row: Mapping[str, Any], key: str, where: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise cv.ToolWorldRefusal(
            cv.FINDING_TASK_FIELD_INVALID, f"{where}: {key} must be a nonempty string"
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


def surface_list(value: Any, code: str, where: str) -> list[str]:
    """``value`` as a nonempty list of known surfaces, or a refusal under ``code``."""
    if _is_surface_list(value):
        return value
    raise cv.ToolWorldRefusal(
        code, f"{where}: surfaces must be a nonempty list drawn from {list(cv.SURFACES)}"
    )


def _surfaces(row: Mapping[str, Any], where: str, allowed: tuple[str, ...]) -> tuple[str, ...]:
    surfaces = surface_list(row.get("surfaces"), cv.FINDING_TASK_FIELD_INVALID, where)
    cv.refuse_when(
        any(item not in allowed for item in surfaces),
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: surfaces {surfaces} are not all declared by the pack ({list(allowed)})",
    )
    return tuple(surfaces)


def _task_id(raw: Mapping[str, Any], where: str) -> str:
    task_id = _require_str(raw, "task_id", where)
    cv.refuse_when(
        not is_slug(task_id, _TASK_ID_SEPARATORS),
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
    if cv.is_genuine_int(max_steps) and 1 <= max_steps <= cv.MAX_STEPS_CEILING:
        return max_steps
    raise cv.ToolWorldRefusal(
        cv.FINDING_TASK_FIELD_INVALID,
        f"{where}: max_steps must be an integer in [1, {cv.MAX_STEPS_CEILING}]",
    )


def _gold(raw: Mapping[str, Any], where: str) -> tuple[Action, ...]:
    rows = raw.get("gold")
    if not isinstance(rows, list) or not rows:
        raise cv.ToolWorldRefusal(
            cv.FINDING_TASK_FIELD_INVALID, f"{where}: gold must be a nonempty list"
        )
    return tuple(
        faults.action_from_row(row, f"{where}.gold[{index}]") for index, row in enumerate(rows)
    )


def _faults(raw: Mapping[str, Any], where: str) -> tuple[FaultSpec, ...]:
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


def parse_task(raw: Any, where: str, pack_surfaces: tuple[str, ...]) -> Task:
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


bind_import_twin(__name__)
