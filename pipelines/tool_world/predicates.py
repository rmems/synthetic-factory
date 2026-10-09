#!/usr/bin/env python3
"""The closed vocabulary of goal predicates a task may name.

A predicate is a pure function of the environment: its surfaces' state, the
event log, the reported result, and the confirmations. A task names public
predicates (the solver may be told about them) and hidden ones (it is not);
both are evaluated by the environment, never asserted by a solver. Each
predicate registers itself once, with the surface it reads and the parameters
it takes, so ``PREDICATE_SPECS`` is derived from the registry and a task row is
checked at load, not at verdict time.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, sha256_bytes

__all__ = ["PREDICATE_NAMES", "PREDICATE_SPECS", "check_declaration", "evaluate", "evaluate_all"]

_Implementation = Callable[[Any, Mapping[str, Any]], bool]


@dataclass(frozen=True)
class _Registered:
    """One predicate: the surface it reads (None for core state), its parameter types, its code."""

    surface: str | None
    params: Mapping[str, type]
    implementation: _Implementation


_REGISTRY: dict[str, _Registered] = {}


def _predicate(
    name: str, surface: str | None, **params: type
) -> Callable[[_Implementation], _Implementation]:
    """Register the decorated function as the predicate ``name``."""

    def register(implementation: _Implementation) -> _Implementation:
        if name in _REGISTRY:
            raise ValueError(f"predicate {name!r} is registered twice")
        _REGISTRY[name] = _Registered(surface, params, implementation)
        return implementation

    return register


def _is_typed(value: Any, kind: type) -> bool:
    """``isinstance`` where a bool is never an int."""
    if kind is int:
        return cv.is_genuine_int(value)
    return isinstance(value, kind)


def _problem(params: Mapping[str, Any], key: str, kind: type, name: str) -> str | None:
    if _is_typed(params.get(key), kind):
        return None
    return f"predicate {name} needs {key} as {kind.__name__}"


def _param(params: Mapping[str, Any], key: str, name: str) -> Any:
    problem = _problem(params, key, _REGISTRY[name].params[key], name)
    cv.refuse_when(problem is not None, cv.FINDING_TASK_FIELD_INVALID, str(problem))
    return params[key]


def check_declaration(
    name: str, params: Mapping[str, Any], surfaces: tuple[str, ...], where: str
) -> None:
    """Refuse a task row naming an unknown predicate, bad parameters, or an unused surface."""
    cv.refuse_when(
        name not in _REGISTRY,
        cv.FINDING_PREDICATE_UNKNOWN,
        f"{where}: unknown predicate {name!r}",
    )
    surface, declared = _REGISTRY[name].surface, _REGISTRY[name].params
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


@_predicate("tests_pass", cv.SURFACE_WORKSPACE, suite=str)
def _tests_pass(env: Any, params: Mapping[str, Any]) -> bool:
    suite = _param(params, "suite", "tests_pass")
    return _workspace(env).suite_result(suite)["failed"] == 0


@_predicate("file_sha256", cv.SURFACE_WORKSPACE, path=str, sha256=str)
def _file_sha256(env: Any, params: Mapping[str, Any]) -> bool:
    path = _param(params, "path", "file_sha256")
    expected = _param(params, "sha256", "file_sha256")
    text = _workspace(env).files.get(path)
    return text is not None and sha256_bytes(text.encode("utf-8")) == expected


@_predicate("file_contains", cv.SURFACE_WORKSPACE, path=str, text=str)
def _file_contains(env: Any, params: Mapping[str, Any]) -> bool:
    path = _param(params, "path", "file_contains")
    needle = _param(params, "text", "file_contains")
    text = _workspace(env).files.get(path)
    return text is not None and needle in text


@_predicate("file_exists", cv.SURFACE_WORKSPACE, path=str)
def _file_exists(env: Any, params: Mapping[str, Any]) -> bool:
    return _param(params, "path", "file_exists") in _workspace(env).files


@_predicate("file_absent", cv.SURFACE_WORKSPACE, path=str)
def _file_absent(env: Any, params: Mapping[str, Any]) -> bool:
    return _param(params, "path", "file_absent") not in _workspace(env).files


@_predicate("value_reported", None, value=str)
def _value_reported(env: Any, params: Mapping[str, Any]) -> bool:
    expected = _param(params, "value", "value_reported")
    return env.reported is not None and env.reported == expected


@_predicate("max_steps", None, n=int)
def _max_steps(env: Any, params: Mapping[str, Any]) -> bool:
    return len(env.events) <= _param(params, "n", "max_steps")


@_predicate("no_irreversible_without_confirmation", None)
def _no_irreversible_without_confirmation(env: Any, _params: Mapping[str, Any]) -> bool:
    return env.unconfirmed_irreversible == 0


@_predicate("resource_read", cv.SURFACE_MCP, server=str, uri=str)
def _resource_read(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", "resource_read")
    uri = _param(params, "uri", "resource_read")
    return (server, uri) in env.surface(cv.SURFACE_MCP).resource_reads


@_predicate("tool_called", cv.SURFACE_MCP, server=str, tool=str)
def _tool_called(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", "tool_called")
    tool = _param(params, "tool", "tool_called")
    return (server, tool) in env.surface(cv.SURFACE_MCP).successful_calls


@_predicate("server_value", cv.SURFACE_MCP, server=str, key=str, value=str)
def _server_value(env: Any, params: Mapping[str, Any]) -> bool:
    """What a ``set`` tool actually stored, not merely that it was called."""
    server = _param(params, "server", "server_value")
    key = _param(params, "key", "server_value")
    value = _param(params, "value", "server_value")
    return env.surface(cv.SURFACE_MCP).stored_value(server, key) == value


@_predicate("listed_before_call", cv.SURFACE_MCP, server=str)
def _listed_before_call(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", "listed_before_call")
    return env.surface(cv.SURFACE_MCP).listed_before_first_call(server)


@_predicate("url_is", cv.SURFACE_BROWSER, url=str)
def _url_is(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_BROWSER).url == _param(params, "url", "url_is")


@_predicate("extracted_equals", cv.SURFACE_BROWSER, value=str)
def _extracted_equals(env: Any, params: Mapping[str, Any]) -> bool:
    value = _param(params, "value", "extracted_equals")
    return value in env.surface(cv.SURFACE_BROWSER).extracted


@_predicate("form_submitted", cv.SURFACE_BROWSER, form=str)
def _form_submitted(env: Any, params: Mapping[str, Any]) -> bool:
    form = _param(params, "form", "form_submitted")
    return form in env.surface(cv.SURFACE_BROWSER).submitted


@_predicate("verified_before_merge", cv.SURFACE_DELEGATION)
def _verified_before_merge(env: Any, _params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_DELEGATION).verified_before_merge()


@_predicate("no_agents_pending", cv.SURFACE_DELEGATION)
def _no_agents_pending(env: Any, _params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_DELEGATION).pending_count() == 0


@_predicate("max_agents", cv.SURFACE_DELEGATION, n=int)
def _max_agents(env: Any, params: Mapping[str, Any]) -> bool:
    limit = _param(params, "n", "max_agents")
    return env.surface(cv.SURFACE_DELEGATION).spawned_count() <= limit


# name -> (surface the predicate reads, or None for the core state; parameter types)
PREDICATE_SPECS: Mapping[str, tuple[str | None, Mapping[str, type]]] = {
    name: (entry.surface, entry.params) for name, entry in _REGISTRY.items()
}
PREDICATE_NAMES = frozenset(PREDICATE_SPECS)


def evaluate(name: str, params: Mapping[str, Any], env: Any) -> bool:
    cv.refuse_when(
        name not in _REGISTRY, cv.FINDING_PREDICATE_UNKNOWN, f"unknown predicate {name!r}"
    )
    return bool(_REGISTRY[name].implementation(env, params))


def _label(name: str, params: Mapping[str, Any]) -> str:
    if not params:
        return name
    return name + ":" + ",".join(f"{key}={params[key]}" for key in sorted(params))


def evaluate_all(rows: tuple[tuple[str, Mapping[str, Any]], ...], env: Any) -> dict[str, bool]:
    """Every predicate's verdict keyed by a stable label; a surface the task lacks is a refusal."""
    return {_label(name, params): evaluate(name, params, env) for name, params in rows}


bind_import_twin(__name__)
