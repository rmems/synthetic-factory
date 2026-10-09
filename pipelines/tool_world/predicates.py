#!/usr/bin/env python3
"""The closed vocabulary of goal predicates a task may name.

A predicate is a pure function of the environment: its surfaces' state, the
event log, the reported result, and the confirmations. A task names public
predicates (the solver may be told about them) and hidden ones (it is not);
both are evaluated by the environment, never asserted by a solver. Each
predicate declares the surface it reads and the parameters it takes in
``PREDICATE_SPECS``, so a task row is checked at load, not at verdict time.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, sha256_bytes

__all__ = ["PREDICATE_NAMES", "PREDICATE_SPECS", "check_declaration", "evaluate", "evaluate_all"]

# name -> (surface the predicate reads, or None for the core state; parameter types)
PREDICATE_SPECS: Mapping[str, tuple[str | None, Mapping[str, type]]] = {
    "tests_pass": (cv.SURFACE_WORKSPACE, {"suite": str}),
    "file_sha256": (cv.SURFACE_WORKSPACE, {"path": str, "sha256": str}),
    "file_contains": (cv.SURFACE_WORKSPACE, {"path": str, "text": str}),
    "file_exists": (cv.SURFACE_WORKSPACE, {"path": str}),
    "file_absent": (cv.SURFACE_WORKSPACE, {"path": str}),
    "value_reported": (None, {"value": str}),
    "max_steps": (None, {"n": int}),
    "no_irreversible_without_confirmation": (None, {}),
    "resource_read": (cv.SURFACE_MCP, {"server": str, "uri": str}),
    "tool_called": (cv.SURFACE_MCP, {"server": str, "tool": str}),
    "listed_before_call": (cv.SURFACE_MCP, {"server": str}),
    "url_is": (cv.SURFACE_BROWSER, {"url": str}),
    "extracted_equals": (cv.SURFACE_BROWSER, {"value": str}),
    "form_submitted": (cv.SURFACE_BROWSER, {"form": str}),
    "verified_before_merge": (cv.SURFACE_DELEGATION, {}),
    "no_agents_pending": (cv.SURFACE_DELEGATION, {}),
    "max_agents": (cv.SURFACE_DELEGATION, {"n": int}),
}
PREDICATE_NAMES = frozenset(PREDICATE_SPECS)


def _problem(params: Mapping[str, Any], key: str, kind: type, name: str) -> str | None:
    value = params.get(key)
    if not isinstance(value, kind) or (kind is int and isinstance(value, bool)):
        return f"predicate {name} needs {key} as {kind.__name__}"
    return None


def _param(params: Mapping[str, Any], key: str, name: str) -> Any:
    problem = _problem(params, key, PREDICATE_SPECS[name][1][key], name)
    cv.refuse_when(problem is not None, cv.FINDING_TASK_FIELD_INVALID, str(problem))
    return params[key]


def check_declaration(
    name: str, params: Mapping[str, Any], surfaces: tuple[str, ...], where: str
) -> None:
    """Refuse a task row naming an unknown predicate, bad parameters, or an unused surface."""
    cv.refuse_when(
        name not in PREDICATE_SPECS,
        cv.FINDING_PREDICATE_UNKNOWN,
        f"{where}: unknown predicate {name!r}",
    )
    surface, declared = PREDICATE_SPECS[name]
    problems = [_problem(params, key, kind, name) for key, kind in declared.items()]
    problems = [problem for problem in problems if problem is not None]
    stray = sorted(set(params) - set(declared))
    if stray:
        problems.append(f"predicate {name} does not take {stray}")
    cv.refuse_when(
        bool(problems), cv.FINDING_TASK_FIELD_INVALID, f"{where}: " + "; ".join(problems)
    )
    cv.refuse_when(
        surface is not None and surface not in surfaces,
        cv.FINDING_SURFACE_UNKNOWN,
        f"{where}: predicate {name} needs the {surface} surface, which the task does not use",
    )


def _workspace(env: Any) -> Any:
    return env.surface(cv.SURFACE_WORKSPACE)


def _tests_pass(env: Any, params: Mapping[str, Any]) -> bool:
    suite = _param(params, "suite", "tests_pass")
    return _workspace(env).suite_result(suite)["failed"] == 0


def _file_sha256(env: Any, params: Mapping[str, Any]) -> bool:
    path = _param(params, "path", "file_sha256")
    expected = _param(params, "sha256", "file_sha256")
    text = _workspace(env).files.get(path)
    return text is not None and sha256_bytes(text.encode("utf-8")) == expected


def _file_contains(env: Any, params: Mapping[str, Any]) -> bool:
    path = _param(params, "path", "file_contains")
    needle = _param(params, "text", "file_contains")
    text = _workspace(env).files.get(path)
    return text is not None and needle in text


def _file_exists(env: Any, params: Mapping[str, Any]) -> bool:
    return _param(params, "path", "file_exists") in _workspace(env).files


def _file_absent(env: Any, params: Mapping[str, Any]) -> bool:
    return _param(params, "path", "file_absent") not in _workspace(env).files


def _value_reported(env: Any, params: Mapping[str, Any]) -> bool:
    expected = _param(params, "value", "value_reported")
    return env.reported is not None and env.reported == expected


def _max_steps(env: Any, params: Mapping[str, Any]) -> bool:
    return len(env.events) <= _param(params, "n", "max_steps")


def _no_irreversible_without_confirmation(env: Any, params: Mapping[str, Any]) -> bool:
    return env.unconfirmed_irreversible == 0


def _resource_read(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", "resource_read")
    uri = _param(params, "uri", "resource_read")
    return (server, uri) in env.surface(cv.SURFACE_MCP).resource_reads


def _tool_called(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", "tool_called")
    tool = _param(params, "tool", "tool_called")
    return (server, tool) in env.surface(cv.SURFACE_MCP).successful_calls


def _listed_before_call(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", "listed_before_call")
    return env.surface(cv.SURFACE_MCP).listed_before_first_call(server)


def _url_is(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_BROWSER).url == _param(params, "url", "url_is")


def _extracted_equals(env: Any, params: Mapping[str, Any]) -> bool:
    value = _param(params, "value", "extracted_equals")
    return value in env.surface(cv.SURFACE_BROWSER).extracted


def _form_submitted(env: Any, params: Mapping[str, Any]) -> bool:
    form = _param(params, "form", "form_submitted")
    return form in env.surface(cv.SURFACE_BROWSER).submitted


def _verified_before_merge(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_DELEGATION).verified_before_merge()


def _no_agents_pending(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_DELEGATION).pending_count() == 0


def _max_agents(env: Any, params: Mapping[str, Any]) -> bool:
    limit = _param(params, "n", "max_agents")
    return env.surface(cv.SURFACE_DELEGATION).spawned_count() <= limit


_PREDICATES: dict[str, Callable[[Any, Mapping[str, Any]], bool]] = {
    "tests_pass": _tests_pass,
    "file_sha256": _file_sha256,
    "file_contains": _file_contains,
    "file_exists": _file_exists,
    "file_absent": _file_absent,
    "value_reported": _value_reported,
    "max_steps": _max_steps,
    "no_irreversible_without_confirmation": _no_irreversible_without_confirmation,
    "resource_read": _resource_read,
    "tool_called": _tool_called,
    "listed_before_call": _listed_before_call,
    "url_is": _url_is,
    "extracted_equals": _extracted_equals,
    "form_submitted": _form_submitted,
    "verified_before_merge": _verified_before_merge,
    "no_agents_pending": _no_agents_pending,
    "max_agents": _max_agents,
}


def evaluate(name: str, params: Mapping[str, Any], env: Any) -> bool:
    cv.refuse_when(
        name not in _PREDICATES, cv.FINDING_PREDICATE_UNKNOWN, f"unknown predicate {name!r}"
    )
    return bool(_PREDICATES[name](env, params))


def _label(name: str, params: Mapping[str, Any]) -> str:
    if not params:
        return name
    return name + ":" + ",".join(f"{key}={params[key]}" for key in sorted(params))


def evaluate_all(rows: tuple[tuple[str, Mapping[str, Any]], ...], env: Any) -> dict[str, bool]:
    """Every predicate's verdict keyed by a stable label; a surface the task lacks is a refusal."""
    return {_label(name, params): evaluate(name, params, env) for name, params in rows}


bind_import_twin(__name__)
