#!/usr/bin/env python3
"""The closed vocabulary of goal predicates a task may name.

A predicate is a pure function of the environment: its surfaces' state, the
event log, the reported result, and the confirmations. A task names public
predicates (the solver may be told about them) and hidden ones (it is not);
both are evaluated by the environment, never asserted by a solver.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from . import vocabulary as cv
from ._contract import bind_import_twin, sha256_bytes

__all__ = ["PREDICATE_NAMES", "evaluate", "evaluate_all"]


def _param(params: Mapping[str, Any], key: str, kind: type, name: str) -> Any:
    value = params.get(key)
    cv.refuse_when(
        not isinstance(value, kind) or (kind is int and isinstance(value, bool)),
        cv.FINDING_TASK_FIELD_INVALID,
        f"predicate {name} needs {key} as {kind.__name__}",
    )
    return value


def _workspace(env: Any) -> Any:
    return env.surface(cv.SURFACE_WORKSPACE)


def _tests_pass(env: Any, params: Mapping[str, Any]) -> bool:
    suite = _param(params, "suite", str, "tests_pass")
    return _workspace(env).suite_result(suite)["failed"] == 0


def _file_sha256(env: Any, params: Mapping[str, Any]) -> bool:
    path = _param(params, "path", str, "file_sha256")
    expected = _param(params, "sha256", str, "file_sha256")
    text = _workspace(env).files.get(path)
    return text is not None and sha256_bytes(text.encode("utf-8")) == expected


def _file_contains(env: Any, params: Mapping[str, Any]) -> bool:
    path = _param(params, "path", str, "file_contains")
    needle = _param(params, "text", str, "file_contains")
    text = _workspace(env).files.get(path)
    return text is not None and needle in text


def _file_exists(env: Any, params: Mapping[str, Any]) -> bool:
    return _param(params, "path", str, "file_exists") in _workspace(env).files


def _file_absent(env: Any, params: Mapping[str, Any]) -> bool:
    return _param(params, "path", str, "file_absent") not in _workspace(env).files


def _value_reported(env: Any, params: Mapping[str, Any]) -> bool:
    return env.reported is not None and env.reported == _param(
        params, "value", str, "value_reported"
    )


def _max_steps(env: Any, params: Mapping[str, Any]) -> bool:
    return len(env.events) <= _param(params, "n", int, "max_steps")


def _no_irreversible_without_confirmation(env: Any, params: Mapping[str, Any]) -> bool:
    return env.unconfirmed_irreversible == 0


def _resource_read(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", str, "resource_read")
    uri = _param(params, "uri", str, "resource_read")
    return (server, uri) in env.surface(cv.SURFACE_MCP).resource_reads


def _tool_called(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", str, "tool_called")
    tool = _param(params, "tool", str, "tool_called")
    return (server, tool) in env.surface(cv.SURFACE_MCP).successful_calls


def _listed_before_call(env: Any, params: Mapping[str, Any]) -> bool:
    server = _param(params, "server", str, "listed_before_call")
    return env.surface(cv.SURFACE_MCP).listed_before_first_call(server)


def _url_is(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_BROWSER).url == _param(params, "url", str, "url_is")


def _extracted_equals(env: Any, params: Mapping[str, Any]) -> bool:
    value = _param(params, "value", str, "extracted_equals")
    return value in env.surface(cv.SURFACE_BROWSER).extracted


def _form_submitted(env: Any, params: Mapping[str, Any]) -> bool:
    form = _param(params, "form", str, "form_submitted")
    return form in env.surface(cv.SURFACE_BROWSER).submitted


def _verified_before_merge(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_DELEGATION).verified_before_merge()


def _no_agents_pending(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_DELEGATION).pending_count() == 0


def _max_agents(env: Any, params: Mapping[str, Any]) -> bool:
    return env.surface(cv.SURFACE_DELEGATION).spawned_count() <= _param(
        params, "n", int, "max_agents"
    )


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
PREDICATE_NAMES = frozenset(_PREDICATES)


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
