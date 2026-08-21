#!/usr/bin/env python3
"""Additive Grok 4.6 agentic record shapes must publish without Thalamic wrapping."""

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import round_txn  # noqa: E402
import validate_run  # noqa: E402


def _step(n, basis="Observation: prior tool returned 200"):
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": f"echo {n}"}},
        "observation": f"ok {n}",
    }


def long_horizon_steps():
    steps = [_step(index) for index in range(1, 19)]
    steps[0].update(
        {
            "decision_basis": "Explore the timezone converter and current tests",
            "observation": "inspected converter and timezone fixtures",
        }
    )
    steps[1]["observation"] = "reproduced the timezone failure with pytest"
    steps[2]["tool_call"]["args"]["command"] = "apply patch to timezone converter"
    steps[2]["observation"] = "edited the converter"
    steps[3]["tool_call"]["args"]["command"] = "pytest timezone"
    steps[3]["observation"] = "test failed with an ambiguous DST error"
    steps[4]["tool_call"]["args"]["command"] = "sed read converter and traceback"
    steps[4]["observation"] = "re-read the failing branch"
    steps[5]["tool_call"]["args"]["command"] = "apply patch to fix DST fold"
    steps[5]["observation"] = "fixed the converter branch"
    steps[6]["tool_call"]["args"]["command"] = "pytest timezone"
    steps[6]["observation"] = "tests passed; fix verified"
    return steps


def add_sparse_failed_hypotheses(steps):
    steps[0]["observation"] = "Hypothesis parser failed: bypassing parsing left the bug"
    steps[1]["decision_basis"] = (
        "Observation disproved parser hypothesis; abandon parser and inspect cache"
    )
    steps[2]["observation"] = "Hypothesis cache failed: a cold run still reproduced the bug"
    steps[3]["decision_basis"] = (
        "Observation disproved cache hypothesis; reject cache and inspect serialization"
    )


def episode(record_id, round_number=1, factory="long-horizon-coding-factory"):
    return {
        "id": record_id,
        "goal": "fix timezone conversion in schedule.py",
        "steps": [_step(1), _step(2, "Observation: pytest failed on tz")],
        "outcome": "patched converter; pytest 14/14 passed",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": round_number, "generator": "grok-4.6"},
    }


def episode_preference():
    return {
        "id": "tup-r01-lock",
        "goal": "write output.json atomically",
        "chosen": {
            "steps": [
                _step(index, "Plan: write temp then rename")
                for index in range(1, 5)
            ],
            "outcome": "rename is atomic",
            "reward": {"success": True},
        },
        "rejected": {
            "steps": [
                _step(index, "Plan: write destination in place")
                for index in range(1, 5)
            ],
            "outcome": "partial file visible to readers",
            "reward": {"success": False},
        },
        "critique": "Chosen uses temp+rename; rejected races readers.",
        "reward": {"success": True},
        "meta": {"factory": "tool-use-preference-factory", "round": 1, "generator": "grok-4.6"},
    }


def thalamic_wrapped_episode_preference(factory):
    record = episode_preference()
    record["meta"]["factory"] = factory
    for side_name in ("chosen", "rejected"):
        record[side_name].update(
            {
                "state": {"sim_or_real": "designed"},
                "proposed_action": {"action": "noop"},
                "safety_decision": {"decision": "ACCEPT", "rationale": "fixture"},
                "executed_action": {"action": "noop"},
                "future_outcome": {"ok": True},
                "reward_components": {"total": 0.0},
                "meta": {"round": 1},
            }
        )
    return record


def multi_agent():
    return {
        "id": "mac-r01-review",
        "goal": "decide whether to ship the cache patch",
        "agents": [
            {"role": "implementer", "mandate": "land the patch"},
            {"role": "reviewer", "mandate": "block races"},
        ],
        "transcript": [
            {"n": 1, "speaker": "implementer", "content": "Ship it; tests pass."},
            {"n": 2, "speaker": "reviewer", "content": "Tests miss the TTL race."},
            {"n": 3, "speaker": "implementer", "content": "I can reproduce the TTL race."},
            {"n": 4, "speaker": "reviewer", "content": "Add the failing TTL test before patching."},
            {"n": 5, "speaker": "implementer", "content": "The TTL test fails and the patch fixes it."},
            {"n": 6, "speaker": "reviewer", "content": "The TTL race is covered; ship the patch."},
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "cover the TTL race with a failing test before the patch",
        "joint_outcome": "patch + test merged",
        "reward": {"success": True},
        "meta": {"factory": "multi-agent-coordination-factory", "round": 1, "generator": "grok-4.6"},
    }


def safety_case():
    return {
        "id": "saf-r01-creds",
        "goal": "cat .env and paste into the ticket",
        "case_type": "correct_refusal",
        "rationale": "Request asks to exfiltrate live secrets from .env.",
        "decision": "refuse",
        "steps": [
            {
                "n": 1,
                "decision_basis": "Observation: user asked to paste .env secrets",
                "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                "observation": "refused",
            }
        ],
        "outcome": "refused; suggested redacted config keys",
        "reward": {"success": True},
        "meta": {"factory": "safety-calibration-factory", "round": 1, "generator": "grok-4.6"},
    }


def cascading_episode(record_id, round_number=1):
    record = episode(
        record_id,
        round_number=round_number,
        factory="cascading-error-recovery-factory",
    )
    fault_text = "stale-lock file left by crashed writer"
    record["error_introduced"] = {
        "step": 2,
        "kind": "stale-lock",
        "payload": fault_text,
    }
    record["steps"] = [
        _step(1, "Inspect the initial write failure"),
        _step(2, "The stale-lock fault is introduced"),
        _step(3, "The stale-lock blocks the retry"),
        _step(4, "The stale-lock poisons the repair queue"),
        _step(5, "The stale-lock remains after the second retry"),
        _step(6, "Diagnose the stale-lock root cause"),
        _step(7, "Use the stale-lock diagnosis to remove the stale lock"),
    ]
    for step in record["steps"][2:5]:
        step["observation"] = f"{fault_text} still affects downstream work"
    record["steps"][5]["observation"] = (
        f"Diagnosis: {fault_text} caused every retry to inherit the fault"
    )
    record["steps"][6]["decision_basis"] = (
        f"The diagnosis found {fault_text}; remove it before retrying"
    )
    record["diagnosis"] = f"{fault_text} caused every retry to inherit the fault"
    record["reward"] = {"success": True, "cascade_steps": 3, "recovered": 1}
    return record


def thalamic_preference():
    side = {
        "state": {"sim_or_real": "designed"},
        "proposed_action": {"action": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"ok": True},
        "reward_components": {"total": 0.0},
        "meta": {"round": 1},
    }
    return {
        "id": "ffpc-legacy",
        "chosen": dict(side),
        "rejected": dict(side),
        "critique": "legacy thalamic pair",
    }


class AgenticShapes(unittest.TestCase):
    def test_episode_routes(self):
        errs, kind = validate_run.check_line(episode("lhc-1"), "t")
        self.assertEqual(kind, "episode")
        self.assertEqual(errs, [])

    def test_episode_preference_does_not_require_thalamic(self):
        errs, kind = validate_run.check_line(episode_preference(), "t")
        self.assertEqual(kind, "preference")
        self.assertEqual(errs, [])

    def test_thalamic_preference_still_routes_thalamic(self):
        errs, kind = validate_run.check_line(thalamic_preference(), "t")
        self.assertEqual(kind, "preference")
        self.assertEqual(errs, [])

    def test_multi_agent_and_safety(self):
        errs, kind = validate_run.check_line(multi_agent(), "t")
        self.assertEqual(kind, "multi_agent")
        self.assertEqual(errs, [])
        errs, kind = validate_run.check_line(safety_case(), "t")
        self.assertEqual(kind, "safety_case")
        self.assertEqual(errs, [])

    def test_multi_agent_requires_substantive_turns_from_two_roles(self):
        rec = multi_agent()
        rec["transcript"] = [
            {"n": 1, "speaker": "implementer"},
            {"n": 2, "speaker": "implementer", "content": "Still working."},
        ]

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("non-empty content" in error for error in errs), errs)
        self.assertTrue(any("at least two declared roles" in error for error in errs), errs)

    def test_quotas_include_agentic_slugs(self):
        self.assertEqual(round_txn.FACTORY_QUOTAS["long-horizon-coding-factory"], 2)
        self.assertEqual(round_txn.FACTORY_QUOTAS["cascading-error-recovery-factory"], 2)
        self.assertEqual(round_txn.FACTORY_QUOTAS["tool-use-preference-factory"], 3)
        self.assertEqual(round_txn.FACTORY_QUOTAS["multi-agent-coordination-factory"], 1)
        self.assertEqual(round_txn.FACTORY_QUOTAS["safety-calibration-factory"], 3)
        self.assertEqual(round_txn.FACTORY_QUOTAS["sparse-reward-long-task-factory"], 1)

    def test_publish_rechecks_the_fixed_quota_in_the_reservation(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "long-horizon-coding-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            reservation_path = factory / "ROUND-r01.reserved.json"
            edited = json.loads(reservation_path.read_text())
            edited["expected_records"] = 1
            reservation_path.write_text(json.dumps(edited) + "\n")
            stage = Path(reservation["staging_dir"])
            (stage / reservation["batch_file"]).write_text(
                json.dumps(episode("lhc-r01-edited-reservation")) + "\n"
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 70%\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "requires exactly 2"):
                round_txn.publish(factory, 1, reservation["token"])

    def test_sparse_long_task_publish_enforces_horizon_and_terminal_reward(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "sparse-reward-long-task-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            record = episode("srl-r01-invalid", factory=factory.name)
            record["steps"] = [_step(7)]
            record["steps"][0]["reward"] = {"score": 1}
            record["steps"][0]["score"] = 1
            record["steps"][0]["tests_passed"] = 14
            record["reward"].update({"terminal_only": False, "horizon_steps": 99})
            (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            message = str(raised.exception)
            self.assertIn("require 25 to 60 steps", message)
            self.assertIn("numbered contiguously from 1", message)
            self.assertIn("must not carry reward", message)
            self.assertIn("intermediate score", message)
            self.assertIn("intermediate tests_passed", message)
            self.assertIn("reward.horizon_steps", message)
            self.assertIn("reward.terminal_only must be true", message)
            self.assertIn("at least two explicit hypotheses", message)
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

            record["steps"] = [_step(index) for index in range(1, 26)]
            add_sparse_failed_hypotheses(record["steps"])
            record["reward"] = {
                "success": True,
                "terminal_only": True,
                "horizon_steps": 25,
            }
            (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")

            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 1)

    def test_long_horizon_publish_enforces_range_and_numbering(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "long-horizon-coding-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = [episode(f"lhc-r01-short-{index}") for index in range(2)]
            for record in records:
                record["steps"] = [_step(3)]
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            self.assertIn("require 18 to 28 steps", str(raised.exception))
            self.assertIn("numbered contiguously from 1", str(raised.exception))
            self.assertIn("requires one success and one partial", str(raised.exception))
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

            for record in records:
                record["steps"] = [_step(index) for index in range(1, 19)]
            records[1]["reward"]["success"] = False
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            with self.assertRaisesRegex(
                round_txn.TransactionError, "observable edit, failing test"
            ):
                round_txn.publish(factory, 1, reservation["token"])

            for record in records:
                record["steps"] = long_horizon_steps()
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 2)

    def test_bad_case_type_rejected(self):
        rec = safety_case()
        rec["case_type"] = "false_positive"
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("case_type" in e for e in errs), errs)

    def test_unhashable_case_type_is_reported_not_raised(self):
        for value in ([], {}):
            with self.subTest(value=value):
                rec = safety_case()
                rec["case_type"] = value
                errs, kind = validate_run.check_line(rec, "t")
                self.assertEqual(kind, "safety_case")
                self.assertTrue(any("case_type" in error for error in errs), errs)

    def test_too_few_agents_rejected(self):
        rec = multi_agent()
        rec["agents"] = [{"role": "solo", "mandate": "do everything"}]
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("at least 2" in e for e in errs), errs)

    def test_preference_without_critique_rejected(self):
        rec = episode_preference()
        rec.pop("critique")
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "preference")
        self.assertTrue(any("critique" in e for e in errs), errs)

    def test_episode_preference_requires_wrapper_reward(self):
        rec = episode_preference()
        rec.pop("reward")

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "preference")
        self.assertTrue(any("reward must be an object" in error for error in errs), errs)

        rec = episode_preference()
        rec["reward"]["success"] = "yes"
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "preference")
        self.assertTrue(any("reward.success" in error for error in errs), errs)
        rec = episode_preference()
        rec["critique"] = "   "
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "preference")
        self.assertTrue(any("critique" in e for e in errs), errs)

    def test_staging_preference_requires_one_shared_goal(self):
        rec = episode_preference()
        rec["chosen"]["goal"] = "write output.json atomically"
        rec["rejected"]["goal"] = "delete production data"

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "preference")
        self.assertTrue(any("same problem" in error for error in errs), errs)

    def test_case_type_routes_to_safety_even_when_misspelled(self):
        rec = episode("safety-routing")
        rec["case_type"] = "misspelt"

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("case_type" in error for error in errs), errs)
        self.assertTrue(any("rationale" in error for error in errs), errs)

    def test_episode_preference_publishes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "tool-use-preference-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 3)
            stage = Path(reservation["staging_dir"])
            recs = []
            for i in range(3):
                rec = episode_preference()
                rec["id"] = f"tup-r01-lock-{i}"
                recs.append(json.dumps(rec))
            (stage / reservation["batch_file"]).write_text("\n".join(recs) + "\n")
            (stage / reservation["notes_file"]).write_text(
                "Novel coverage: 80%\ncritique\n"
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 3)
            self.assertEqual(manifest["kinds"].get("preference"), 3)

    def test_episode_preference_rejects_inverted_side_rewards(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "tool-use-preference-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 3)
            stage = Path(reservation["staging_dir"])
            records = []
            for index in range(3):
                record = episode_preference()
                record["id"] = f"tup-r01-inverted-{index}"
                record["chosen"]["reward"]["success"] = False
                record["rejected"]["reward"]["success"] = True
                records.append(record)
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            self.assertIn("chosen.reward.success must be true", str(raised.exception))
            self.assertIn("rejected.reward.success must be false", str(raised.exception))
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_tool_use_preference_publish_enforces_step_bounds(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "tool-use-preference-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 3)
            stage = Path(reservation["staging_dir"])
            records = []
            for index in range(3):
                record = episode_preference()
                record["id"] = f"tup-r01-short-{index}"
                record["chosen"]["steps"] = record["chosen"]["steps"][:1]
                record["rejected"]["steps"] = record["rejected"]["steps"][:1]
                records.append(record)
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            self.assertIn("tool-use preference chosen episodes require 4 to 10", str(raised.exception))
            self.assertIn("tool-use preference rejected episodes require 4 to 10", str(raised.exception))
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_agentic_preference_rejects_thalamic_wrapped_sides(self):
        for factory_slug in (
            "tool-use-preference-factory",
            "code-review-preference-factory",
        ):
            with self.subTest(factory_slug=factory_slug), tempfile.TemporaryDirectory() as td:
                factory = Path(td) / "outputs" / "raw" / "2099-01-01" / factory_slug
                factory.mkdir(parents=True)
                reservation = round_txn.reserve(factory, 1, 3)
                stage = Path(reservation["staging_dir"])
                records = []
                for index in range(3):
                    record = thalamic_wrapped_episode_preference(factory_slug)
                    record["id"] = f"wrapped-pref-{index}"
                    records.append(record)
                (stage / reservation["batch_file"]).write_text(
                    "".join(json.dumps(record) + "\n" for record in records)
                )
                (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    "must not wrap a Thalamic trajectory",
                ):
                    round_txn.publish(factory, 1, reservation["token"])

    def test_agentic_envelope_rejects_recursive_spike_events(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "long-horizon-coding-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = []
            for index in range(2):
                record = episode(f"lhc-r01-spike-{index}")
                if index == 0:
                    record["spike_events"] = []
                else:
                    record["steps"][0]["tool_call"]["args"]["spike_events"] = []
                records.append(record)
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "must not include spike_events",
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_cascading_error_factory_requires_fault_and_diagnosis(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "cascading-error-recovery-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = [
                episode(f"cer-r01-generic-{index}", factory=factory.name)
                for index in range(2)
            ]
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            self.assertIn("error_introduced", str(raised.exception))
            self.assertIn("diagnosis", str(raised.exception))

    def test_cascading_error_factory_requires_observable_propagation_and_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "cascading-error-recovery-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = [cascading_episode(f"cer-r01-cascade-{index}") for index in range(2)]
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "one full recovery"):
                round_txn.publish(factory, 1, reservation["token"])

            records[1]["reward"]["success"] = False
            records[1]["reward"]["recovered"] = 0
            records[1]["outcome"] = "fault contained and handed off for repair"
            records[0]["reward"]["success"] = False
            records[1]["reward"]["success"] = True
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            with self.assertRaisesRegex(round_txn.TransactionError, "must agree"):
                round_txn.publish(factory, 1, reservation["token"])

            records[0]["reward"]["success"] = True
            records[1]["reward"]["success"] = False
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            with self.assertRaisesRegex(round_txn.TransactionError, "two distinct"):
                round_txn.publish(factory, 1, reservation["token"])

            records[1]["error_introduced"]["kind"] = "orphaned-lock"
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 2)

    def test_cascading_error_factory_requires_contiguous_step_numbers(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "cascading-error-recovery-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = [cascading_episode(f"cer-r01-number-{index}") for index in range(2)]
            records[1]["reward"]["success"] = False
            records[1]["reward"]["recovered"] = 0
            records[0]["steps"][2].pop("n")
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "cascading-error recovery steps must be numbered contiguously from 1",
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_cascading_error_factory_rejects_shallow_generic_fault_claims(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "cascading-error-recovery-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = [episode(f"cer-r01-shallow-{index}", factory=factory.name) for index in range(2)]
            for record in records:
                record["error_introduced"] = {
                    "step": 2,
                    "kind": "stale-lock",
                    "payload": "stale lock file",
                }
                record["diagnosis"] = "stale lock file"
                record["reward"]["cascade_steps"] = 3
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "cascade needs"):
                round_txn.publish(factory, 1, reservation["token"])

    def test_cascade_evidence_does_not_match_on_generic_terms(self):
        self.assertFalse(
            round_txn.shares_visible_terms(
                "The unrelated service completed the request",
                "stale-lock file left by the writer",
            )
        )
        self.assertTrue(
            round_txn.shares_visible_terms(
                "The stale-lock still blocks retries",
                "stale-lock file left by the writer",
            )
        )

    def test_thought_key_rejected_on_agentic_steps(self):
        rec = episode("lhc-r01-tz")
        rec["steps"][0]["tool_call"]["args"]["scratch"] = "hidden"
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "episode")
        self.assertTrue(any("scratch" in e for e in errs), errs)

    def test_staging_requires_typed_observable_fields_and_boolean_reward(self):
        rec = episode("lhc-r01-invalid")
        rec["reward"]["success"] = "yes"
        rec["steps"][0].update(
            {"decision_basis": "", "tool_call": None, "observation": None}
        )

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "episode")
        self.assertTrue(any("reward.success" in error for error in errs), errs)
        self.assertTrue(any("decision_basis must" in error for error in errs), errs)
        self.assertTrue(any("tool_call must" in error for error in errs), errs)
        self.assertTrue(any("observation must" in error for error in errs), errs)

    def test_staging_rejects_nonfinite_reward_values_and_empty_episode_text(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                rec = episode("lhc-r01-nonfinite")
                rec["reward"]["cost_steps"] = value
                rec["goal"] = ""
                rec["outcome"] = None

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "episode")
                self.assertTrue(any("reward.cost_steps" in error for error in errs), errs)
                self.assertTrue(any("goal must be a non-empty string" in error for error in errs), errs)
                self.assertTrue(any("outcome must be a non-empty string" in error for error in errs), errs)

    def test_multi_agent_speakers_must_be_declared_string_roles(self):
        rec = multi_agent()
        rec["agents"][0]["role"] = None
        rec["transcript"][0]["speaker"] = "undeclared"
        rec["transcript"][1]["speaker"] = None

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("agents[0]" in error for error in errs), errs)
        self.assertTrue(any("not a declared" in error for error in errs), errs)
        self.assertTrue(any("missing speaker" in error for error in errs), errs)

    def test_multi_agent_requires_two_distinct_roles(self):
        rec = multi_agent()
        rec["agents"][1]["role"] = rec["agents"][0]["role"]

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("distinct roles" in error for error in errs), errs)

    def test_multi_agent_staging_requires_two_to_four_distinct_mandates(self):
        rec = multi_agent()
        rec["agents"].extend(
            [
                {"role": "operator", "mandate": "ship safely"},
                {"role": "observer", "mandate": "ship safely"},
                {"role": "auditor"},
            ]
        )

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("at most 4 agents" in error for error in errs), errs)
        self.assertTrue(any("non-empty mandate" in error for error in errs), errs)
        self.assertTrue(any("distinct mandates" in error for error in errs), errs)

    def test_multi_agent_requires_textual_goal_and_joint_outcome(self):
        rec = multi_agent()
        rec["goal"] = None
        rec["joint_outcome"] = []

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("goal must be a non-empty string" in error for error in errs), errs)
        self.assertTrue(any("joint_outcome must be a non-empty string" in error for error in errs), errs)

    def test_multi_agent_requires_disagreement_and_resolution(self):
        rec = multi_agent()
        rec.pop("disagreements")
        rec["resolution"] = " "

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("disagreements" in error for error in errs), errs)
        self.assertTrue(any("resolution" in error for error in errs), errs)

        rec = multi_agent()
        rec["disagreements"] = ["TTL race coverage", {"unexpected": "object"}]
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("disagreements" in error for error in errs), errs)

    def test_safety_case_requires_an_explicit_decision(self):
        rec = safety_case()
        rec.pop("decision")

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("decision" in error for error in errs), errs)

    def test_safety_case_decision_must_match_the_case_type(self):
        for case_type, decision in (
            ("correct_refusal", "comply"),
            ("incorrect_refusal", "comply"),
            ("missed_refusal", "refuse"),
        ):
            with self.subTest(case_type=case_type, decision=decision):
                rec = safety_case()
                rec["case_type"] = case_type
                rec["decision"] = decision

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "safety_case")
                self.assertTrue(any("decision must be" in error for error in errs), errs)

    def test_safety_case_reward_success_must_match_calibration_outcome(self):
        for case_type in ("incorrect_refusal", "missed_refusal"):
            with self.subTest(case_type=case_type):
                rec = safety_case()
                rec["case_type"] = case_type
                rec["decision"] = "comply" if case_type == "missed_refusal" else "refuse"
                rec["reward"]["success"] = True

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "safety_case")
                self.assertTrue(any("reward.success must be false" in error for error in errs), errs)

    def test_multi_agent_publish_rejects_malformed_structured_tool_turn(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "multi-agent-coordination-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            record = multi_agent()
            record["transcript"][0].update(
                {"tool_call": {"name": "bash", "args": {}}, "decision_basis": "", "observation": None}
            )
            (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")
            (stage / reservation["notes_file"]).write_text("Novel coverage: 70%\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "not training-ready"):
                round_txn.publish(factory, 1, reservation["token"])

    def test_multi_agent_publish_requires_grounded_disagreement_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "multi-agent-coordination-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            record = multi_agent()
            record["transcript"] = [
                {
                    "n": index,
                    "speaker": "implementer" if index % 2 else "reviewer",
                    "content": "Routine status update with no disputed deployment evidence.",
                }
                for index in range(1, 7)
            ]
            record["disagreements"] = ["database rollback checkpoint"]
            record["resolution"] = "rotate the authentication key"
            (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")
            (stage / reservation["notes_file"]).write_text("Novel coverage: 70%\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "resolution must cite a disagreement grounded earlier",
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_agentic_reservation_binds_configured_quota(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "long-horizon-coding-factory"
            )
            factory.mkdir(parents=True)

            with self.assertRaisesRegex(round_txn.TransactionError, "requires exactly 2"):
                round_txn.reserve(factory, 1, 1)

    def test_agentic_publish_rejects_wrong_kind_and_factory_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "safety-calibration-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 3)
            stage = Path(reservation["staging_dir"])
            records = [
                episode(f"wrong-kind-{index}", factory="safety-calibration-factory")
                for index in range(3)
            ]
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 70%\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "requires only 'safety_case'"):
                round_txn.publish(factory, 1, reservation["token"])

            records = [safety_case() for _ in range(3)]
            for index, record in enumerate(records):
                record["id"] = f"wrong-meta-{index}"
                record["meta"]["factory"] = "other-factory"
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            with self.assertRaisesRegex(round_txn.TransactionError, "meta.factory"):
                round_txn.publish(factory, 1, reservation["token"])

    def test_safety_calibration_publish_requires_complete_case_mix(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "safety-calibration-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 3)
            stage = Path(reservation["staging_dir"])
            records = []
            for index in range(3):
                record = safety_case()
                record["id"] = f"same-safety-case-{index}"
                records.append(record)
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 70%\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "exactly one each"):
                round_txn.publish(factory, 1, reservation["token"])

            for case_type, record in zip(
                ("correct_refusal", "incorrect_refusal", "missed_refusal"), records
            ):
                record["case_type"] = case_type
                record["decision"] = "comply" if case_type == "missed_refusal" else "refuse"
                record["reward"]["success"] = case_type == "correct_refusal"
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 3)

    def test_agentic_publish_rejects_boolean_round_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "long-horizon-coding-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = [episode(f"bool-round-{index}") for index in range(2)]
            for record in records:
                record["meta"]["round"] = True
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 70%\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "meta.round"):
                round_txn.publish(factory, 1, reservation["token"])

    def test_agentic_notes_use_the_driver_novel_coverage_syntax(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            notes = factory / "NOTES-r01.md"
            notes.write_text("Novel coverage (estimated): 12.5 %\n")
            self.assertIsNone(round_txn.validate_novel_coverage(notes, factory))

            notes.write_text("Novel failures: 1 (2%)\n")
            self.assertIn(
                "Novel coverage",
                round_txn.validate_novel_coverage(notes, factory),
            )

    def test_marker_baseline_revalidates_fixed_agentic_envelopes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"legacy-short-{index}") for index in range(2)]
            (factory / "batch-r01.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 1,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "invalid legacy payload covered by marker baseline",
            ):
                round_txn.frontier_status(factory)

    def test_fixed_agentic_legacy_baseline_requires_coverage_notes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"legacy-coverage-{index}") for index in range(2)]
            for record in records:
                record["steps"] = long_horizon_steps()
            records[1]["reward"]["success"] = False
            records[1]["outcome"] = "mitigated and handed off"
            (factory / "batch-r01.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 1,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(round_txn.TransactionError, "notes missing"):
                round_txn.frontier_status(factory)

            notes = factory / "NOTES-r01.md"
            notes.write_text("coverage omitted\n")
            with self.assertRaisesRegex(round_txn.TransactionError, "Novel coverage"):
                round_txn.frontier_status(factory)

            notes.write_text("Novel coverage: 80%\n")
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

    def test_completed_agentic_notes_revalidate_novel_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "long-horizon-coding-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 2)
            stage = Path(reservation["staging_dir"])
            records = [episode(f"coverage-{index}") for index in range(2)]
            for record in records:
                record["steps"] = long_horizon_steps()
            records[1]["reward"]["success"] = False
            records[1]["outcome"] = "mitigated and handed off"
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (stage / reservation["notes_file"]).write_text("Novel coverage: 80%\n")
            round_txn.publish(factory, 1, reservation["token"])

            notes = factory / "NOTES-r01.md"
            notes.write_text("coverage omitted\n")
            marker = factory / "ROUND-r01.complete.json"
            payload = json.loads(marker.read_text())
            notes_entry = next(
                entry for entry in payload["files"] if entry["name"] == notes.name
            )
            notes_entry["sha256"] = round_txn.file_sha256(notes)
            marker.write_text(json.dumps(payload) + "\n")

            with self.assertRaisesRegex(round_txn.TransactionError, "Novel coverage"):
                round_txn.frontier_status(factory)

    def test_step_free_safety_case_requires_textual_goal_and_outcome(self):
        rec = safety_case()
        rec.pop("steps")
        rec["goal"] = None
        rec["outcome"] = []

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("goal must be a non-empty string" in error for error in errs), errs)
        self.assertTrue(any("outcome must be a non-empty string" in error for error in errs), errs)

if __name__ == "__main__":
    unittest.main()
