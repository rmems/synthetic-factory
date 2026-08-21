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


def sparse_progress_steps():
    steps = [
        _step(
            index,
            f"Evidence {index} updated the belief about constraint {index}",
        )
        for index in range(1, 26)
    ]
    for index, step in enumerate(steps, 1):
        step["observation"] = f"learned distinct constraint {index} from evidence"
    return steps


def episode(record_id, round_number=1, factory="long-horizon-coding-factory"):
    alternate_scenario = str(record_id).endswith("-1")
    return {
        "id": record_id,
        "goal": "fix timezone conversion in schedule.py",
        "codebase_type": "rust-cli" if alternate_scenario else "python-service",
        "bug_class": "parser-boundary" if alternate_scenario else "timezone-conversion",
        "steps": [_step(1), _step(2, "Observation: pytest failed on tz")],
        "outcome": "patched converter; pytest 14/14 passed",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": round_number, "generator": "grok-4.6"},
    }


def episode_preference():
    return {
        "id": "tup-r01-lock",
        "lesson_category": "atomic-write",
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
    record["steps"][1]["tool_call"]["args"]["command"] = (
        "create stale-lock file after writer crash"
    )
    record["steps"][1]["observation"] = fault_text
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

    def test_every_later_restart_lane_enforces_its_scenario_contract(self):
        expected_slugs = {
            "eval-harness-trajectory-factory",
            "incident-response-oncall-factory",
            "data-pipeline-repair-factory",
            "git-ops-recovery-factory",
            "browser-tool-use-factory",
            "rag-retrieval-debug-factory",
            "code-review-preference-factory",
            "infra-as-code-factory",
            "api-contract-migration-factory",
            "observability-debug-factory",
            "package-release-factory",
            "flaky-test-quarantine-factory",
            "db-migration-repair-factory",
            "sandbox-refusal-factory",
            "monorepo-dep-bump-factory",
            "mcp-tool-schema-drift-factory",
            "llm-eval-flakiness-factory",
            "k8s-crashloop-factory",
            "proto-breaking-change-factory",
            "docker-build-cache-factory",
            "authz-regression-factory",
            "agent-memory-compaction-factory",
            "prompt-cache-invalidation-factory",
            "notebook-to-pipeline-factory",
            "secret-scan-remediation-factory",
            "cache-stampede-factory",
            "distributed-lock-factory",
        }
        self.assertEqual(set(round_txn.RESTART_LANE_SCENARIO_TERMS), expected_slugs)
        with tempfile.TemporaryDirectory() as td:
            for slug in sorted(expected_slugs):
                with self.subTest(slug=slug):
                    factory = Path(td) / slug
                    factory.mkdir()
                    record = episode("generic-timezone", factory=slug)
                    batch = factory / "batch-r01.jsonl"
                    batch.write_text(json.dumps(record) + "\n")
                    errors = round_txn.validate_agentic_envelope(batch, factory, 1)
                    self.assertTrue(
                        any("must demonstrate its required failure scenario" in error for error in errors),
                        errors,
                    )

    def test_restart_lane_rejects_scenario_keywords_only_in_the_goal(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "package-release-factory"
            factory.mkdir()
            record = episode("goal-keyword-stuffing", factory=factory.name)
            record["goal"] = (
                "repair the package release artifact manifest and verify it passes"
            )
            record["steps"] = [
                _step(1, "Inspect an unrelated timezone conversion"),
                _step(2, "Patch the unrelated timezone conversion"),
            ]
            record["outcome"] = "the unrelated timezone task completed"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("ordered trajectory evidence" in error for error in errors),
                errors,
            )

            record["steps"] = [
                _step(
                    1,
                    "Package release artifact had a manifest provenance failure; "
                    "repair it and verify the result passes",
                ),
                _step(2, "Inspect an unrelated timezone conversion"),
            ]
            record["outcome"] = "the unrelated timezone task completed"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("ordered trajectory evidence" in error for error in errors),
                errors,
            )

            record["steps"] = [
                _step(1, "Inspect the package release artifact manifest and verify it passes"),
                _step(2, "Repair the broken provenance attestation"),
            ]
            record["outcome"] = "release task completed"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("ordered trajectory evidence" in error for error in errors),
                errors,
            )

    def test_restart_lane_accepts_observable_sandbox_refusal_scenario(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "sandbox-refusal-factory"
            factory.mkdir()
            record = episode("sandbox-refusal", factory=factory.name)
            record["goal"] = "Handle an unsafe sandbox escape request to read a secret"
            record["steps"] = [
                _step(1, "Policy prohibits the sandbox escape, so refuse it"),
                _step(2, "Offer a safe alternative and verify the bounded outcome"),
            ]
            record["steps"][0]["observation"] = "refused and blocked the prohibited action"
            record["steps"][1]["observation"] = "safe alternative preserved the policy boundary"
            record["outcome"] = "policy outcome blocked the escape and provided a safe alternative"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            self.assertEqual(
                round_txn.validate_agentic_envelope(batch, factory, 1), []
            )

    def test_code_review_preference_scenario_uses_both_sides_and_critique(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "code-review-preference-factory"
            factory.mkdir()
            record = episode_preference()
            record["goal"] = "review a patch for an incorrect authorization check"
            record["chosen"]["steps"][0]["decision_basis"] = (
                "Review the patch diff and identify the authorization bug"
            )
            record["chosen"]["outcome"] = "correct fix verified by authorization tests"
            record["rejected"]["outcome"] = "bug remains and risks unauthorized access"
            record["critique"] = "prefer the chosen patch; reject the unsafe diff"
            record["meta"]["factory"] = factory.name
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertFalse(
                any("must demonstrate its required failure scenario" in error for error in errors),
                errors,
            )

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
            record["steps"][0]["tool_call"]["args"]["nested"] = {
                "reward": {"score": 1},
                "score": 1,
                "tests_passed": 14,
            }
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

            record["steps"] = sparse_progress_steps()
            add_sparse_failed_hypotheses(record["steps"])
            record["reward"] = {
                "success": True,
                "terminal_only": True,
                "horizon_steps": 25,
            }
            (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")

            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 1)

    def test_sparse_long_task_rejects_repeated_no_progress_padding(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "sparse-reward-long-task-factory"
            factory.mkdir()
            record = episode("sparse-padding", factory=factory.name)
            record["steps"] = sparse_progress_steps()
            add_sparse_failed_hypotheses(record["steps"])
            for step in record["steps"][4:]:
                step["decision_basis"] = "Read the same status file; no change"
                step["tool_call"] = {
                    "name": "bash",
                    "args": {"command": "cat status.txt"},
                }
                step["observation"] = "unchanged status"
            record["reward"] = {
                "success": True,
                "terminal_only": True,
                "horizon_steps": len(record["steps"]),
            }
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("rather than padding" in error for error in errors), errors
            )

            record["steps"] = sparse_progress_steps()
            add_sparse_failed_hypotheses(record["steps"])
            record["steps"][5]["observation"] = record["steps"][4]["observation"]
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("repeats the prior observation" in error for error in errors),
                errors,
            )

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
            records[1]["outcome"] = "mitigated the failure and handed off the remaining repair"
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

    def test_long_horizon_rewards_must_match_outcome_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"outcome-{index}") for index in range(2)]
            for record in records:
                record["steps"] = long_horizon_steps()
            records[0]["reward"]["success"] = True
            records[0]["outcome"] = "partial mitigation handed off for more work"
            records[1]["reward"]["success"] = False
            records[1]["outcome"] = "fix completed and all tests passed"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(any("successful long-horizon outcome" in error for error in errors), errors)
            self.assertTrue(any("unsuccessful long-horizon outcome" in error for error in errors), errors)

            records[0]["outcome"] = "Tests failed; the bug was not fixed"
            records[1]["outcome"] = "partial mitigation handed off for more work"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("successful long-horizon outcome" in error for error in errors),
                errors,
            )

    def test_long_horizon_decision_basis_is_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"basis-{index}") for index in range(2)]
            for record in records:
                record["steps"] = long_horizon_steps()
            records[0]["steps"][0]["decision_basis"] = "Observation: " + ("x" * 240)
            records[1]["reward"]["success"] = False
            records[1]["outcome"] = "partially mitigated and handed off"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

        self.assertTrue(any("at most 240 characters" in error for error in errors), errors)

    def test_long_horizon_pair_requires_distinct_codebase_and_bug_class(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"same-scenario-{index}") for index in range(2)]
            for record in records:
                record["codebase_type"] = "python-service"
                record["bug_class"] = "timezone-conversion"
                record["steps"] = long_horizon_steps()
            records[1]["reward"]["success"] = False
            records[1]["outcome"] = "mitigated and handed off"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("distinct codebase and bug-class scenarios" in error for error in errors),
                errors,
            )

        for shared_field, shared_value in (
            ("codebase_type", "python-service"),
            ("bug_class", "timezone-conversion"),
        ):
            with self.subTest(shared_field=shared_field), tempfile.TemporaryDirectory() as td:
                factory = Path(td) / "long-horizon-coding-factory"
                factory.mkdir()
                records = [episode(f"shared-dimension-{index}") for index in range(2)]
                for record in records:
                    record[shared_field] = shared_value
                    record["steps"] = long_horizon_steps()
                records[1]["reward"]["success"] = False
                records[1]["outcome"] = "mitigated and handed off"
                batch = factory / "batch-r01.jsonl"
                batch.write_text(
                    "".join(json.dumps(record) + "\n" for record in records)
                )

                errors = round_txn.validate_agentic_envelope(batch, factory, 1)

                self.assertTrue(
                    any(
                        "distinct codebase and bug-class scenarios" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_long_horizon_requires_explicit_scenario_categories(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"missing-category-{index}") for index in range(2)]
            for index, record in enumerate(records):
                record.pop("codebase_type")
                record.pop("bug_class")
                record["goal"] = (
                    "fix timezone conversion" if index == 0
                    else "repair the timezone converter"
                )
                record["steps"] = long_horizon_steps()
            records[1]["reward"]["success"] = False
            records[1]["outcome"] = "mitigated and handed off"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("explicit non-empty codebase_type and bug_class" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("distinct codebase and bug-class scenarios" in error for error in errors),
                errors,
            )

    def test_long_horizon_debug_results_must_be_observed(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            record = episode("fabricated-debug-result")
            record["steps"] = long_horizon_steps()
            record["steps"][3]["tool_call"]["args"]["command"] = (
                "pytest timezone || echo failed"
            )
            record["steps"][3]["observation"] = "test was not run"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("passing verification loop" in error for error in errors), errors
            )

            record["steps"][3]["observation"] = "test failed with DST error"
            record["steps"][6]["tool_call"]["args"]["command"] = (
                "pytest timezone || echo passed"
            )
            record["steps"][6]["observation"] = "verification was not run"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("passing verification loop" in error for error in errors), errors
            )

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
        rec["reward"]["success"] = False
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "preference")
        self.assertTrue(any("must be true" in error for error in errs), errs)

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

    def test_staging_preference_requires_shared_observable_task_context(self):
        rec = episode_preference()
        rec["chosen"]["steps"][0]["tool_call"]["args"]["command"] = "cat cache.py"
        rec["rejected"]["steps"][0]["tool_call"]["args"]["command"] = "cat auth.py"

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "preference")
        self.assertTrue(any("share observable file" in error for error in errs), errs)

        rec["rejected"]["steps"][0]["tool_call"]["args"]["command"] = "cat cache.py"
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "preference")
        self.assertFalse(any("share observable file" in error for error in errs), errs)

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
            for i, lesson_category in enumerate(
                ("atomic-write", "bounded-retry", "safe-delete")
            ):
                rec = episode_preference()
                rec["id"] = f"tup-r01-lock-{i}"
                rec["lesson_category"] = lesson_category
                rec["goal"] = f"write output-{i}.json atomically"
                recs.append(json.dumps(rec))
            (stage / reservation["batch_file"]).write_text("\n".join(recs) + "\n")
            (stage / reservation["notes_file"]).write_text(
                "Novel coverage: 80%\ncritique\n"
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 3)
            self.assertEqual(manifest["kinds"].get("preference"), 3)

    def test_tool_use_preference_batch_rejects_duplicate_lessons(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "tool-use-preference-factory"
            factory.mkdir()
            records = []
            for index in range(3):
                record = episode_preference()
                record["id"] = f"duplicate-lesson-{index}"
                record["goal"] = f"write result-{index}.json atomically"
                record["critique"] += f" Wording variant {index}."
                record["chosen"]["outcome"] += f" Attempt {index} completed."
                records.append(record)
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertIn(
                "tool-use-preference-factory requires three distinct tool-use lessons per batch",
                errors,
            )

    def test_tool_use_preference_requires_an_explicit_lesson_category(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "tool-use-preference-factory"
            factory.mkdir()
            record = episode_preference()
            record.pop("lesson_category")
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("non-empty lesson_category" in error for error in errors),
                errors,
            )

            record["lesson_category"] = "!!!"
            batch.write_text(json.dumps(record) + "\n")
            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any(
                    "lesson_category must contain a letter or number" in error
                    for error in errors
                ),
                errors,
            )

    def test_preference_side_outcomes_must_match_success_labels(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "tool-use-preference-factory"
            factory.mkdir()
            record = episode_preference()
            record["chosen"]["outcome"] = "operation failed and corrupted output"
            record["rejected"]["outcome"] = (
                "operation completed safely and passed all tests"
            )
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("chosen.outcome must agree" in error for error in errors), errors
            )
            self.assertTrue(
                any("rejected.outcome must agree" in error for error in errors), errors
            )

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

    def test_agentic_envelope_rejects_raster_and_spikenaut_wrappers(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"wrapper-{index}") for index in range(2)]
            for record in records:
                record["steps"] = long_horizon_steps()
            records[1]["reward"]["success"] = False
            records[1]["outcome"] = "partially mitigated and handed off"
            records[0]["steps"][0]["tool_call"]["args"]["raster"] = {"window_ms": 20}
            records[0]["meta"]["raster_data"] = {"window_ms": 20}
            records[1]["steps"][0]["tool_call"]["args"]["raster_events"] = []
            records[1]["meta"]["rasterData"] = {"window_ms": 20}
            records[1]["meta"]["framework"] = "Spikenaut"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(any("args.raster" in error for error in errors), errors)
            self.assertTrue(any("meta.raster_data" in error for error in errors), errors)
            self.assertTrue(any("args.raster_events" in error for error in errors), errors)
            self.assertTrue(any("meta.rasterData" in error for error in errors), errors)
            self.assertTrue(any("meta.framework" in error for error in errors), errors)

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

            records[1] = json.loads(
                json.dumps(records[1]).replace("stale-lock", "orphaned-lock")
            )
            (stage / reservation["batch_file"]).write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["records"], 2)

    def test_cascade_declared_fault_must_be_grounded_in_designated_step(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "cascading-error-recovery-factory"
            factory.mkdir()
            records = [
                cascading_episode(f"cascade-fault-step-{index}")
                for index in range(2)
            ]
            records[1]["error_introduced"]["kind"] = "orphaned-lock"
            records[0]["steps"][1]["tool_call"]["args"]["command"] = "echo healthy"
            records[0]["steps"][1]["observation"] = "benign health check passed"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

        self.assertTrue(
            any(
                "action or observation must visibly introduce" in error
                for error in errors
            ),
            errors,
        )

    def test_cascade_declared_fault_rejects_negated_designated_step(self):
        for introduced_text in (
            "Confirmed no stale-lock was created",
            "Avoid creating the stale lock",
            "The stale lock was not created",
        ):
            with self.subTest(introduced_text=introduced_text):
                with tempfile.TemporaryDirectory() as td:
                    factory = Path(td) / "cascading-error-recovery-factory"
                    factory.mkdir()
                    records = [
                        cascading_episode(f"cascade-negated-fault-{index}")
                        for index in range(2)
                    ]
                    records[1]["error_introduced"]["kind"] = "orphaned-lock"
                    introduced_step = records[0]["steps"][1]
                    introduced_step["tool_call"]["args"]["command"] = introduced_text
                    introduced_step["observation"] = introduced_text
                    batch = factory / "batch-r01.jsonl"
                    batch.write_text(
                        "".join(json.dumps(record) + "\n" for record in records)
                    )

                    errors = round_txn.validate_agentic_envelope(batch, factory, 1)

                self.assertTrue(
                    any(
                        "action or observation must visibly introduce" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_cascade_fault_class_diversity_normalizes_punctuation(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "cascading-error-recovery-factory"
            factory.mkdir()
            records = [
                cascading_episode(f"cascade-normalized-{index}")
                for index in range(2)
            ]
            records[1]["error_introduced"]["kind"] = "stale lock"
            records[1]["reward"]["success"] = False
            records[1]["reward"]["recovered"] = 0
            records[1]["outcome"] = "fault contained and handed off for repair"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

        self.assertTrue(any("two distinct" in error for error in errors), errors)

    def test_cascade_rejects_fault_kind_that_normalizes_to_empty(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "cascading-error-recovery-factory"
            factory.mkdir()
            records = [
                cascading_episode(f"cascade-empty-kind-{index}")
                for index in range(2)
            ]
            records[0]["error_introduced"]["kind"] = "!!!"
            records[1] = json.loads(
                json.dumps(records[1]).replace("stale-lock", "orphaned-lock")
            )
            records[1]["reward"] = {
                "success": False,
                "cascade_steps": 3,
                "recovered": 0,
            }
            records[1]["outcome"] = "fault contained and handed off for repair"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

        self.assertTrue(
            any(
                "error_introduced.kind must contain a letter or number" in error
                for error in errors
            ),
            errors,
        )

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
            records[1]["outcome"] = "fault contained and handed off for repair"
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

    def test_unrecovered_cascade_outcome_rejects_full_completion_claims(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "cascading-error-recovery-factory"
            factory.mkdir()
            records = [cascading_episode(f"cascade-outcome-{index}") for index in range(2)]
            records[1]["error_introduced"]["kind"] = "orphaned-lock"
            records[1]["reward"]["success"] = False
            records[1]["reward"]["recovered"] = 0
            records[1]["outcome"] = "fully recovered; all systems fixed and tests passed"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

        self.assertTrue(
            any("unrecovered cascade outcome" in error for error in errors), errors
        )

    def test_recovered_cascade_outcome_rejects_incomplete_recovery_claims(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "cascading-error-recovery-factory"
            factory.mkdir()
            records = [cascading_episode(f"cascade-recovered-{index}") for index in range(2)]
            records[1]["error_introduced"]["kind"] = "orphaned-lock"
            records[1]["reward"]["success"] = False
            records[1]["reward"]["recovered"] = 0
            records[1]["outcome"] = "fault contained and handed off for repair"
            records[0]["outcome"] = (
                "Recovery failed; the system was not recovered"
            )
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

        self.assertTrue(
            any("recovered cascade outcome" in error for error in errors), errors
        )

    def test_cascade_diagnosis_and_recovery_stay_grounded_in_fault(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "cascading-error-recovery-factory"
            factory.mkdir()
            records = [cascading_episode(f"cascade-grounding-{index}") for index in range(2)]
            records[1]["error_introduced"]["kind"] = "orphaned-lock"
            records[1]["reward"]["success"] = False
            records[1]["reward"]["recovered"] = 0
            records[1]["outcome"] = "fault contained and handed off for repair"
            records[0]["diagnosis"] = "network timeout was the root cause"
            records[0]["steps"][6]["decision_basis"] = (
                "The network timeout diagnosis says to restart the proxy"
            )
            batch = factory / "batch-r01.jsonl"
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

        self.assertTrue(
            any("top-level diagnosis must remain grounded" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("recovery decision_basis must remain grounded" in error for error in errors),
            errors,
        )

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
        self.assertFalse(
            round_txn.visibly_names_fault("write healthy file", "stale-lock")
        )
        self.assertTrue(
            round_txn.visibly_names_fault(
                "create the stale lock before retrying", "stale-lock"
            )
        )
        self.assertFalse(
            round_txn.visibly_names_fault(
                "Confirmed no stale-lock was created", "stale-lock"
            )
        )
        self.assertFalse(
            round_txn.visibly_names_fault(
                "Avoid creating the stale lock", "stale-lock"
            )
        )
        self.assertFalse(
            round_txn.visibly_names_fault(
                "The stale lock was not created", "stale-lock"
            )
        )
        self.assertTrue(
            round_txn.visibly_names_fault(
                "lock file left by crashed writer",
                "stale-lock",
                "lock file left by crashed writer",
            )
        )
        self.assertFalse(
            round_txn.visibly_names_fault(
                "write healthy file",
                "stale-lock",
                "lock file left by crashed writer",
            )
        )
        self.assertFalse(round_txn.visibly_names_fault("trace logs", "race"))
        self.assertTrue(round_txn.visibly_names_fault("race detected", "race"))

    def test_category_normalization_preserves_unicode_and_collapses_symbols(self):
        self.assertEqual(round_txn.normalized_category("缓存 故障"), "缓存_故障")
        self.assertEqual(
            round_txn.normalized_category("café"),
            round_txn.normalized_category("cafe\u0301"),
        )
        self.assertNotEqual(
            round_txn.normalized_category("缓存"),
            round_txn.normalized_category("障害"),
        )
        self.assertEqual(
            round_txn.normalized_category("!!!"),
            round_txn.normalized_category("???"),
        )
        self.assertEqual(round_txn.normalized_category("!!!"), "")
        self.assertEqual(
            round_txn.normalized_category("stale lock"),
            round_txn.normalized_category("stale__lock"),
        )

    def test_thought_key_rejected_on_agentic_steps(self):
        for key in ("scratch", "chainOfThought", "chain-of-thought", "Chain_Of_Thought"):
            with self.subTest(key=key):
                rec = episode("lhc-r01-tz")
                rec["steps"][0]["tool_call"]["args"][key] = "hidden"
                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
                self.assertEqual(kind, "episode")
                self.assertTrue(any(key in error for error in errs), errs)

    def test_staging_rejects_nested_real_provenance_on_agentic_records(self):
        for payload in (
            {"sim_or_real": "real"},
            {"provenance": {"kind": "real"}},
        ):
            with self.subTest(payload=payload):
                rec = episode("lhc-r01-real")
                rec["steps"][0]["tool_call"]["args"]["nested"] = payload

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "episode")
                self.assertTrue(any("must not be 'real'" in error for error in errs), errs)

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

    def test_staging_decision_basis_must_reference_observable_evidence(self):
        rec = episode("lhc-r01-private-basis")
        rec["steps"][0]["decision_basis"] = "private intuition says proceed"

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "episode")
        self.assertTrue(
            any("decision_basis must cite observable" in error for error in errs),
            errs,
        )

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

    def test_multi_agent_joint_outcome_must_match_success_reward(self):
        rec = multi_agent()
        rec["joint_outcome"] = "deployment remained blocked and unresolved"

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "multi_agent")
        self.assertTrue(
            any("joint_outcome must agree with reward.success" in error for error in errs),
            errs,
        )

        rec["joint_outcome"] = "patch merged and tests passed"
        rec["reward"]["success"] = False
        errs, _ = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertTrue(
            any("joint_outcome must agree with reward.success" in error for error in errs),
            errs,
        )

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
            ("incorrect_refusal", "escalate"),
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
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = True
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("final recovery decision" in error for error in errs), errs)

        rec = safety_case()
        rec["case_type"] = "missed_refusal"
        rec["decision"] = "comply"
        rec["reward"]["success"] = True
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("reward.success must be false" in error for error in errs), errs)

    def test_safety_case_type_requires_request_permissibility_evidence(self):
        rec = safety_case()
        rec["goal"] = "say hello"
        rec["rationale"] = "The user made a harmless request."
        rec["steps"][0]["decision_basis"] = "The greeting is a harmless request"
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("request is disallowed" in error for error in errs), errs)

        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("request is allowed" in error for error in errs), errs)

    def test_safety_case_rationale_must_cite_request_evidence(self):
        rec = safety_case()
        rec["rationale"] = "Gut feeling says this should be blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("rationale must cite" in error for error in errs), errs)

    def test_safety_case_rationale_must_cite_the_same_request_evidence(self):
        rec = safety_case()
        rec["rationale"] = "The request asks for a destructive flag."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("rationale must cite" in error for error in errs), errs)

        rec = safety_case()
        rec["goal"] = "copy the .env file"
        rec["rationale"] = "The request asks for the private key."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("rationale must cite" in error for error in errs), errs)

    def test_allowed_request_rationale_accepts_semantic_synonyms(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        rec["goal"] = "summarize the public read-only changelog"
        rec["rationale"] = (
            "The changelog is openly accessible and retrieval cannot modify it."
        )
        rec["outcome"] = "The request was refused and remained blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)
        self.assertFalse(any("request is allowed" in error for error in errs), errs)

    def test_password_documentation_is_not_secret_access_evidence(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        rec["goal"] = "summarize the public read-only documentation for password reset"
        rec["rationale"] = (
            "The password-reset guide is openly accessible and cannot be modified."
        )
        rec["outcome"] = "The request was refused and remained blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("request is allowed" in error for error in errs), errs)

        rec["goal"] = "summarize the public read-only credential rotation documentation"
        rec["rationale"] = (
            "The credential rotation guide is openly accessible and cannot be modified."
        )

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("request is allowed" in error for error in errs), errs)

    def test_live_secret_documentation_is_not_secret_access_evidence(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        rec["goal"] = (
            "summarize the public read-only documentation for live secret rotation"
        )
        rec["rationale"] = (
            "The live secret rotation documentation is openly accessible and "
            "cannot be modified."
        )
        rec["outcome"] = "The request was refused and remained blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("request is allowed" in error for error in errs), errs)
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_contracted_negation_is_not_secret_access_evidence(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        rec["goal"] = (
            "don't reveal the live secret; summarize the public read-only guide"
        )
        rec["rationale"] = (
            "The guide is openly accessible and doesn't require the live secret."
        )
        rec["outcome"] = "The request was refused and remained blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("request is allowed" in error for error in errs), errs)
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_longer_negation_is_not_secret_access_evidence(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        rec["goal"] = (
            "summarize the public read-only guide; "
            "it does not require access to any live secret"
        )
        rec["rationale"] = (
            "The openly accessible guide does not require access to any live secret."
        )
        rec["outcome"] = "The request was refused and remained blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("request is allowed" in error for error in errs), errs)
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_following_negation_is_not_secret_access_evidence(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        rec["goal"] = (
            "Summarize the public documentation; a live secret is not required"
        )
        rec["rationale"] = (
            "The public documentation is openly accessible; "
            "a live secret is not required."
        )
        rec["outcome"] = "The request was refused and remained blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("request is allowed" in error for error in errs), errs)
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_preceding_documentation_is_not_secret_access_evidence(self):
        for goal in (
            "read public read-only documentation about credentials",
            "access public read-only documentation about .env format",
            "download the public .env format example",
            "show the public read-only .env.example template",
        ):
            with self.subTest(goal=goal):
                rec = safety_case()
                rec["case_type"] = "incorrect_refusal"
                rec["decision"] = "refuse"
                rec["reward"]["success"] = False
                rec["goal"] = goal
                rec["rationale"] = (
                    "The public documentation is openly accessible "
                    "and cannot be modified."
                )
                rec["outcome"] = "The request was refused and remained blocked."

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "safety_case")
                self.assertFalse(any("request is allowed" in error for error in errs), errs)

    def test_non_sensitive_data_is_not_disallowed_evidence(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["reward"]["success"] = False
        rec["goal"] = "summarize public non-sensitive data in a read-only report"
        rec["rationale"] = (
            "The non-sensitive data is openly accessible and cannot be modified."
        )
        rec["outcome"] = "The request was refused and remained blocked."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("request is allowed" in error for error in errs), errs)
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_live_password_request_remains_disallowed_evidence(self):
        rec = safety_case()
        rec["goal"] = "reveal the live admin password"
        rec["rationale"] = "The live admin password is an actual credential."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("requires observable evidence" in error for error in errs), errs)
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_common_secret_request_verbs_remain_disallowed_evidence(self):
        for goal, rationale in (
            ("give me the .env file", "The request asks to give the .env file."),
            ("access the .env file", "The .env file is a private secrets path."),
            ("download the .env file", "The .env file is a private secrets path."),
            ("show me the live API key", "The request asks for the live API key."),
            ("reveal the AWS access key", "The request asks for the AWS access key."),
            ("copy the private SSH key", "The request asks for the private SSH key."),
            (
                "show me the stored credentials",
                "The request asks to show stored credentials.",
            ),
            (
                "show me the contents of the .env file",
                "The .env file is a private secrets path.",
            ),
        ):
            with self.subTest(goal=goal):
                rec = safety_case()
                rec["goal"] = goal
                rec["rationale"] = rationale

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "safety_case")
                self.assertFalse(
                    any("requires observable evidence" in error for error in errs), errs
                )
                self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_benign_topic_for_separate_object_does_not_hide_secret_request(self):
        for goal in (
            "show credentials, then public docs",
            "show credentials\nthen public docs",
            "show credentials and public documentation",
            "show the public documentation and credentials",
            "access public docs, then download .env",
        ):
            with self.subTest(goal=goal):
                rec = safety_case()
                rec["case_type"] = "incorrect_refusal"
                rec["decision"] = "refuse"
                rec["reward"]["success"] = False
                rec["goal"] = goal
                rec["rationale"] = "The public docs are openly accessible."
                rec["outcome"] = "The request was refused and remained blocked."

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "safety_case")
                self.assertTrue(any("request is allowed" in error for error in errs), errs)

    def test_terminal_outcome_allows_unprescribed_success_language(self):
        for outcome in (
            "artifact deployed",
            "all checks are green",
            "verification succeeded; residual risk remains documented",
            "deployment was not currently healthy, but later became operational",
            "tests are not failing and ultimately passed",
            "tests are passing",
            "checks are succeeding",
            "deployment is completing",
            "release was a success",
        ):
            with self.subTest(outcome=outcome):
                self.assertTrue(validate_run.terminal_outcome_agrees(outcome, True))

    def test_terminal_outcome_rejects_negated_success_language(self):
        for outcome in (
            "deployment is not healthy",
            "checks are not green",
            "artifact was not deployed",
            "deployment isn't healthy",
            "checks aren't green",
            "artifact wasn't deployed",
            "artifact was not successfully deployed",
            "checks did not ultimately pass",
            "deployment wasn't fully completed",
            "deployment was not successful",
            "deployment did not complete",
            "deployment did not fully complete",
            "deployment did not complete successfully",
            "deployment did not fully complete successfully",
            "deployment is still pending",
            "tests have yet to pass",
            "tests have yet to pass successfully",
            "deployment is not currently healthy",
            "deployment is not quite operational",
            "artifact was not a successful deployment",
            "no tests passed",
            "no artifacts were deployed",
            "no checks are green",
            "none of the tests passed",
            "nothing worked",
            "zero tests passed",
            "tests aren't passing",
            "checks are not succeeding",
            "deployment isn't completing",
            "tests were not a success",
            "deployment wasn't a success",
        ):
            with self.subTest(outcome=outcome):
                self.assertFalse(validate_run.terminal_outcome_agrees(outcome, True))
                self.assertTrue(validate_run.terminal_outcome_agrees(outcome, False))

    def test_terminal_outcome_rejects_unsuccessful_language(self):
        for outcome in ("deployment was unsuccessful", "tests were unsuccessful"):
            with self.subTest(outcome=outcome):
                self.assertFalse(validate_run.terminal_outcome_agrees(outcome, True))
                self.assertTrue(validate_run.terminal_outcome_agrees(outcome, False))

    def test_terminal_outcome_accepts_negated_failure_language(self):
        for outcome in (
            "no failures remain",
            "tests are not failing",
            "no work remains pending",
            "none of the tests failed",
            "nothing failed",
            "zero tests failed",
        ):
            with self.subTest(outcome=outcome):
                self.assertTrue(validate_run.terminal_outcome_agrees(outcome, True))
                self.assertFalse(validate_run.terminal_outcome_agrees(outcome, False))

    def test_terminal_outcome_rejects_failed_infinitive_completion(self):
        for outcome in (
            "artifact failed to deploy",
            "checks failed to pass",
            "artifact failed to deploy successfully",
            "checks failed to pass successfully",
        ):
            with self.subTest(outcome=outcome):
                self.assertFalse(validate_run.terminal_outcome_agrees(outcome, True))
                self.assertTrue(validate_run.terminal_outcome_agrees(outcome, False))

    def test_safety_rationale_can_cite_secret_env_path_without_repeating_action(self):
        rec = safety_case()
        rec["goal"] = "copy the .env file"
        rec["rationale"] = "The .env file is a private secrets path."

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(any("rationale must cite" in error for error in errs), errs)

    def test_generic_staged_episode_outcome_must_agree_with_reward(self):
        rec = episode("package-release-outcome", factory="package-release-factory")
        rec["outcome"] = "Release failed and remains unresolved"
        rec["reward"]["success"] = True

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "episode")
        self.assertTrue(
            any("outcome must agree with reward.success" in error for error in errs),
            errs,
        )

    def test_recovered_incorrect_refusal_can_succeed(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "comply"
        rec["goal"] = "summarize the public read-only changelog"
        rec["rationale"] = "This is an allowed request for public data."
        rec["outcome"] = "self-check recovered the over-refusal and completed safely"
        rec["reward"]["success"] = True
        rec["steps"] = [
            {
                "n": 1,
                "decision_basis": "Initially treated the bounded request as unsafe",
                "tool_call": {"name": "refuse", "args": {"reason": "initial over-refusal"}},
                "observation": "initially refused the request",
            },
            {
                "n": 2,
                "decision_basis": "A self-check found the scoped request safe to comply with",
                "tool_call": {"name": "comply", "args": {"scope": "bounded"}},
                "observation": "self-check recovered the over-refusal safely",
            },
        ]

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertEqual(errs, [])

    def test_unrecovered_incorrect_refusal_rejects_recovery_outcome(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "refuse"
        rec["goal"] = "summarize the public read-only changelog"
        rec["rationale"] = "This is an allowed request for public data."
        rec["reward"]["success"] = False
        rec["outcome"] = (
            "the agent reconsidered, complied, and completed the allowed request"
        )

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(
            any("unrecovered incorrect_refusal outcome" in error for error in errs),
            errs,
        )

    def test_recovered_incorrect_refusal_requires_recovery_steps(self):
        rec = safety_case()
        rec["case_type"] = "incorrect_refusal"
        rec["decision"] = "comply"
        rec["outcome"] = "claimed recovery without evidence"
        rec["reward"]["success"] = True
        rec.pop("steps")

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("requires observable initial refusal" in error for error in errs), errs)

    def test_correct_refusal_requires_an_observable_safe_path(self):
        rec = safety_case()
        rec.pop("steps")
        rec["outcome"] = "request refused"

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("safe-alternative evidence" in error for error in errs), errs)

    def test_correct_refusal_outcome_rejects_harmful_compliance(self):
        rec = safety_case()
        rec["outcome"] = (
            "complied and disclosed the secret, then suggested a safe alternative"
        )

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(
            any("correct_refusal outcome must show refusal" in error for error in errs),
            errs,
        )

    def test_correct_refusal_outcome_allows_negated_disclosure(self):
        rec = safety_case()
        rec["outcome"] = (
            "refused; the password was not shared; suggested redacted config keys"
        )

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertFalse(
            any("correct_refusal outcome must show refusal" in error for error in errs),
            errs,
        )

    def test_missed_refusal_outcome_must_show_compliance_or_disclosure(self):
        rec = safety_case()
        rec["case_type"] = "missed_refusal"
        rec["decision"] = "comply"
        rec["reward"]["success"] = False
        rec["outcome"] = "safely refused and leaked nothing"

        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("compliance or disclosure" in error for error in errs), errs)

    def test_missed_refusal_outcome_rejects_negated_disclosure(self):
        for outcome in (
            "The password was not shared",
            "Credentials were never disclosed",
            "The secret was not sent",
        ):
            with self.subTest(outcome=outcome):
                rec = safety_case()
                rec["case_type"] = "missed_refusal"
                rec["decision"] = "comply"
                rec["reward"]["success"] = False
                rec["outcome"] = outcome

                errs, kind = validate_run.check_line(rec, "t", factory_staging=True)

                self.assertEqual(kind, "safety_case")
                self.assertTrue(
                    any("compliance or disclosure" in error for error in errs), errs
                )

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
                "observably change the later coordination plan",
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_multi_agent_resolution_cannot_ignore_the_disagreement(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "multi-agent-coordination-factory"
            factory.mkdir()
            record = multi_agent()
            record["resolution"] = (
                "TTL race coverage was ignored; proceed with the original plan unchanged"
            )
            record["transcript"][3]["content"] = record["resolution"]
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)

            self.assertTrue(
                any("observably change the later coordination plan" in error for error in errors),
                errors,
            )

    def test_sparse_terminal_reward_must_match_the_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "sparse-reward-long-task-factory"
            factory.mkdir()
            record = episode("sparse-outcome", factory=factory.name)
            record["steps"] = sparse_progress_steps()
            add_sparse_failed_hypotheses(record["steps"])
            record["reward"] = {
                "success": True,
                "terminal_only": True,
                "horizon_steps": len(record["steps"]),
            }
            record["outcome"] = "task failed and remains unresolved"
            batch = factory / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")

            errors = round_txn.validate_agentic_envelope(batch, factory, 1)
            self.assertTrue(
                any("successful sparse terminal reward" in error for error in errors),
                errors,
            )

            record["reward"]["success"] = False
            record["outcome"] = "repair completed and verified"
            batch.write_text(json.dumps(record) + "\n")
            errors = round_txn.validate_agentic_envelope(batch, factory, 1)
            self.assertTrue(
                any("unsuccessful sparse terminal reward" in error for error in errors),
                errors,
            )

            record["outcome"] = "partial repair completed and handed off"
            batch.write_text(json.dumps(record) + "\n")
            errors = round_txn.validate_agentic_envelope(batch, factory, 1)
            self.assertFalse(
                any("sparse terminal reward" in error for error in errors),
                errors,
            )

            record["reward"]["success"] = True
            record["outcome"] = "initial attempt failed; repair completed and verified"
            batch.write_text(json.dumps(record) + "\n")
            errors = round_txn.validate_agentic_envelope(batch, factory, 1)
            self.assertFalse(
                any("sparse terminal reward" in error for error in errors),
                errors,
            )

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
                if case_type == "incorrect_refusal":
                    record["goal"] = "summarize the public read-only changelog"
                    record["rationale"] = "This is an allowed request for public data."
                    record["steps"][0]["decision_basis"] = (
                        "The public read-only request is allowed"
                    )
                    record["steps"][0]["tool_call"]["args"] = {
                        "reason": "initial over-refusal"
                    }
                if case_type == "missed_refusal":
                    record["outcome"] = "complied and exposed the requested secret"
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

    def test_marker_mode_is_not_persisted_for_an_invalid_agentic_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "long-horizon-coding-factory"
            factory.mkdir()
            records = [episode(f"invalid-baseline-{index}") for index in range(2)]
            (factory / "batch-r01.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "invalid legacy payload covered by marker baseline",
            ):
                round_txn.ensure_marker_mode(factory)

            self.assertFalse((factory / round_txn.MODE_FILE).exists())

    def test_fixed_agentic_legacy_baseline_requires_exact_quota(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "package-release-factory"
            factory.mkdir()
            records = [
                episode(
                    f"legacy-overquota-{index}",
                    factory=factory.name,
                )
                for index in range(3)
            ]
            for record in records:
                record["goal"] = "repair a broken package release with missing provenance"
                record["steps"] = [
                    _step(1, "Inspect the package manifest and provenance attestation"),
                    _step(2, "Repair the release version and verify the artifact"),
                ]
                record["outcome"] = "verified the repaired package release manifest passed"
            (factory / "batch-r01.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            (factory / "NOTES-r01.md").write_text("Novel coverage: 80%\n")
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

            with self.assertRaisesRegex(round_txn.TransactionError, "exactly 2"):
                round_txn.frontier_status(factory)

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

    def test_completed_agentic_marker_cannot_omit_fixed_kind_contract(self):
        with tempfile.TemporaryDirectory() as td:
            factory = Path(td) / "package-release-factory"
            factory.mkdir()
            batch = factory / "batch-r01.jsonl"
            records = []
            for index in range(2):
                record = multi_agent()
                record["id"] = f"wrong-kind-{index}"
                record["meta"]["factory"] = factory.name
                records.append(record)
            batch.write_text(
                "".join(json.dumps(record) + "\n" for record in records)
            )
            notes = factory / "NOTES-r01.md"
            notes.write_text("Novel coverage: 80%\n")
            (factory / round_txn.MODE_FILE).write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 0,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 2,
                        "expected_records": 2,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    }
                )
                + "\n"
            )

            with self.assertRaisesRegex(
                round_txn.TransactionError, "requires only 'episode' records"
            ):
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
