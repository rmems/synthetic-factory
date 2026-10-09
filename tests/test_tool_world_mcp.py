#!/usr/bin/env python3
"""The MCP surface through the tickets-mcp pack: protocol, pagination, errors, faults, replay."""

from __future__ import annotations

import copy
import dataclasses
import json
import tempfile
import unittest
from pathlib import Path

from tests import tool_world_test_support as support

from curate_coding import contains_hidden_reasoning_key
from tool_world import faults as faults_mod
from tool_world import generate, records, replay
from tool_world.policies import scripted
from tool_world.surfaces import mcp as mcp_mod

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
    pack = support.load_pack(PACK)
    patched = dataclasses.replace(pack, servers={**pack.servers, name: spec})
    return support.env_mod.Environment(patched, patched.task(task_id), 0)


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
        for cursor in ("page-2", "cursor-x", 2):
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


class FaultTests(unittest.TestCase):
    def test_schema_drift_announces_list_changed_and_rejects_the_stale_arguments(self):
        env = fault_env(
            TRIAGE, "schema_drift", {"method": "tools/call", "params.name": "set_status"}
        )
        handshake(env, "tickets")
        observation = env.step(
            mcp_call(
                "tickets",
                "tools/call",
                {"name": "set_status", "arguments": {"id": "T-104", "status": "in_progress"}},
            )
        )
        lines = observation.text.splitlines()
        self.assertEqual(
            json.loads(lines[0]), {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}
        )
        error = json.loads(lines[1])["error"]
        self.assertEqual(error["code"], -32602)
        self.assertIn("missing required property 'ticket_id'", error["message"])
        self.assertEqual(observation.fault_id, "test-schema_drift")
        view = env.surface("mcp").state_view()["tickets"]
        self.assertTrue(view["drifted"])
        self.assertEqual(view["store"], {})
        page = rpc(env, "tickets", "tools/list", {"cursor": "cursor-2"})
        self.assertEqual(
            page["result"]["tools"][0]["inputSchema"]["required"], ["ticket_id", "status"]
        )
        fixed = call_tool(
            env, "tickets", "set_status", {"ticket_id": "T-104", "status": "in_progress"}
        )
        self.assertFalse(fixed["result"]["isError"])
        self.assertIn(("tickets", "set_status"), env.surface("mcp").successful_calls)

    def test_rate_limited_returns_a_retryable_error_and_changes_nothing(self):
        env = fault_env(
            FIND, "rate_limited", {"method": "tools/call", "params.name": "list_tickets"}
        )
        handshake(env, "tickets")
        limited = call_tool(env, "tickets", "list_tickets", {})
        self.assertEqual(limited["error"]["code"], -32000)
        self.assertEqual(limited["error"]["data"], {"retryAfterMs": 1000})
        self.assertEqual(env.surface("mcp").state_view()["tickets"]["calls"], 0)
        self.assertEqual(env.events[-1].fault_id, "test-rate_limited")
        retried = call_tool(env, "tickets", "list_tickets", {})
        self.assertIn("T-104 open", retried["result"]["content"][0]["text"])
        self.assertIsNone(env.events[-1].fault_id)

    def test_server_restart_drops_the_session_and_the_store(self):
        env = fault_env(BOOK, "server_restart", {"method": "tools/call", "params.name": "get_slot"})
        handshake(env, "calendar")
        call_tool(env, "calendar", "book_slot", {"slot": "2026-10-12T15:00", "title": "follow-up"})
        lost = call_tool(env, "calendar", "get_slot", {"slot": "2026-10-12T15:00"})
        self.assertEqual(lost["error"]["code"], -32603)
        self.assertIn("server restarted", lost["error"]["message"])
        view = env.surface("mcp").state_view()["calendar"]
        self.assertEqual((view["initialized"], view["store"]), (False, {}))
        self.assertEqual(rpc(env, "calendar", "tools/list", {})["error"]["code"], -32600)
        handshake(env, "calendar")
        gone = call_tool(env, "calendar", "get_slot", {"slot": "2026-10-12T15:00"})
        self.assertTrue(gone["result"]["isError"])
        call_tool(env, "calendar", "book_slot", {"slot": "2026-10-12T15:00", "title": "follow-up"})
        held = call_tool(env, "calendar", "get_slot", {"slot": "2026-10-12T15:00"})
        self.assertEqual(held["result"]["content"][0]["text"], "follow-up")

    def test_empty_first_page_carries_a_cursor_to_the_real_first_page(self):
        env = fault_env(TRIAGE, "empty_first_page", {"method": "tools/list", "params.cursor": None})
        handshake(env, "tickets")
        empty = rpc(env, "tickets", "tools/list", {})
        self.assertEqual(empty["result"], {"tools": [], "nextCursor": "cursor-0"})
        followed = rpc(env, "tickets", "tools/list", {"cursor": "cursor-0"})
        self.assertEqual(tool_names(followed), ["list_tickets", "get_ticket"])
        self.assertEqual(followed["result"]["nextCursor"], "cursor-2")
        self.assertEqual(
            [event.fault_id for event in env.events[2:]], ["test-empty_first_page", None]
        )

    def test_a_schema_invalid_call_neither_counts_nor_fires(self):
        env = fault_env(
            FIND, "rate_limited", {"method": "tools/call", "params.name": "list_tickets"}
        )
        handshake(env, "tickets")
        malformed = env.step({"name": "mcp", "args": {"server": 7, "method": "tools/call"}})
        self.assertTrue(malformed.text.startswith("error: invalid arguments"))
        self.assertIsNone(malformed.fault_id)
        self.assertEqual(env.fault_engine.fired, ())
        call_tool(env, "tickets", "list_tickets", {})
        self.assertEqual(env.fault_engine.fired, ("test-rate_limited",))


class PredicateTests(unittest.TestCase):
    def test_listed_before_first_call_orders_the_listing_against_the_first_valid_call(self):
        listed_first = plain_env(TRIAGE)
        handshake(listed_first, "tickets")
        rpc(listed_first, "tickets", "tools/list", {})
        call_tool(listed_first, "tickets", "get_ticket", {"id": "T-104"})
        self.assertTrue(listed_first.surface("mcp").listed_before_first_call("tickets"))
        called_first = plain_env(TRIAGE)
        handshake(called_first, "tickets")
        call_tool(called_first, "tickets", "get_ticket", {"id": "T-104"})
        rpc(called_first, "tickets", "tools/list", {})
        self.assertFalse(called_first.surface("mcp").listed_before_first_call("tickets"))
        never_called = plain_env(TRIAGE)
        handshake(never_called, "tickets")
        rpc(never_called, "tickets", "tools/list", {})
        self.assertFalse(never_called.surface("mcp").listed_before_first_call("tickets"))
        self.assertFalse(never_called.surface("mcp").listed_before_first_call("mail"))

    def test_a_rejected_call_is_not_the_first_call(self):
        env = plain_env(TRIAGE)
        handshake(env, "tickets")
        call_tool(env, "tickets", "get_ticket", {})
        rpc(env, "tickets", "tools/list", {})
        call_tool(env, "tickets", "get_ticket", {"id": "T-104"})
        self.assertTrue(env.surface("mcp").listed_before_first_call("tickets"))

    def test_a_page_that_lists_no_tool_is_not_a_listing(self):
        selector = {"method": "tools/list", "params.cursor": None}
        ignored = fault_env(TRIAGE, "empty_first_page", selector)
        handshake(ignored, "tickets")
        self.assertEqual(rpc(ignored, "tickets", "tools/list", {})["result"]["tools"], [])
        call_tool(ignored, "tickets", "get_ticket", {"id": "T-104"})
        self.assertFalse(ignored.surface("mcp").listed_before_first_call("tickets"))
        self.assertEqual(ignored.surface("mcp").servers["tickets"].listed_at, [])
        followed = fault_env(TRIAGE, "empty_first_page", selector)
        handshake(followed, "tickets")
        rpc(followed, "tickets", "tools/list", {})
        rpc(followed, "tickets", "tools/list", {"cursor": "cursor-0"})
        call_tool(followed, "tickets", "get_ticket", {"id": "T-104"})
        self.assertTrue(followed.surface("mcp").listed_before_first_call("tickets"))
        self.assertEqual(followed.surface("mcp").servers["tickets"].listed_at, [4])

    def test_a_cursor_past_the_last_page_lists_nothing_and_counts_for_nothing(self):
        env = plain_env(TRIAGE)
        handshake(env, "tickets")
        beyond = rpc(env, "tickets", "tools/list", {"cursor": "cursor-99"})
        self.assertEqual(beyond["result"], {"tools": []})
        call_tool(env, "tickets", "get_ticket", {"id": "T-104"})
        self.assertFalse(env.surface("mcp").listed_before_first_call("tickets"))

    def test_verdict_labels_name_every_declared_predicate(self):
        env = support.make_env(PACK, TRIAGE, seed=1)
        scripted.run(env)
        verdict = env.verdict()
        self.assertTrue(verdict["success"])
        self.assertEqual(
            sorted(verdict["public"]), ["max_steps:n=18", "value_reported:value=T-104 in_progress"]
        )
        self.assertIn("tool_called:server=tickets,tool=set_status", verdict["hidden"])
        self.assertIn("resource_read:server=tickets,uri=tickets://policy", verdict["hidden"])


class DeterminismTests(unittest.TestCase):
    def test_state_view_is_sorted_and_deterministic(self):
        views = []
        for _ in range(2):
            env = plain_env(SYNC, seed=3)
            handshake(env, "calendar")
            call_tool(env, "calendar", "book_slot", {"slot": "2026-10-12T11:00", "title": "sync"})
            views.append((env.surface("mcp").state_view(), env.snapshot_digest()))
        self.assertEqual(views[0], views[1])
        self.assertEqual(list(views[0][0]), ["calendar", "tickets"])
        self.assertEqual(list(views[0][0]["calendar"]["store"]), ["2026-10-12T11:00"])

    def test_same_seed_produces_identical_observation_digests(self):
        digests = []
        for _ in range(2):
            env = support.make_env(PACK, TRIAGE, seed=7)
            scripted.run(env)
            digests.append(
                ([event.observation_sha256 for event in env.events], env.replay_digest())
            )
        self.assertEqual(digests[0], digests[1])
        self.assertGreaterEqual(len(digests[0][0]), 10)


class GoldTrajectoryTests(unittest.TestCase):
    def setUp(self):
        self.pack = support.load_pack(PACK)

    def test_every_gold_plan_succeeds_under_every_seed(self):
        for task in self.pack.tasks:
            for seed in SEEDS:
                with self.subTest(task=task.task_id, seed=seed):
                    env = support.env_mod.Environment(self.pack, task, seed)
                    trajectory = scripted.run(env)
                    self.assertTrue(env.verdict()["success"], env.verdict())
                    self.assertEqual(env.reported, task.gold[-1].tool_call["args"]["value"])
                    self.assertLessEqual(len(trajectory.steps), task.max_steps)

    def test_every_declared_fault_fires_and_is_recovered_under_some_seed(self):
        for task in self.pack.tasks:
            for spec in task.faults:
                with self.subTest(task=task.task_id, fault=spec.fault_id):
                    self.assertTrue(self._fires_and_recovers(task, spec.fault_id))

    def _fires_and_recovers(self, task, fault_id: str) -> bool:
        for seed in range(40):
            env = support.env_mod.Environment(self.pack, task, seed)
            trajectory = scripted.run(env)
            if fault_id in env.fault_engine.fired:
                return env.verdict()["success"] and trajectory.faults_recovered >= 1
        return False

    def test_perturbed_variants_are_labelled_by_the_environment(self):
        env = support.make_env(PACK, TRIAGE, seed=1)
        skipped = scripted.run(env, "skip_verification")
        self.assertFalse(env.verdict()["hidden"]["tool_called:server=tickets,tool=get_status"])
        self.assertFalse(skipped.gave_up)
        env = support.make_env(PACK, TRIAGE, seed=1)
        gave_up = scripted.run(env, "give_up_on_fault")
        self.assertTrue(gave_up.gave_up)
        self.assertFalse(env.verdict()["success"])
        env = support.make_env(PACK, TRIAGE, seed=1)
        mangled = scripted.run(env, "wrong_arg_type")
        self.assertTrue(mangled.steps[0].observation.startswith("error: invalid arguments"))
        self.assertTrue(env.verdict()["success"])
        record = records.build_record(
            env, mangled, records.RunContext("0" * 64, "run", "0" * 64), 1
        )
        self.assertEqual(record["curation"]["decision"], "measure")
        self.assertEqual(record["record_kind"], "mcp_session_v1")


class GenerateReplayTests(unittest.TestCase):
    def test_generate_and_replay_round_trip_on_a_private_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_dir = support.private_catalog(root / "catalog", (PACK,))
            request = generate.RunRequest(
                catalog_dir=catalog_dir,
                out_dir=root / "run",
                seed=1,
                count=4,
                factory=FACTORY,
                produced_at=support.PRODUCED_AT,
            )
            summary = generate.run(request)
            self.assertEqual(summary["accepted"], 4)
            gold_rows = [row for row in summary["rows"] if row["variant"] == "gold"]
            self.assertEqual({row["decision"] for row in gold_rows}, {"accept"})
            self.assertEqual({row["task_id"] for row in gold_rows}, {TRIAGE, FIND, BOOK, SYNC})
            catalog = support.catalog_mod.load_catalog(catalog_dir)
            result = replay.replay_run(root / "run", catalog)
            self.assertTrue(result["passed"], result)
            self.assertEqual(result["records"], summary["records"])
            lines = (root / "run" / "candidates.jsonl").read_text().splitlines()
            loaded = [json.loads(line) for line in lines]
            self.assertEqual({record["record_kind"] for record in loaded}, {"mcp_session_v1"})
            self._check_tampering_is_detected(loaded[0], catalog)

    def _check_tampering_is_detected(self, record: dict, catalog) -> None:
        """A rewritten observation, action, or outcome must break the fresh replay."""
        self.assertTrue(replay.replay_record(record, catalog).agreement)
        tampered = copy.deepcopy(record)
        tampered["training_view"]["steps"][2]["observation"] += " "
        mismatch = replay.replay_record(tampered, catalog)
        self.assertFalse(mismatch.agreement)
        self.assertIn("step 3: training_view observation text differs", mismatch.mismatches)
        tampered = copy.deepcopy(record)
        tampered["payload"]["actions"][2]["tool_call"]["args"]["method"] = "resources/list"
        mismatch = replay.replay_record(tampered, catalog)
        self.assertFalse(mismatch.agreement)
        self.assertIn("step 3: observation digest differs", mismatch.mismatches)
        self.assertIn("oracle.result_hash differs from the replay digest", mismatch.mismatches)
        tampered = copy.deepcopy(record)
        reward = tampered["training_view"]["reward"]
        reward["success"] = not reward["success"]
        mismatch = replay.replay_record(tampered, catalog)
        self.assertIn("reward.success differs from the replayed verdict", mismatch.mismatches)


if __name__ == "__main__":
    unittest.main()
