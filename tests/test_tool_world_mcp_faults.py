#!/usr/bin/env python3
"""MCP fault kinds, the listed-before-first-call predicate, determinism, gold plans, and replay."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tests import tool_world_test_support as support
from tests.tool_world_mcp_support import (
    BOOK,
    FACTORY,
    FIND,
    PACK,
    SEEDS,
    SYNC,
    TRIAGE,
    call_tool,
    fault_env,
    handshake,
    mcp_call,
    plain_env,
    rpc,
    tool_names,
)

from tool_world import generate, records, replay
from tool_world.policies import scripted


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
