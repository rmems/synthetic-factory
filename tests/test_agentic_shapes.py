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
            "steps": [_step(1, "Plan: write temp then rename")],
            "outcome": "rename is atomic",
            "reward": {"success": True},
        },
        "rejected": {
            "steps": [_step(1, "Plan: write destination in place")],
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
            {"n": 3, "speaker": "implementer", "content": "Adding a TTL test, then ship."},
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "add failing test then patch",
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
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 2)

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
