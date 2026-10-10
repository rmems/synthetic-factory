#!/usr/bin/env python3
"""Shared constants and helpers for the tickets-mcp test modules.

The MCP surface is exercised through the committed ``tickets-mcp`` pack by
two sibling modules (protocol, faults). They share the pack's task ids, the
JSON-RPC call wrappers that step the environment and parse its last
response line, and the environment builders that strip the fault menu, arm
one fault, or replace a server member.
"""

from __future__ import annotations

import dataclasses
import json

from tests import tool_world_test_support as support

from tool_world import faults as faults_mod

PACK = "tickets-mcp"
TRIAGE = "tickets.triage-t104"
FIND = "tickets.find-csv-ticket"
BOOK = "calendar.book-followup"
SYNC = "tickets.block-on-sync"
FACTORY = "tool-world-mcp-factory"
INIT_PARAMS = {"protocolVersion": "2025-06-18", "clientInfo": {"name": "test", "version": "0"}}
SEEDS = (1, 2, 3, 7)


def mcp_call(server: str, method: str, params: dict | None = None) -> dict:
    args: dict = {"server": server, "method": method}
    if params is not None:
        args["params"] = params
    return {"name": "mcp", "args": args}


def rpc(env, server: str, method: str, params: dict | None = None) -> dict:
    """Step the environment and parse the last JSON-RPC line of the observation."""
    text = env.step(mcp_call(server, method, params)).text
    return json.loads(text.splitlines()[-1])


def call_tool(env, server: str, name: str, arguments: dict) -> dict:
    return rpc(env, server, "tools/call", {"name": name, "arguments": arguments})


def handshake(env, server: str) -> None:
    rpc(env, server, "initialize", INIT_PARAMS)
    rpc(env, server, "notifications/initialized", {})


def tool_names(page: dict) -> list[str]:
    return [tool["name"] for tool in page["result"]["tools"]]


def plain_env(task_id: str, seed: int = 0):
    """An environment on the task with its fault menu removed, so no seed can interfere."""
    pack = support.load_pack(PACK)
    task = dataclasses.replace(pack.task(task_id), faults=())
    return support.env_mod.Environment(pack, task, seed)


def fault_env(task_id: str, kind: str, selector: dict, seed: int = 0):
    """An environment whose task declares exactly one always-armed fault of ``kind``."""
    pack = support.load_pack(PACK)
    task = pack.task(task_id)
    row = {
        "id": f"test-{kind}",
        "surface": "mcp",
        "kind": kind,
        "tool": "mcp",
        "selector": selector,
        "occurrence": 1,
        "probability_percent": 100,
        "marker": "unused",
        "recovery": [],
        "retry": True,
    }
    spec = faults_mod.fault_spec_from_row(row, "test")
    return support.env_mod.Environment(pack, dataclasses.replace(task, faults=(spec,)), seed)


def server_env(task_id: str, name: str, spec):
    """An environment on the pack with the server member ``name`` replaced by ``spec``."""
    pack = support.load_pack(PACK)
    patched = dataclasses.replace(pack, servers={**pack.servers, name: spec})
    return support.env_mod.Environment(patched, patched.task(task_id), 0)
