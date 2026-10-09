#!/usr/bin/env python3
"""The MCP surface: simulated JSON-RPC 2.0 servers behind one ``mcp`` tool.

Each server is a pack member: tools with ``inputSchema`` and a declared
behavior, resources, prompts, a page size, and an optional drifted tool set.
Responses are canonical JSON-RPC envelopes; a pending
``notifications/tools/list_changed`` is delivered on the line before the next
response, as a transport would deliver it.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .. import schema_lite
from .. import vocabulary as cv
from .._contract import bind_import_twin
from .base import Surface, ToolSpec, canonical_text

__all__ = ["McpSurface"]

FAULT_SCHEMA_DRIFT = "schema_drift"
FAULT_RATE_LIMITED = "rate_limited"
FAULT_SERVER_RESTART = "server_restart"
FAULT_EMPTY_FIRST_PAGE = "empty_first_page"
PROTOCOL_VERSION = "2025-06-18"
_METHODS = (
    "initialize",
    "notifications/initialized",
    "tools/list",
    "tools/call",
    "resources/list",
    "resources/read",
    "prompts/list",
    "prompts/get",
)
_ERR_INVALID_REQUEST = -32600
_ERR_METHOD_NOT_FOUND = -32601
_ERR_INVALID_PARAMS = -32602
_ERR_INTERNAL = -32603
_ERR_RATE_LIMITED = -32000
_ERR_RESOURCE_NOT_FOUND = -32002


class _Server:
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


class McpSurface(Surface):
    NAME = cv.SURFACE_MCP
    FAULT_KINDS = frozenset(
        {FAULT_SCHEMA_DRIFT, FAULT_RATE_LIMITED, FAULT_SERVER_RESTART, FAULT_EMPTY_FIRST_PAGE}
    )

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        super().__init__(pack, task, env)
        cv.refuse_when(
            not pack.servers,
            cv.FINDING_PACK_FIELD_INVALID,
            f"pack {pack.pack_id} declares no MCP servers",
        )
        self.servers = {name: _Server(spec) for name, spec in pack.servers.items()}
        for name, server in self.servers.items():
            cv.refuse_when(
                server.name != name,
                cv.FINDING_PACK_FIELD_INVALID,
                f"server {name} names itself {server.name!r}",
            )
        self.request_id = 0
        self.resource_reads: set[tuple[str, str]] = set()
        self.successful_calls: set[tuple[str, str]] = set()

    def tools(self) -> tuple[ToolSpec, ...]:
        return (
            ToolSpec(
                cv.TOOL_MCP,
                self.NAME,
                "Send one JSON-RPC request to a named MCP server and read its response.",
                {
                    "type": "object",
                    "required": ["server", "method"],
                    "properties": {
                        "server": {"type": "string", "enum": sorted(self.servers)},
                        "method": {"type": "string", "enum": list(_METHODS)},
                        "params": {"type": "object"},
                    },
                    "additionalProperties": False,
                },
                actions=_METHODS,
            ),
        )

    # --- transport ---------------------------------------------------------

    def execute(self, name: str, args: Mapping[str, Any], fault: Any) -> str:
        server = self.servers[args["server"]]
        method, params = args["method"], dict(args.get("params") or {})
        self.request_id += 1
        pending = [
            canonical_text({"jsonrpc": "2.0", "method": note}) for note in server.notifications
        ]
        server.notifications.clear()
        kind = fault.spec.kind if fault is not None else None
        if kind == FAULT_SCHEMA_DRIFT and not server.drifted:
            server.drifted = True
            pending.append(
                canonical_text({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            )
        if kind == FAULT_RATE_LIMITED:
            body = self._error(
                _ERR_RATE_LIMITED, "rate limited; retry after 1s", {"retryAfterMs": 1000}
            )
        elif kind == FAULT_SERVER_RESTART:
            server.initialized, server.store = False, {}
            body = self._error(_ERR_INTERNAL, "server restarted; session lost, initialize again")
        else:
            body = self._dispatch(server, method, params, kind)
        return "\n".join(pending + [canonical_text(body)])

    def _error(self, code: int, message: str, data: Any = None) -> dict[str, Any]:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": self.request_id, "error": error}

    def _result(self, result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": self.request_id, "result": result}

    def _dispatch(
        self, server: _Server, method: str, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        if method == "initialize":
            server.initialized = True
            return self._result(
                {
                    "protocolVersion": server.spec.get("protocol_version", PROTOCOL_VERSION),
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {},
                        "prompts": {},
                    },
                    "serverInfo": {
                        "name": server.name,
                        "version": server.spec.get("version", "1.0.0"),
                    },
                }
            )
        if not server.initialized:
            return self._error(
                _ERR_INVALID_REQUEST, "session not initialized: call initialize first"
            )
        if method == "notifications/initialized":
            server.client_ready = True
            return {
                "jsonrpc": "2.0",
                "method": method,
                "delivered": True,
                "note": "notifications carry no response",
            }
        handlers = {
            "tools/list": self._tools_list,
            "tools/call": self._tools_call,
            "resources/list": self._resources_list,
            "resources/read": self._resources_read,
            "prompts/list": self._prompts_list,
            "prompts/get": self._prompts_get,
        }
        if method not in handlers:
            return self._error(_ERR_METHOD_NOT_FOUND, f"method not found: {method}")
        return handlers[method](server, params, kind)

    # --- methods -----------------------------------------------------------

    def _tools_list(
        self, server: _Server, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        tools = server.tools()
        size = int(server.spec.get("page_size", len(tools) or 1))
        cursor = params.get("cursor")
        start = 0
        if cursor is not None:
            if (
                not isinstance(cursor, str)
                or not cursor.startswith("cursor-")
                or not cursor[7:].isdigit()
            ):
                return self._error(_ERR_INVALID_PARAMS, f"invalid cursor {cursor!r}")
            start = int(cursor[7:])
        server.listed_at.append(len(self.env.events) + 1)
        if kind == FAULT_EMPTY_FIRST_PAGE and cursor is None:
            return self._result({"tools": [], "nextCursor": "cursor-0"})
        page = tools[start : start + size]
        result: dict[str, Any] = {"tools": [self._public_tool(tool) for tool in page]}
        if start + size < len(tools):
            result["nextCursor"] = f"cursor-{start + size}"
        return self._result(result)

    @staticmethod
    def _public_tool(tool: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "inputSchema": tool["inputSchema"],
        }

    def _tools_call(
        self, server: _Server, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        name = params.get("name")
        tool = next((row for row in server.tools() if row["name"] == name), None)
        if tool is None:
            return self._error(_ERR_INVALID_PARAMS, f"unknown tool: {name}")
        arguments = params.get("arguments", {})
        problems = schema_lite.validate_args(tool["inputSchema"], arguments, "arguments")
        if problems:
            return self._error(_ERR_INVALID_PARAMS, "invalid arguments: " + "; ".join(problems))
        server.calls += 1
        if server.first_call_at is None:
            server.first_call_at = len(self.env.events) + 1
        text, is_error = self._behave(server, tool.get("behavior") or {}, arguments)
        if not is_error:
            self.successful_calls.add((server.name, name))
        return self._result({"content": [{"type": "text", "text": text}], "isError": is_error})

    @staticmethod
    def _behave(
        server: _Server, behavior: Mapping[str, Any], arguments: Mapping[str, Any]
    ) -> tuple[str, bool]:
        kind = behavior.get("kind", "echo")
        if kind == "lookup":
            key = str(arguments.get(behavior.get("key_arg", "key")))
            table = behavior.get("table") or {}
            if key in table:
                return str(table[key]), False
            return f"no entry for {key!r}", True
        if kind == "set":
            key = str(arguments.get(behavior.get("key_arg", "key")))
            server.store[key] = str(arguments.get(behavior.get("value_arg", "value")))
            return f"stored {key}", False
        if kind == "get":
            key = str(arguments.get(behavior.get("key_arg", "key")))
            if key in server.store:
                return server.store[key], False
            return f"nothing stored under {key!r}", True
        if kind == "list_items":
            return "\n".join(str(item) for item in behavior.get("items", [])), False
        if kind == "fail":
            return str(behavior.get("message", "tool failed")), True
        return canonical_text(arguments), False

    def _resources_list(
        self, server: _Server, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        rows = [
            {
                "uri": row["uri"],
                "name": row.get("name", row["uri"]),
                "mimeType": row.get("mimeType", "text/plain"),
            }
            for row in server.spec.get("resources", [])
        ]
        return self._result({"resources": rows})

    def _resources_read(
        self, server: _Server, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        uri = params.get("uri")
        row = next((item for item in server.spec.get("resources", []) if item["uri"] == uri), None)
        if row is None:
            return self._error(_ERR_RESOURCE_NOT_FOUND, f"resource not found: {uri}")
        self.resource_reads.add((server.name, row["uri"]))
        return self._result(
            {
                "contents": [
                    {
                        "uri": row["uri"],
                        "mimeType": row.get("mimeType", "text/plain"),
                        "text": row.get("text", ""),
                    }
                ]
            }
        )

    def _prompts_list(
        self, server: _Server, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        rows = [
            {
                "name": row["name"],
                "description": row.get("description", ""),
                "arguments": row.get("arguments", []),
            }
            for row in server.spec.get("prompts", [])
        ]
        return self._result({"prompts": rows})

    def _prompts_get(
        self, server: _Server, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        name = params.get("name")
        row = next((item for item in server.spec.get("prompts", []) if item["name"] == name), None)
        if row is None:
            return self._error(_ERR_INVALID_PARAMS, f"unknown prompt: {name}")
        text = row.get("text", "")
        for key, value in (params.get("arguments") or {}).items():
            text = text.replace("{{" + str(key) + "}}", str(value))
        return self._result(
            {
                "description": row.get("description", ""),
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            }
        )

    # --- predicates --------------------------------------------------------

    def listed_before_first_call(self, server_name: str) -> bool:
        server = self.servers.get(server_name)
        if server is None or server.first_call_at is None:
            return False
        return any(at < server.first_call_at for at in server.listed_at)

    def state_view(self) -> Any:
        return {name: server.view() for name, server in sorted(self.servers.items())}


bind_import_twin(__name__)
