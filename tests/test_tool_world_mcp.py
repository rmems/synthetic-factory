#!/usr/bin/env python3
"""The MCP surface through the tickets-mcp pack: pack shape, the JSON-RPC protocol, and errors."""

from __future__ import annotations

import json
import unittest

from tests import tool_world_test_support as support
from tests.tool_world_mcp_support import (
    FACTORY,
    INIT_PARAMS,
    PACK,
    TRIAGE,
    call_tool,
    handshake,
    plain_env,
    rpc,
    server_env,
    tool_names,
)

from curate_coding import contains_hidden_reasoning_key
from tool_world.surfaces import mcp as mcp_mod


class PackTests(unittest.TestCase):
    def setUp(self):
        self.pack = support.load_pack(PACK)

    def test_pack_declares_two_servers_on_the_mcp_surface(self):
        self.assertEqual(self.pack.surfaces, ("mcp",))
        self.assertEqual(sorted(self.pack.servers), ["calendar", "tickets"])
        self.assertEqual(self.pack.servers["tickets"]["page_size"], 2)
        drifted = {row["name"]: row for row in self.pack.servers["tickets"]["drifted_tools"]}
        self.assertEqual(drifted["set_status"]["inputSchema"]["required"], ["ticket_id", "status"])
        self.assertEqual({task.factory for task in self.pack.tasks}, {FACTORY})

    def test_every_value_a_gold_plan_stores_is_checked_by_a_server_value_predicate(self):
        for task in self.pack.tasks:
            declared = {
                (p["server"], p["key"], p["value"])
                for name, p in task.hidden_predicates
                if name == "server_value"
            }
            for stored in self._stored_values(task):
                with self.subTest(task=task.task_id, stored=stored):
                    self.assertIn(stored, declared)

    def _stored_values(self, task) -> list[tuple[str, str, str]]:
        """``(server, key, value)`` for every ``set`` tool a gold plan calls."""
        stored = []
        for action in task.gold:
            args = action.tool_call["args"]
            if action.tool_call["name"] != "mcp" or args.get("method") != "tools/call":
                continue
            params = args["params"]
            tools = {row["name"]: row for row in self.pack.servers[args["server"]]["tools"]}
            behavior = tools[params["name"]].get("behavior", {})
            if behavior.get("kind") != "set":
                continue
            arguments = params["arguments"]
            key = str(arguments[behavior.get("key_arg", "key")])
            value = str(arguments[behavior.get("value_arg", "value")])
            stored.append((args["server"], key, value))
        return stored

    def test_license_block_is_the_counter_workspace_block_verbatim(self):
        self.assertEqual(self.pack.license, support.load_pack("counter-workspace").license)

    def test_pack_members_carry_no_hidden_reasoning_key_and_fit_the_budget(self):
        total = 0
        for path in sorted(self.pack.directory.rglob("*.json")):
            total += len(path.read_bytes())
            self.assertFalse(contains_hidden_reasoning_key(json.loads(path.read_text())), path)
        self.assertLess(total, 60_000)

    def test_tasks_together_declare_every_fault_kind_of_the_surface(self):
        kinds = {spec.kind for task in self.pack.tasks for spec in task.faults}
        self.assertEqual(kinds, set(mcp_mod.McpSurface.FAULT_KINDS))

    def test_malformed_server_members_are_refused_at_load(self):
        good = self.pack.servers["tickets"]
        bad_schema = [{"name": "t", "inputSchema": {"type": "object", "pattern": "x"}}]
        cases = (
            ({**good, "name": "other"}, "name equals its file stem"),
            ({**good, "page_size": 0}, "page_size"),
            ({**good, "page_size": None}, "page_size"),
            ({**good, "page_size": "2"}, "page_size"),
            ({**good, "tools": bad_schema}, "unsupported keyword 'pattern'"),
            ({**good, "tools": [{"inputSchema": {"type": "object"}}]}, "nonempty name"),
            ({**good, "drifted_tools": "none"}, "drifted_tools: must be a list"),
            ({**good, "resources": [{"name": "no uri"}]}, "string 'uri'"),
            ({**good, "resources": [{"uri": "tickets://x", "text": 5}]}, "string 'text'"),
            ({**good, "prompts": [{"text": "no name"}]}, "string 'name'"),
            ({**good, "prompts": [{"name": "triage"}]}, "string 'text'"),
        )
        for spec, needle in cases:
            with (
                self.subTest(needle=needle),
                support.refusal(self, support.cv.FINDING_PACK_FIELD_INVALID, needle),
            ):
                server_env(TRIAGE, "tickets", spec)

    def test_malformed_tool_members_are_refused_at_load(self):
        good = self.pack.servers["tickets"]
        lookup = good["tools"][1]["behavior"]
        untyped = {"properties": {"id": {"type": "string"}}}
        cases = (
            ({"inputSchema": untyped}, "inputSchema: type must be 'object'"),
            ({"behavior": "lookup"}, "behavior: must be an object whose kind"),
            ({"behavior": None}, "behavior: must be an object whose kind"),
            ({"behavior": {**lookup, "kind": "lookp"}}, "whose kind is one of"),
            ({"behavior": {**lookup, "table": ["T-104"]}}, "table: must map strings"),
            ({"behavior": {**lookup, "table": "T-104 open"}}, "table: must map strings"),
            ({"behavior": {**lookup, "table": {"T-104": 7}}}, "table: must map strings"),
            ({"behavior": {**lookup, "key_arg": 3}}, "key_arg: must be a string"),
            ({"behavior": {"kind": "set", "value_arg": []}}, "value_arg: must be a string"),
            ({"behavior": {"kind": "list_items", "items": 3}}, "items: must be a list"),
            ({"behavior": {"kind": "list_items", "items": [1]}}, "items: must be a list"),
            ({"behavior": {"kind": "fail", "message": 5}}, "message: must be a string"),
        )
        for patch, needle in cases:
            tools = [dict(row) for row in good["tools"]]
            tools[1] = {**tools[1], **patch}
            with (
                self.subTest(needle=needle),
                support.refusal(self, support.cv.FINDING_PACK_FIELD_INVALID, needle),
            ):
                server_env(TRIAGE, "tickets", {**good, "tools": tools})

    def test_a_server_without_page_size_lists_every_tool_on_one_page(self):
        spec = {key: value for key, value in self.pack.servers["tickets"].items()}
        del spec["page_size"]
        env = server_env(TRIAGE, "tickets", spec)
        handshake(env, "tickets")
        page = rpc(env, "tickets", "tools/list", {})
        self.assertEqual(len(tool_names(page)), 4)
        self.assertNotIn("nextCursor", page["result"])


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.env = plain_env(TRIAGE)
        self.surface = self.env.surface("mcp")

    def test_requests_before_initialize_are_invalid_requests(self):
        for method, params in (("tools/list", {}), ("tools/call", {"name": "list_tickets"})):
            with self.subTest(method=method):
                response = rpc(self.env, "tickets", method, params)
                self.assertEqual(response["error"]["code"], -32600)
                self.assertIn("initialize first", response["error"]["message"])
        self.assertFalse(self.surface.state_view()["tickets"]["initialized"])

    def test_initialize_reports_identity_and_initialized_marks_the_client_ready(self):
        response = rpc(self.env, "tickets", "initialize", INIT_PARAMS)
        self.assertEqual(response["result"]["serverInfo"], {"name": "tickets", "version": "1.4.0"})
        self.assertEqual(response["result"]["protocolVersion"], "2025-06-18")
        self.assertTrue(response["result"]["capabilities"]["tools"]["listChanged"])
        self.assertFalse(self.surface.state_view()["tickets"]["client_ready"])
        note = rpc(self.env, "tickets", "notifications/initialized", {})
        self.assertTrue(note["delivered"])
        self.assertNotIn("id", note)
        self.assertTrue(self.surface.state_view()["tickets"]["client_ready"])

    def test_tools_list_paginates_with_next_cursor(self):
        handshake(self.env, "tickets")
        first = rpc(self.env, "tickets", "tools/list", {})
        self.assertEqual(tool_names(first), ["list_tickets", "get_ticket"])
        self.assertEqual(first["result"]["nextCursor"], "cursor-2")
        second = rpc(self.env, "tickets", "tools/list", {"cursor": first["result"]["nextCursor"]})
        self.assertEqual(tool_names(second), ["set_status", "get_status"])
        self.assertNotIn("nextCursor", second["result"])
        self.assertEqual(self.surface.servers["tickets"].listed_at, [3, 4])

    def test_invalid_cursors_are_invalid_params(self):
        handshake(self.env, "tickets")
        for cursor in ("page-2", "cursor-x", 2, "cursor-", "cursor-\u00b2", "cursor-" + "9" * 12):
            with self.subTest(cursor=cursor):
                response = rpc(self.env, "tickets", "tools/list", {"cursor": cursor})
                self.assertEqual(response["error"]["code"], -32602)
                self.assertIn("invalid cursor", response["error"]["message"])

    def test_calendar_lists_on_one_page_and_keeps_its_own_session(self):
        handshake(self.env, "calendar")
        page = rpc(self.env, "calendar", "tools/list", {})
        self.assertEqual(tool_names(page), ["list_events", "book_slot", "get_slot"])
        self.assertNotIn("nextCursor", page["result"])
        self.assertEqual(rpc(self.env, "tickets", "tools/list", {})["error"]["code"], -32600)

    def test_unknown_tool_and_invalid_arguments_are_invalid_params(self):
        handshake(self.env, "tickets")
        unknown = call_tool(self.env, "tickets", "close_ticket", {"id": "T-104"})
        self.assertEqual(unknown["error"]["code"], -32602)
        self.assertIn("unknown tool: close_ticket", unknown["error"]["message"])
        bad_enum = call_tool(self.env, "tickets", "set_status", {"id": "T-104", "status": "done"})
        self.assertEqual(bad_enum["error"]["code"], -32602)
        self.assertIn("must be one of", bad_enum["error"]["message"])
        missing = call_tool(self.env, "tickets", "get_ticket", {})
        self.assertIn("missing required property 'id'", missing["error"]["message"])
        self.assertEqual(self.surface.state_view()["tickets"]["calls"], 0)
        self.assertEqual(self.surface.successful_calls, set())

    def test_tool_error_results_are_results_not_transport_failures(self):
        handshake(self.env, "tickets")
        miss = call_tool(self.env, "tickets", "get_ticket", {"id": "T-103"})
        self.assertNotIn("error", miss)
        self.assertTrue(miss["result"]["isError"])
        self.assertEqual(miss["result"]["content"][0]["text"], "no entry for 'T-103'")
        self.assertNotIn(("tickets", "get_ticket"), self.surface.successful_calls)
        hit = call_tool(self.env, "tickets", "get_ticket", {"id": "T-104"})
        self.assertFalse(hit["result"]["isError"])
        self.assertIn("CSV export drops the header row", hit["result"]["content"][0]["text"])
        self.assertIn(("tickets", "get_ticket"), self.surface.successful_calls)

    def test_set_status_round_trips_through_the_session_store(self):
        handshake(self.env, "tickets")
        empty = call_tool(self.env, "tickets", "get_status", {"id": "T-104"})
        self.assertTrue(empty["result"]["isError"])
        stored = call_tool(self.env, "tickets", "set_status", {"id": "T-104", "status": "blocked"})
        self.assertEqual(stored["result"]["content"][0]["text"], "stored T-104")
        read = call_tool(self.env, "tickets", "get_status", {"id": "T-104"})
        self.assertEqual(read["result"]["content"][0]["text"], "blocked")
        self.assertEqual(self.surface.state_view()["tickets"]["store"], {"T-104": "blocked"})

    def test_resources_read_returns_the_policy_and_unknown_uris_are_not_found(self):
        handshake(self.env, "tickets")
        listed = rpc(self.env, "tickets", "resources/list", {})
        self.assertEqual(
            [row["uri"] for row in listed["result"]["resources"]], ["tickets://policy"]
        )
        read = rpc(self.env, "tickets", "resources/read", {"uri": "tickets://policy"})
        content = read["result"]["contents"][0]
        self.assertEqual(content["mimeType"], "text/markdown")
        self.assertTrue(content["text"].startswith("# Triage policy"))
        self.assertIn(("tickets", "tickets://policy"), self.surface.resource_reads)
        missing = rpc(self.env, "tickets", "resources/read", {"uri": "tickets://nope"})
        self.assertEqual(missing["error"]["code"], -32002)

    def test_prompts_get_substitutes_arguments(self):
        handshake(self.env, "tickets")
        listed = rpc(self.env, "tickets", "prompts/list", {})
        self.assertEqual([row["name"] for row in listed["result"]["prompts"]], ["triage"])
        prompt = rpc(
            self.env,
            "tickets",
            "prompts/get",
            {"name": "triage", "arguments": {"ticket_id": "T-102"}},
        )
        text = prompt["result"]["messages"][0]["content"]["text"]
        self.assertTrue(text.startswith("Triage ticket T-102:"))
        self.assertNotIn("{{", text)
        unknown = rpc(self.env, "tickets", "prompts/get", {"name": "nope"})
        self.assertEqual(unknown["error"]["code"], -32602)

    def test_prompts_get_refuses_arguments_that_are_not_an_object(self):
        handshake(self.env, "tickets")
        for arguments in ("T-104", [1], 5, None):
            with self.subTest(arguments=arguments):
                params = {"name": "triage", "arguments": arguments}
                response = rpc(self.env, "tickets", "prompts/get", params)
                self.assertEqual(response["error"]["code"], -32602)
                self.assertEqual(
                    response["error"]["message"], "invalid params: arguments must be an object"
                )
        self.assertEqual(self.surface.request_id, 6)

    def test_an_unknown_behavior_kind_is_a_coded_refusal_not_an_echo(self):
        server = self.surface.servers["tickets"]
        with support.refusal(self, support.cv.FINDING_PACK_FIELD_INVALID, "'lookp' is not one of"):
            mcp_mod.McpSurface._behave(server, {"kind": "lookp"}, {"id": "T-104"})
        self.assertEqual(
            mcp_mod.McpSurface._behave(server, {}, {"id": "T-104"}), ('{"id":"T-104"}', False)
        )

    def test_tool_schema_rejects_unknown_servers_and_methods_before_the_surface(self):
        for args in (
            {"server": "mail", "method": "initialize"},
            {"server": "tickets", "method": "ping"},
        ):
            with self.subTest(args=args):
                observation = self.env.step({"name": "mcp", "args": args})
                self.assertTrue(observation.text.startswith("error: invalid arguments for mcp"))
        self.assertEqual(self.surface.request_id, 0)


if __name__ == "__main__":
    unittest.main()
