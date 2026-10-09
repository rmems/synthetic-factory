#!/usr/bin/env python3
"""Server members of the MCP surface: their shape at load, their session state, their behaviors.

A server is a pack member: tools with ``inputSchema`` and a declared
behavior, resources, prompts, a page size, and an optional drifted tool set.
``check_server_spec`` refuses at load any member the transport could not
serve exactly as written, so a request never meets a shape the surface
cannot answer. ``Server`` carries one member's session state across an
episode, and ``behave`` runs one validated ``tools/call`` against the
declared behavior kinds, returning the text and whether it is an error.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from .. import schema_lite
from .. import vocabulary as cv
from .._contract import bind_import_twin
from .base import canonical_text

__all__ = ["Server", "behave", "check_server_spec"]

_BEHAVIOR_STRING_KEYS = ("key_arg", "value_arg", "message")


class Server:
    def __init__(self, spec: Mapping[str, Any]) -> None:
        self.spec = spec
        self.name = spec["name"]
        self.initialized = False
        self.client_ready = False
        self.drifted = False
        self.notifications: list[str] = []
        self.store: dict[str, str] = {}
        self.listed_at: list[int] = []
        self.first_call_at: int | None = None
        self.calls = 0

    def tools(self) -> list[Mapping[str, Any]]:
        if self.drifted and isinstance(self.spec.get("drifted_tools"), list):
            return list(self.spec["drifted_tools"])
        return list(self.spec.get("tools", []))

    def view(self) -> dict[str, Any]:
        return {
            "initialized": self.initialized,
            "client_ready": self.client_ready,
            "drifted": self.drifted,
            "store": dict(sorted(self.store.items())),
            "calls": self.calls,
        }


# --- tool behaviors: (text, isError) for one validated call ---------------


def _key_of(behavior: Mapping[str, Any], arguments: Mapping[str, Any]) -> str:
    return str(arguments.get(behavior.get("key_arg", "key")))


def _echo(_server: Server, _behavior: Mapping[str, Any], arguments: Mapping[str, Any]):
    return canonical_text(arguments), False


def _lookup(_server: Server, behavior: Mapping[str, Any], arguments: Mapping[str, Any]):
    key, table = _key_of(behavior, arguments), behavior.get("table", {})
    if key in table:
        return table[key], False
    return f"no entry for {key!r}", True


def _set(server: Server, behavior: Mapping[str, Any], arguments: Mapping[str, Any]):
    key = _key_of(behavior, arguments)
    server.store[key] = str(arguments.get(behavior.get("value_arg", "value")))
    return f"stored {key}", False


def _get(server: Server, behavior: Mapping[str, Any], arguments: Mapping[str, Any]):
    key = _key_of(behavior, arguments)
    if key in server.store:
        return server.store[key], False
    return f"nothing stored under {key!r}", True


def _list_items(_server: Server, behavior: Mapping[str, Any], _arguments: Mapping[str, Any]):
    return "\n".join(behavior.get("items", [])), False


def _fail(_server: Server, behavior: Mapping[str, Any], _arguments: Mapping[str, Any]):
    return behavior.get("message", "tool failed"), True


_BEHAVIORS = {
    "echo": _echo,
    "lookup": _lookup,
    "set": _set,
    "get": _get,
    "list_items": _list_items,
    "fail": _fail,
}


def behave(
    server: Server, behavior: Mapping[str, Any], arguments: Mapping[str, Any]
) -> tuple[str, bool]:
    """Run one validated call against its declared behavior: ``(text, isError)``."""
    kind = behavior.get("kind", "echo")
    handler = _BEHAVIORS.get(kind)
    if handler is None:
        raise cv.ToolWorldRefusal(
            cv.FINDING_PACK_FIELD_INVALID,
            f"tool behavior kind {kind!r} is not one of {sorted(_BEHAVIORS)}",
        )
    return handler(server, behavior, arguments)


# --- load-time checks of a server member ----------------------------------


def _all_strings(values: Any) -> bool:
    return all(isinstance(value, str) for value in values)


def _is_text_entry(row: Any, key: str) -> bool:
    return (
        isinstance(row, Mapping)
        and isinstance(row.get(key), str)
        and isinstance(row.get("text"), str)
    )


def _duplicates(values: Iterable[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def _check_unique(names: Iterable[str], key: str, where: str) -> None:
    """Refuse a member list in which two entries answer to one ``key``."""
    repeated = _duplicates(names)
    cv.refuse_when(
        bool(repeated),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: duplicate {key} values {repeated}",
    )


def _check_rows(rows: Any, key: str, where: str) -> None:
    cv.refuse_when(
        not isinstance(rows, list) or any(not _is_text_entry(row, key) for row in rows),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: every entry must be an object with a string {key!r} and a string 'text'",
    )
    _check_unique((row[key] for row in rows), key, where)


def _check_input_schema(schema: Any, where: str) -> None:
    problems = schema_lite.check_schema(schema, where)
    cv.refuse_when(bool(problems), cv.FINDING_PACK_FIELD_INVALID, "; ".join(problems))
    cv.refuse_when(
        schema.get("type") != "object",
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: type must be 'object'",
    )


def _check_behavior(behavior: Any, where: str) -> None:
    kind = behavior.get("kind", "echo") if isinstance(behavior, Mapping) else None
    cv.refuse_when(
        not isinstance(kind, str) or kind not in _BEHAVIORS,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: must be an object whose kind is one of {sorted(_BEHAVIORS)}",
    )
    table, items = behavior.get("table", {}), behavior.get("items", [])
    cv.refuse_when(
        not isinstance(table, Mapping) or not _all_strings([*table, *table.values()]),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}.table: must map strings to strings",
    )
    cv.refuse_when(
        not isinstance(items, list) or not _all_strings(items),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}.items: must be a list of strings",
    )
    for key in _BEHAVIOR_STRING_KEYS:
        cv.refuse_when(
            key in behavior and not isinstance(behavior[key], str),
            cv.FINDING_PACK_FIELD_INVALID,
            f"{where}.{key}: must be a string",
        )


def _check_tools(rows: Any, where: str) -> None:
    cv.refuse_when(
        not isinstance(rows, list), cv.FINDING_PACK_FIELD_INVALID, f"{where}: must be a list"
    )
    for index, row in enumerate(rows):
        label = f"{where}[{index}]"
        cv.refuse_when(
            not isinstance(row, Mapping) or not isinstance(row.get("name"), str) or not row["name"],
            cv.FINDING_PACK_FIELD_INVALID,
            f"{label}: a tool must carry a nonempty name",
        )
        _check_input_schema(row.get("inputSchema"), f"{label}.inputSchema")
        _check_behavior(row.get("behavior", {}), f"{label}.behavior")
    _check_unique((row["name"] for row in rows), "name", where)


def check_server_spec(name: str, spec: Any) -> None:
    """Refuse a server member the surface could not serve exactly as written."""
    where = f"server {name}"
    cv.refuse_when(
        not isinstance(spec, Mapping) or spec.get("name") != name,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: must be an object whose name equals its file stem",
    )
    if "page_size" in spec:
        cv.refuse_when(
            not cv.is_genuine_int(spec["page_size"]) or spec["page_size"] < 1,
            cv.FINDING_PACK_FIELD_INVALID,
            f"{where}: page_size must be a positive integer",
        )
    for key in ("tools", "drifted_tools"):
        _check_tools(spec.get(key, []), f"{where}.{key}")
    _check_rows(spec.get("resources", []), "uri", f"{where}.resources")
    _check_rows(spec.get("prompts", []), "name", f"{where}.prompts")


bind_import_twin(__name__)
