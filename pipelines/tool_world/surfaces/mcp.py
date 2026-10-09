#!/usr/bin/env python3
"""The MCP surface: simulated JSON-RPC 2.0 servers behind one ``mcp`` tool.

Each server is a pack member that ``mcp_servers`` checks at load, so a
request can never meet a shape the surface cannot serve: a malformed member
refuses the pack, a malformed request earns a coded JSON-RPC error.
Responses are canonical JSON-RPC envelopes; a pending
``notifications/tools/list_changed`` is delivered on the line before the
next response, as a transport would deliver it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .. import schema_lite
from .. import vocabulary as cv
from .._contract import bind_import_twin
from .base import Surface, ToolSpec, canonical_text
from .mcp_servers import Server, behave, check_server_spec

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
_CURSOR_PREFIX = "cursor-"


_CURSOR_DIGITS = 9


def _is_ascii_offset(text: str) -> bool:
    """Only plain decimal digits, bounded, so ``int`` can neither reject nor overflow it."""
    return 0 < len(text) <= _CURSOR_DIGITS and all("0" <= char <= "9" for char in text)


def _cursor_start(cursor: Any) -> int | None:
    """The page offset a cursor names, or None when it is not one the server issued."""
    if not isinstance(cursor, str) or not cursor.startswith(_CURSOR_PREFIX):
        return None
    offset = cursor[len(_CURSOR_PREFIX) :]
    return int(offset) if _is_ascii_offset(offset) else None


def _public_resource(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "uri": row["uri"],
        "name": row.get("name", row["uri"]),
        "mimeType": row.get("mimeType", "text/plain"),
    }


def _public_prompt(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "name": row["name"],
        "description": row.get("description", ""),
        "arguments": row.get("arguments", []),
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
        for name, spec in pack.servers.items():
            check_server_spec(name, spec)
        self.servers = {name: Server(spec) for name, spec in pack.servers.items()}
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
        self, server: Server, method: str, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        if method != "initialize" and not server.initialized:
            return self._error(
                _ERR_INVALID_REQUEST, "session not initialized: call initialize first"
            )
        handlers = {
            "initialize": lambda: self._initialize(server),
            "notifications/initialized": lambda: self._client_ready(server, method),
            "tools/list": lambda: self._tools_list(server, params, kind),
            "tools/call": lambda: self._tools_call(server, params),
            "resources/list": lambda: self._members(server, "resources", _public_resource),
            "resources/read": lambda: self._resources_read(server, params),
            "prompts/list": lambda: self._members(server, "prompts", _public_prompt),
            "prompts/get": lambda: self._prompts_get(server, params),
        }
        handler = handlers.get(method)
        if handler is None:
            return self._error(_ERR_METHOD_NOT_FOUND, f"method not found: {method}")
        return handler()

    # --- methods -----------------------------------------------------------

    def _initialize(self, server: Server) -> dict[str, Any]:
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

    @staticmethod
    def _client_ready(server: Server, method: str) -> dict[str, Any]:
        server.client_ready = True
        return {
            "jsonrpc": "2.0",
            "method": method,
            "delivered": True,
            "note": "notifications carry no response",
        }

    def _tools_list(
        self, server: Server, params: Mapping[str, Any], kind: str | None
    ) -> dict[str, Any]:
        cursor = params.get("cursor")
        start = 0 if cursor is None else _cursor_start(cursor)
        if start is None:
            return self._error(_ERR_INVALID_PARAMS, f"invalid cursor {cursor!r}")
        if kind == FAULT_EMPTY_FIRST_PAGE and cursor is None:
            return self._result({"tools": [], "nextCursor": f"{_CURSOR_PREFIX}0"})
        return self._result(self._tools_page(server, start))

    def _tools_page(self, server: Server, start: int) -> dict[str, Any]:
        """One page of the server's current tools; only a page naming a tool counts as a listing."""
        tools = server.tools()
        size = server.spec.get("page_size") or (len(tools) or 1)
        page = tools[start : start + size]
        if page:
            server.listed_at.append(len(self.env.events) + 1)
        result: dict[str, Any] = {"tools": [self._public_tool(tool) for tool in page]}
        if start + size < len(tools):
            result["nextCursor"] = f"{_CURSOR_PREFIX}{start + size}"
        return result

    @staticmethod
    def _public_tool(tool: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "inputSchema": tool["inputSchema"],
        }

    def _tools_call(self, server: Server, params: Mapping[str, Any]) -> dict[str, Any]:
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
        text, is_error = self._behave(server, tool.get("behavior", {}), arguments)
        if not is_error:
            self.successful_calls.add((server.name, name))
        return self._result({"content": [{"type": "text", "text": text}], "isError": is_error})

    # The declared behavior runs through the class seam, so a caller can reach it here.
    _behave = staticmethod(behave)

    def _members(self, server: Server, key: str, public: Callable[[Any], Any]) -> dict[str, Any]:
        """The server's ``key`` member list, each row in its public shape, as a result."""
        return self._result({key: [public(row) for row in server.spec.get(key, [])]})

    def _resources_read(self, server: Server, params: Mapping[str, Any]) -> dict[str, Any]:
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
                        "text": row["text"],
                    }
                ]
            }
        )

    def _prompts_get(self, server: Server, params: Mapping[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        row = next((item for item in server.spec.get("prompts", []) if item["name"] == name), None)
        if row is None:
            return self._error(_ERR_INVALID_PARAMS, f"unknown prompt: {name}")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, Mapping):
            return self._error(_ERR_INVALID_PARAMS, "invalid params: arguments must be an object")
        text = row["text"]
        for key, value in arguments.items():
            text = text.replace("{{" + str(key) + "}}", str(value))
        return self._result(
            {
                "description": row.get("description", ""),
                "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
            }
        )

    # --- predicates --------------------------------------------------------

    def stored_value(self, server_name: str, key: str) -> str | None:
        """The value a ``set`` tool stored under ``key``, or None when nothing is stored there."""
        server = self.servers.get(server_name)
        return None if server is None else server.store.get(key)

    def listed_before_first_call(self, server_name: str) -> bool:
        server = self.servers.get(server_name)
        if server is None or server.first_call_at is None:
            return False
        return any(at < server.first_call_at for at in server.listed_at)

    def state_view(self) -> Any:
        return {name: server.view() for name, server in sorted(self.servers.items())}


bind_import_twin(__name__)
