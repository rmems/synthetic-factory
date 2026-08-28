#!/usr/bin/env python3
"""Regression tests for the quality and execution gates.

Both gates run over untrusted generated JSONL, so malformed records must
produce a verdict rather than an exception, and provenance must be counted
from whichever field carries it.

``FrontierPublishGate`` covers clause 16 of docs/verify-execution.md: the
round_txn publish path runs the verifier in strict mode, an inconclusive record
blocks ``ROUND-rNN.complete.json`` so the marker-based frontier cannot advance,
and only an explicit operator waiver — recorded in the completion marker — lets
cannot-verify records through. A failed record is never waivable.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import quality_gate  # noqa: E402
import round_txn  # noqa: E402
import verify_execution  # noqa: E402


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def thalamic(record_id, observable=True, rationale="bounded fixture"):
    """A thalamic record that the strict execution gate can verify.

    ``observable=False`` drops the observable outcome evidence, which is the
    unverifiable-assertion fixture: the record still passes the shape and
    reward validators, but its claimed outcome cannot be checked.
    """
    future_outcome = {"success": True}
    if observable:
        future_outcome.update(
            {
                "timeline": [{"t_ms": 0, "event": "noop accepted"}],
                "observed_effects": ["no actuator motion"],
                "new_state": {"sim_or_real": "designed", "domain": "gate-test"},
            }
        )
    record = {
        "id": record_id,
        "state": {"sim_or_real": "designed", "domain": "gate-test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": rationale},
        "executed_action": {"action": "noop"},
        "future_outcome": future_outcome,
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {
            "factory": "thalamic-trajectory-factory",
            "round": 1,
            "tags": ["gate-test"],
        },
    }
    return record


def episode_side():
    return {
        "steps": [
            {
                "n": 1,
                "decision_basis": "read the file before editing",
                "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                "observation": "file has 3 lines",
            }
        ],
        "outcome": "edited safely",
        "reward": {"success": True},
    }


def execution_summary(
    *,
    verified=1,
    inconclusive=0,
    failed=0,
    override=None,
    gate=None,
    strict=True,
    extra=None,
):
    summary = {
        "gate": round_txn.EXECUTION_GATE_LABEL if gate is None else gate,
        "strict": strict,
        "counts": {
            "failed": failed,
            "inconclusive": inconclusive,
            "total": verified + inconclusive + failed,
            "verified": verified,
        },
        "override": override,
    }
    if extra:
        summary.update(extra)
    return summary


class QualityGate(unittest.TestCase):
    def test_record_hash_survives_malformed_preference_records(self):
        for malformed in (
            {"chosen": {"state": {"a": 1}}},           # no rejected side
            {"chosen": "not-an-object", "rejected": None},
            {"chosen": {}, "rejected": 5},
        ):
            digest = quality_gate.record_hash(malformed)
            self.assertIsInstance(digest, str)
            self.assertTrue(digest)

    def test_provenance_counts_sim_or_real_without_top_level_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "f" / "batch.jsonl", [
                {"id": "a", "state": {"sim_or_real": "designed"}},
                {"id": "b", "state": {"sim_or_real": "simulated"}},
            ])
            report = quality_gate.audit_run(root)

        mix = report["mix"] if "mix" in report else report
        self.assertEqual(mix["provenance"].get("designed"), 1)
        self.assertEqual(mix["provenance"].get("simulated"), 1)
        self.assertEqual(mix["synthetic"], 2)

    def test_provenance_falls_back_to_top_level_kind(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "f" / "batch.jsonl", [
                {"id": "a", "state": {}, "provenance": {"kind": "hil"}},
            ])
            report = quality_gate.audit_run(root)

        mix = report["mix"] if "mix" in report else report
        self.assertEqual(mix["provenance"].get("hil"), 1)


class VerifyExecution(unittest.TestCase):
    def test_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution.verify_thalamic("a string", "where")
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)

    def test_non_string_rationale_does_not_raise(self):
        status, _ = verify_execution.verify_thalamic(
            {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"rationale": {"nested": "object"}},
                "future_outcome": {},
            },
            "where",
        )
        self.assertEqual(status, "failed")

    def test_malformed_observable_fields_are_not_verified(self):
        for field, value in (
            ("timeline", "narrative"),
            ("new_state", True),
            ("state_delta", True),
            ("surprises", {"not": "an array"}),
            ("latency_ms", True),
        ):
            with self.subTest(field=field):
                record = thalamic(f"malformed-{field}")
                record["future_outcome"] = {field: value}
                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertEqual(status, "failed")
                self.assertIn(f"future_outcome.{field} must be", reason)

    def test_factory_outcome_vocabulary_is_observable_evidence(self):
        outcomes = (
            {
                "state_delta": {"position_m": [1.0, 1.2]},
                "surprises": [{"delay_ms": 50, "effect": "thermal rise"}],
                "reward_inflection_t_us": 123456,
            },
            {"latency_ms": 41.0},
            {"hazard_avoided": "sensor_blind_advance"},
            {"incident": "guard tripped downstream"},
        )
        for index, outcome in enumerate(outcomes):
            with self.subTest(outcome=outcome):
                record = thalamic(f"outcome-vocabulary-{index}")
                record["future_outcome"] = outcome
                status, _reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertEqual(status, "verified")

    def test_negative_timing_metrics_are_not_observable_evidence(self):
        for field in (
            "divergence_detected_ms",
            "latency_ms",
            "reward_inflection_t_us",
            "slip_arrested_ms",
        ):
            with self.subTest(field=field):
                record = thalamic(f"negative-{field}")
                record["future_outcome"] = {field: -1}

                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )

                self.assertEqual(status, "failed")
                self.assertIn("must be a non-negative finite number", reason)

    def test_oversized_integer_metric_returns_a_failed_verdict(self):
        record = thalamic("oversized-latency")
        record["future_outcome"] = {"latency_ms": 10**1000}

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "failed")
        self.assertIn("future_outcome.latency_ms must be a finite number", reason)

    def test_bridge_with_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution.verify_record_execution(
            {"language_view": {"trajectory": "oops"}, "spike_events": [1]},
            "where",
        )
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)

    def test_preference_side_inherits_the_pair_goal_and_is_verified_by_step(self):
        # The pair owns `goal`; each side owns its own `steps`. That side is an
        # episode, not an unrecognized shape.
        side = {
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "read the file before editing",
                    "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                    "observation": "file has 3 lines",
                }
            ],
            "outcome": "edited safely",
            "reward": {"success": True},
        }
        pair = {
            "goal": "edit a.txt safely",
            "chosen": side,
            "rejected": json.loads(json.dumps(side)),
            "critique": "the chosen edit preserves the requested invariant",
            "reward": {"success": True},
        }
        self.assertEqual(
            verify_execution.verify_record_execution(pair, "where")[0], "verified"
        )
        pair["chosen"]["steps"][0]["observation"] = ""
        status, reason = verify_execution.verify_record_execution(pair, "where")
        self.assertEqual(status, "inconclusive")
        self.assertIn("missing observation", reason)

    def test_malformed_or_mixed_preference_sides_are_not_verified(self):
        valid_side = {
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "read before editing",
                    "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                    "observation": "three lines",
                }
            ],
            "outcome": "edited safely",
            "reward": {"success": True},
        }
        missing_envelope = {"steps": valid_side["steps"]}
        status, reason = verify_execution.verify_record_execution(
            missing_envelope, "standalone"
        )
        self.assertEqual(status, "failed")
        self.assertIn("episode missing 'goal'", reason)

        pair = {
            "goal": "edit a.txt safely",
            "chosen": thalamic("mixed-thalamic"),
            "rejected": valid_side,
            "critique": "the two sides use incompatible record families",
            "reward": {"success": True},
        }
        status, reason = verify_execution.verify_record_execution(pair, "mixed")
        self.assertEqual(status, "failed")
        self.assertIn("preference wrapper invalid", reason)

    def test_preference_wrapper_uses_the_staging_envelope(self):
        side = {
            "goal": "edit a.txt safely",
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "read before editing",
                    "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                    "observation": "three lines",
                }
            ],
            "outcome": "edited safely",
            "reward": {"success": True},
        }
        valid = {
            "goal": "edit a.txt safely",
            "chosen": side,
            "rejected": json.loads(json.dumps(side)),
            "critique": "the chosen edit keeps the file valid",
            "reward": {"success": True},
        }
        self.assertEqual(
            verify_execution.verify_record_execution(valid, "where")[0],
            "verified",
        )

        cases = []
        missing_critique = json.loads(json.dumps(valid))
        missing_critique.pop("critique")
        cases.append((missing_critique, "preference record needs a non-empty critique"))
        missing_reward = json.loads(json.dumps(valid))
        missing_reward.pop("reward")
        cases.append((missing_reward, "reward must be an object"))
        conflicting_goal = json.loads(json.dumps(valid))
        conflicting_goal["rejected"]["goal"] = "delete b.txt"
        cases.append(
            (
                conflicting_goal,
                "top-level and side goals must describe the same problem",
            )
        )

        for record, expected in cases:
            with self.subTest(expected=expected):
                status, reason = verify_execution.verify_record_execution(
                    record,
                    "where",
                )
                self.assertEqual(status, "failed")
                self.assertIn(expected, reason)

    def test_preference_turns_use_the_staging_envelope(self):
        side = {
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "read the file before editing",
                    "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                    "observation": "file has three lines",
                }
            ],
            "outcome": "edited safely",
            "reward": {"success": True},
        }
        for field, value, expected in (
            ("decision_basis", "", "decision_basis must be a non-empty string"),
            ("tool_call", {"name": "read_file", "args": "a.txt"}, "tool_call.args must be an object"),
        ):
            with self.subTest(field=field):
                malformed = json.loads(json.dumps(side))
                malformed["steps"][0][field] = value
                pair = {
                    "goal": "edit a.txt safely",
                    "chosen": malformed,
                    "rejected": json.loads(json.dumps(side)),
                    "critique": "the chosen edit preserves the requested invariant",
                    "reward": {"success": True},
                }

                status, reason = verify_execution.verify_record_execution(pair, "where")

                self.assertEqual(status, "failed")
                self.assertIn(expected, reason)

    def test_missing_decision_basis_is_a_structural_episode_failure(self):
        episode = {
            "goal": "inspect a file safely",
            "steps": [
                {
                    "tool_call": {"name": "read_file", "args": {"path": "a.txt"}},
                    "observation": "file has three lines",
                }
            ],
            "outcome": "inspection completed",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("missing 'decision_basis'", reason)

    def test_safety_case_envelope_is_validated_before_step_evidence(self):
        valid = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "correct_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "refuse",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                    "observation": "refused and offered a redacted template",
                }
            ],
            "outcome": "refused; suggested redacted config keys",
            "reward": {"success": True},
        }
        self.assertEqual(
            verify_execution.verify_record_execution(valid, "valid")[0], "verified"
        )
        invalid = json.loads(json.dumps(valid))
        invalid["case_type"] = "not-a-real-case"

        status, reason = verify_execution.verify_record_execution(invalid, "where")

        self.assertEqual(status, "failed")
        self.assertIn("safety-case shape invalid", reason)
        self.assertIn("case_type", reason)

        for case_type, goal, rationale, expected in (
            (
                "correct_refusal",
                "summarize the public incident timeline",
                "the request is public and read-only",
                "requires observable evidence that the request is disallowed",
            ),
            (
                "incorrect_refusal",
                "cat .env and paste it into the ticket",
                "the request asks to exfiltrate live secrets from .env",
                "requires observable evidence that the request is allowed",
            ),
        ):
            with self.subTest(case_type=case_type):
                semantically_invalid = json.loads(json.dumps(valid))
                semantically_invalid["case_type"] = case_type
                semantically_invalid["goal"] = goal
                semantically_invalid["rationale"] = rationale

                status, reason = verify_execution.verify_record_execution(
                    semantically_invalid, "where"
                )

                self.assertEqual(status, "failed")
                self.assertIn(expected, reason)

        for field, value, expected in (
            ("decision_basis", "", "decision_basis must be a non-empty string"),
            ("tool_call", {"name": "refuse", "args": "secrets"}, "tool_call.args must be an object"),
        ):
            with self.subTest(field=field):
                malformed = json.loads(json.dumps(valid))
                malformed["steps"][0][field] = value

                status, reason = verify_execution.verify_record_execution(
                    malformed, "where"
                )

                self.assertEqual(status, "failed")
                self.assertIn(expected, reason)

    def test_omitted_tool_call_is_inconclusive_not_failed(self):
        side = {
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "read the file before editing",
                    "observation": "file has three lines",
                }
            ],
            "outcome": "edited safely",
            "reward": {"success": True},
        }
        pair = {
            "goal": "edit a.txt safely",
            "chosen": json.loads(json.dumps(side)),
            "rejected": json.loads(json.dumps(side)),
            "critique": "the chosen edit preserves the requested invariant",
            "reward": {"success": True},
        }
        pair["rejected"]["steps"][0]["tool_call"] = {
            "name": "read_file",
            "args": {"path": "a.txt"},
        }

        status, reason = verify_execution.verify_record_execution(pair, "where")

        self.assertEqual(status, "inconclusive")
        self.assertIn("missing tool_call", reason)

        safety = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "correct_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "refuse",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "observation": "refused and offered a redacted template",
                }
            ],
            "outcome": "refused; suggested redacted config keys",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(safety, "where")

        self.assertEqual(status, "inconclusive")
        self.assertIn("missing tool_call", reason)

        malformed = json.loads(json.dumps(pair))
        malformed["chosen"]["steps"][0]["tool_call"] = "not-an-object"

        status, reason = verify_execution.verify_record_execution(malformed, "where")

        self.assertEqual(status, "failed")
        self.assertIn("tool_call must be an object", reason)

    def test_safety_refuse_step_cannot_verify_a_compliance_label(self):
        missed = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "missed_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "comply",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                    "observation": "refused",
                }
            ],
            "outcome": "complied and exposed the requested secret",
            "reward": {"success": False},
        }

        status, reason = verify_execution.verify_record_execution(missed, "where")

        self.assertEqual(status, "failed")
        self.assertIn("contradicts the calibrated compliance or leakage outcome", reason)

        leaked = json.loads(json.dumps(missed))
        leaked["steps"][0]["tool_call"] = {
            "name": "bash",
            "args": {"command": "cat .env"},
        }
        leaked["steps"][0]["observation"] = "leaked the .env contents into the ticket"

        self.assertEqual(
            verify_execution.verify_record_execution(leaked, "where")[0],
            "verified",
        )

    def test_refusal_step_is_verifiable_evidence(self):
        status, _ = verify_execution.verify_episode_steps(
            [
                {
                    "n": 1,
                    "decision_basis": "the request asks for live secrets",
                    "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                    "observation": "refused",
                }
            ],
            "where",
        )
        self.assertEqual(status, "verified")

    def test_shape_error_helpers_reject_unparseable_step_indexes(self):
        self.assertIsNone(
            verify_execution._step_index_from_shape_error("other step 0: missing", "where")
        )
        self.assertIsNone(
            verify_execution._step_index_from_shape_error("where step 0", "where")
        )
        self.assertIsNone(
            verify_execution._step_index_from_shape_error(
                "where step x: tool_call must be an object", "where"
            )
        )
        self.assertFalse(
            verify_execution._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": []},
            )
        )
        self.assertFalse(
            verify_execution._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": "not-a-list"},
            )
        )

    def test_episode_and_safety_fail_closed_without_shape_checkers(self):
        status, reason = verify_execution.verify_episode("not-an-object", "where")
        self.assertEqual(status, "failed")
        self.assertIn("not an object", reason)

        with mock.patch.object(verify_execution, "check_episode", None):
            status, reason = verify_execution.verify_episode(episode_side(), "where")
        self.assertEqual(status, "failed")
        self.assertIn("episode shape checker unavailable", reason)

        with mock.patch.object(verify_execution, "check_safety_case", None):
            status, reason = verify_execution.verify_safety_episode(
                {"case_type": "correct_refusal", "steps": []}, "where"
            )
        self.assertEqual(status, "failed")
        self.assertIn("safety-case shape checker unavailable", reason)

        with mock.patch.object(verify_execution, "check_line", None):
            status, reason = verify_execution.verify_record_execution(
                {"chosen": episode_side(), "rejected": episode_side()},
                "where",
            )
        self.assertEqual(status, "failed")
        self.assertIn("preference shape checker unavailable", reason)

        status, reason = verify_execution.verify_record_execution(
            {"note": "no executable shape"}, "where"
        )
        self.assertEqual(status, "inconclusive")
        self.assertIn("unrecognized shape", reason)

    def test_refusal_helpers_reject_malformed_inputs(self):
        self.assertEqual(verify_execution._tool_call_name("Refuse now"), "refuse")
        self.assertEqual(verify_execution._tool_call_name("   "), "")
        self.assertEqual(verify_execution._tool_call_name(None), "")
        self.assertFalse(verify_execution._step_records_refusal("not-a-step"))
        self.assertFalse(
            verify_execution._calibrated_outcome_is_compliance_or_leakage("nope")
        )
        self.assertFalse(
            verify_execution._calibrated_outcome_is_compliance_or_leakage(
                {"decision": 12}
            )
        )
        self.assertIsNone(
            verify_execution._safety_refusal_contradicts_calibrated_outcome(
                {"case_type": "missed_refusal", "steps": "not-a-list"},
                "where",
            )
        )

    def test_typed_outcome_containers_reject_malformed_entries(self):
        cases = (
            ({"timeline": ["narrative"]}, "timeline entries must be objects"),
            ({"timeline": []}, "lacks observable execution evidence"),
            ({"observed_effects": "narrative"}, "observed_effects must be an array"),
            (
                {"observed_effects": [""]},
                "observed_effects entries must be non-empty",
            ),
            ({"state_delta": {}}, "lacks observable execution evidence"),
            ({"state_delta": []}, "lacks observable execution evidence"),
            (
                {"state_delta": [""]},
                "state_delta entries must be non-empty",
            ),
            ({"surprises": []}, "lacks observable execution evidence"),
            (
                {"surprises": [""]},
                "surprises entries must be non-empty",
            ),
            (
                {"hazard_avoided": ""},
                "hazard_avoided must be a non-empty string or object",
            ),
            (
                {"incident": {}},
                "incident must be a non-empty string or object",
            ),
        )
        for outcome, expected in cases:
            with self.subTest(outcome=outcome):
                record = thalamic("typed-outcome")
                record["future_outcome"] = outcome
                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertIn(expected, reason)
                self.assertIn(status, {"failed", "inconclusive"})

    def test_state_delta_list_is_observable_when_well_formed(self):
        record = thalamic("state-delta-list")
        record["future_outcome"] = {"state_delta": ["moved 1m"]}
        status, _reason = verify_execution.verify_record_execution(record, "where")
        self.assertEqual(status, "verified")

    def test_preference_sides_cover_thalamic_and_malformed_routing(self):
        thalamic_pair = {
            "goal": "keep the actuator stopped after the noop",
            "chosen": thalamic("chosen-side"),
            "rejected": thalamic("rejected-side"),
            "critique": "chosen keeps the actuator stopped after the noop",
            "reward": {"success": True},
        }
        self.assertEqual(
            verify_execution.verify_record_execution(thalamic_pair, "where")[0],
            "verified",
        )

        with mock.patch.object(
            verify_execution, "check_line", return_value=([], "unknown")
        ):
            status, reason = verify_execution.verify_record_execution(
                {"chosen": episode_side(), "rejected": episode_side()},
                "where",
            )
        self.assertEqual(status, "failed")
        self.assertIn("not classified as a preference", reason)

        with mock.patch.object(
            verify_execution, "check_line", return_value=([], "preference")
        ):
            status, reason = verify_execution.verify_record_execution(
                {"chosen": "left", "rejected": "right"},
                "where",
            )
        self.assertEqual(status, "failed")
        self.assertIn("sides must both be objects", reason)

        mixed = {
            "chosen": thalamic("mixed-chosen"),
            "rejected": episode_side(),
        }
        with mock.patch.object(
            verify_execution, "check_line", return_value=([], "preference")
        ):
            status, reason = verify_execution.verify_record_execution(mixed, "where")
        self.assertEqual(status, "failed")
        self.assertIn("mix episode and Thalamic", reason)

        omitted = {
            "chosen": thalamic("omit-chosen"),
            "rejected": {"state": {"sim_or_real": "designed"}},
        }
        with mock.patch.object(
            verify_execution, "check_line", return_value=([], "preference")
        ):
            status, reason = verify_execution.verify_record_execution(omitted, "where")
        self.assertEqual(status, "failed")
        self.assertIn("mix or omit required shape fields", reason)

        neither = {"chosen": {"note": "left"}, "rejected": {"note": "right"}}
        with mock.patch.object(
            verify_execution, "check_line", return_value=([], "preference")
        ):
            status, reason = verify_execution.verify_record_execution(neither, "where")
        self.assertEqual(status, "failed")
        self.assertIn("not episode or Thalamic", reason)

        blank_goal = {
            "goal": "   ",
            "chosen": episode_side(),
            "rejected": episode_side(),
        }
        with mock.patch.object(
            verify_execution, "check_line", return_value=([], "preference")
        ):
            status, reason = verify_execution.verify_record_execution(
                blank_goal, "where"
            )
        self.assertEqual(status, "failed")
        self.assertIn("shared goal must be a non-empty string", reason)


class ExecutionOverrideReason(unittest.TestCase):
    def test_absent_override_stays_absent(self):
        self.assertIsNone(round_txn.normalized_execution_override(None))

    def test_reason_is_whitespace_normalized(self):
        self.assertEqual(
            round_txn.normalized_execution_override(
                "  hil rig\n  offline until Monday  "
            ),
            "hil rig offline until Monday",
        )

    def test_reason_must_be_written_printable_and_bounded(self):
        for rejected in (
            "",
            "     ",
            "brief",
            "ok\x00fine because",
            "\u200b" * 8,
            "audit \u202ereason",
            b"bytes reason",
            42,
            True,
            "x" * (round_txn.EXECUTION_OVERRIDE_MAX_CHARS + 1),
        ):
            with self.subTest(rejected=rejected):
                with self.assertRaises(round_txn.TransactionError):
                    round_txn.normalized_execution_override(rejected)

    def test_recorded_override_rejects_non_canonical_markers(self):
        reason = "hil replay rig offline"
        valid_override = {"reason": reason, "waived_inconclusive": 1}
        cases = (
            {"execution_verification": "nope"},
            {"execution_verification": {"override": ["not-a-dict"]}},
            {
                "execution_verification": {
                    "override": {"reason": "  " + reason + "  ", "waived_inconclusive": 1}
                }
            },
            {
                "execution_verification": {
                    "override": {"reason": reason, "waived_inconclusive": 0}
                }
            },
            {
                "execution_verification": {
                    "override": {"reason": reason, "waived_inconclusive": True}
                }
            },
        )
        for manifest in cases:
            with self.subTest(manifest=manifest):
                with self.assertRaises(round_txn.TransactionError):
                    round_txn.recorded_execution_override(manifest)
        self.assertEqual(
            round_txn.recorded_execution_override(
                {"execution_verification": {"override": valid_override}}
            ),
            reason,
        )
        with self.assertRaises(round_txn.TransactionError):
            round_txn.comparable_execution_verification("nope")
        comparable = round_txn.comparable_execution_verification(
            {"gate": "g", "override": dict(valid_override)}
        )
        self.assertNotIn("reason", comparable["override"])
        self.assertEqual(comparable["override"]["waived_inconclusive"], 1)

    def test_verification_summary_rejects_invalid_blocks(self):
        waived = {
            "reason": "hil replay rig offline",
            "waived_inconclusive": 1,
        }
        valid = execution_summary()
        self.assertEqual(
            round_txn.validated_execution_verification_summary(valid), valid
        )
        self.assertEqual(
            round_txn.validated_execution_verification_summary(
                execution_summary(
                    verified=0, inconclusive=1, override=waived
                )
            )["override"]["reason"],
            waived["reason"],
        )
        rejected = (
            "nope",
            execution_summary(extra={"extra": True}),
            execution_summary(extra={"counts": {"verified": 1}}),
            execution_summary(verified=True),
            execution_summary(verified=-1),
            execution_summary(gate="other.gate"),
            execution_summary(strict=False),
            execution_summary(verified=0, inconclusive=0, failed=0),
            execution_summary(failed=1),
            execution_summary(verified=1, inconclusive=1, failed=0),
            execution_summary(verified=0, inconclusive=1, override=None),
            execution_summary(
                verified=0,
                inconclusive=1,
                override={"reason": "hil replay rig offline", "waived_inconclusive": 2},
            ),
            execution_summary(override=waived),
        )
        for summary in rejected:
            with self.subTest(summary=summary):
                with self.assertRaises(round_txn.TransactionError):
                    round_txn.validated_execution_verification_summary(summary)

        # verified+inconclusive != total is a counts-key mismatch on the object
        mismatched = execution_summary()
        mismatched["counts"]["total"] = 3
        with self.assertRaises(round_txn.TransactionError):
            round_txn.validated_execution_verification_summary(mismatched)

    def test_completed_verification_wraps_a_live_gate_failure(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("conflict", rationale="")])
            recorded = execution_summary(
                verified=0,
                inconclusive=1,
                override={
                    "reason": "hil replay rig offline",
                    "waived_inconclusive": 1,
                },
            )
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "conflicts with committed batch",
            ):
                round_txn.validate_completed_execution_verification(
                    batch, {"execution_verification": recorded}
                )

    def test_replace_json_atomically_rejects_unsafe_markers(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "ROUND-r01.publishing.json"
            with self.assertRaisesRegex(
                round_txn.TransactionError, "unsafe publishing marker"
            ):
                round_txn.replace_json_atomically(missing, {"ok": True})
            link = Path(td) / "ROUND-r01.link.json"
            link.symlink_to(Path(td) / "missing-target")
            with self.assertRaisesRegex(
                round_txn.TransactionError, "unsafe publishing marker"
            ):
                round_txn.replace_json_atomically(link, {"ok": True})


class FrontierPublishGate(unittest.TestCase):
    """docs/verify-execution.md clause 16 — round_txn round-trip."""

    def factory(self, root):
        path = (
            Path(root)
            / "outputs"
            / "raw"
            / "2099-01-01"
            / "thalamic-trajectory-factory"
        )
        path.mkdir(parents=True)
        return path

    def stage(self, reservation, records):
        stage = Path(reservation["staging_dir"])
        write(stage / reservation["batch_file"], records)
        (stage / reservation["notes_file"]).write_text(
            "# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n"
        )
        return stage

    def test_inconclusive_record_blocks_publish_and_the_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            stage = self.stage(reservation, [thalamic("gate-1", observable=False)])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.publish(factory, 1, reservation["token"])

            message = str(raised.exception)
            self.assertIn("cannot verify 1 of 1", message)
            self.assertIn("future_outcome lacks observable", message)
            self.assertIn("--allow-inconclusive", message)
            # No commit point, no committed artifacts, frontier unmoved, and
            # the staging area stays inspectable for the operator.
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())
            self.assertFalse((factory / "ROUND-r01.publishing.json").exists())
            self.assertFalse((factory / "batch-r01.jsonl").exists())
            self.assertFalse((factory / "NOTES-r01.md").exists())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 1)
            self.assertTrue(stage.is_dir())
            self.assertTrue((factory / "ROUND-r01.reserved.json").is_file())

    def test_verified_batch_publishes_and_records_the_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-ok")])

            manifest = round_txn.publish(factory, 1, reservation["token"])

            verdict = manifest["execution_verification"]
            self.assertTrue(verdict["strict"])
            self.assertIsNone(verdict["override"])
            self.assertEqual(verdict["counts"]["verified"], 1)
            self.assertEqual(verdict["counts"]["inconclusive"], 0)
            self.assertEqual(verdict["counts"]["failed"], 0)
            self.assertEqual(
                json.loads((factory / "ROUND-r01.complete.json").read_text())[
                    "execution_verification"
                ],
                verdict,
            )
            self.assertEqual(manifest["version"], 2)
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

    def test_version_2_completion_marker_binds_the_execution_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-bound")])
            round_txn.publish(factory, 1, reservation["token"])
            marker = factory / "ROUND-r01.complete.json"
            payload = json.loads(marker.read_text())

            deleted = dict(payload)
            deleted.pop("execution_verification")
            marker.write_text(json.dumps(deleted, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(
                round_txn.TransactionError, "version 2 completion marker"
            ):
                round_txn.frontier_status(factory)

            corrupted = json.loads(json.dumps(payload))
            corrupted["execution_verification"]["counts"]["verified"] = 0
            corrupted["execution_verification"]["counts"]["inconclusive"] = 1
            corrupted["execution_verification"]["override"] = {
                "reason": "hil replay rig offline",
                "waived_inconclusive": 1,
            }
            marker.write_text(json.dumps(corrupted, indent=2, sort_keys=True) + "\n")
            with self.assertRaisesRegex(
                round_txn.TransactionError,
                "execution verification conflicts with committed batch",
            ):
                round_txn.frontier_status(factory)

    def test_legacy_version_1_markers_without_verification_remain_visible(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            write(batch, [thalamic("legacy-v1")])
            notes.write_text("# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {
                                "name": batch.name,
                                "sha256": round_txn.file_sha256(batch),
                            },
                            {
                                "name": notes.name,
                                "sha256": round_txn.file_sha256(notes),
                            },
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
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

            status = round_txn.frontier_status(factory)

            self.assertEqual(status["next_round"], 2)
            self.assertEqual(status["completed_markers"], [1])

    def test_operator_override_records_the_waiver_before_advancing(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-waived", observable=False)])

            manifest = round_txn.publish(
                factory,
                1,
                reservation["token"],
                "hil replay rig offline; reviewed by operator",
            )

            override = manifest["execution_verification"]["override"]
            self.assertEqual(
                override["reason"], "hil replay rig offline; reviewed by operator"
            )
            self.assertEqual(override["waived_inconclusive"], 1)
            self.assertEqual(
                manifest["execution_verification"]["counts"]["inconclusive"], 1
            )
            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 0
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())
            self.assertEqual(round_txn.frontier_status(factory)["next_round"], 2)

    def test_cli_publish_accepts_the_operator_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-cli", observable=False)])

            blocked = round_txn.main(
                ["publish", str(factory), "--round", "1", "--token", reservation["token"]]
            )
            self.assertEqual(blocked, 1)
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

            allowed = round_txn.main(
                [
                    "publish",
                    str(factory),
                    "--round",
                    "1",
                    "--token",
                    reservation["token"],
                    "--allow-inconclusive",
                    "replay harness unavailable this window",
                ]
            )
            self.assertEqual(allowed, 0)
            marker = json.loads((factory / "ROUND-r01.complete.json").read_text())
            self.assertEqual(
                marker["execution_verification"]["override"]["reason"],
                "replay harness unavailable this window",
            )

    def test_failed_record_is_never_waivable(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic("gate-failed", rationale="")])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(
                    batch, batch, override="operator accepts this batch"
                )

            self.assertIn("never waivable", str(raised.exception))

    def test_gate_fails_closed_when_the_verifier_is_unimportable(self):
        with mock.patch.dict(sys.modules, {"verify_execution": None}):
            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.load_execution_verifier()
        self.assertIn("execution verification is unavailable", str(raised.exception))

    def test_publish_retry_keeps_the_first_recorded_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-retry", observable=False)])
            reason = "sensor replay pending; waived for this window"

            with mock.patch.object(
                round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
            ):
                with self.assertRaises(OSError):
                    round_txn.publish(factory, 1, reservation["token"], reason)
            self.assertTrue((factory / "ROUND-r01.publishing.json").is_file())

            manifest = round_txn.publish(
                factory, 1, reservation["token"], "reworded on retry, same batch"
            )

            self.assertEqual(
                manifest["execution_verification"]["override"]["reason"], reason
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publish_retry_reuses_the_recorded_waiver_without_a_new_flag(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-resume", observable=False)])
            reason = "sensor replay pending; waived for this window"

            with mock.patch.object(
                round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
            ):
                with self.assertRaises(OSError):
                    round_txn.publish(factory, 1, reservation["token"], reason)

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(
                manifest["execution_verification"]["override"]["reason"], reason
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())

    def test_publish_retry_migrates_a_pre_gate_publishing_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-legacy-retry")])

            with mock.patch.object(
                round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
            ):
                with self.assertRaises(OSError):
                    round_txn.publish(factory, 1, reservation["token"])

            publishing = factory / "ROUND-r01.publishing.json"
            legacy = json.loads(publishing.read_text())
            legacy.pop("execution_verification")
            publishing.write_text(json.dumps(legacy) + "\n")

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 1
            )
            self.assertIsNone(manifest["execution_verification"]["override"])
            self.assertEqual(
                json.loads((factory / "ROUND-r01.complete.json").read_text()),
                manifest,
            )

    def test_publish_retry_rejects_corrupted_execution_verification(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-corrupt-retry")])

            with mock.patch.object(
                round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
            ):
                with self.assertRaises(OSError):
                    round_txn.publish(factory, 1, reservation["token"])

            publishing = factory / "ROUND-r01.publishing.json"
            corrupted = json.loads(publishing.read_text())
            corrupted["execution_verification"]["counts"]["verified"] = 999
            publishing.write_text(json.dumps(corrupted) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "execution verification conflicts"
            ):
                round_txn.publish(factory, 1, reservation["token"])
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_gate_summarizes_when_findings_exceed_five(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            write(batch, [thalamic(f"inc-{index}", observable=False) for index in range(6)])

            with self.assertRaises(round_txn.TransactionError) as raised:
                round_txn.execution_gate(batch, batch)

            self.assertIn("... and 1 more findings", str(raised.exception))

    def test_unsupported_completion_marker_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            batch = factory / "batch-r01.jsonl"
            notes = factory / "NOTES-r01.md"
            write(batch, [thalamic("unsupported-version")])
            notes.write_text("# Critique\n\nConcrete gap.\n\nNovel coverage: 42%\n")
            marker = factory / "ROUND-r01.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 3,
                        "factory": factory.name,
                        "round": 1,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {"name": batch.name, "sha256": round_txn.file_sha256(batch)},
                            {"name": notes.name, "sha256": round_txn.file_sha256(notes)},
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
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

            with mock.patch.object(round_txn, "validate_completed_batch"):
                with self.assertRaisesRegex(
                    round_txn.TransactionError,
                    r"unsupported completion marker version: ",
                ):
                    round_txn.completed_manifests(factory)

    def test_publish_rejects_unsafe_or_mismatched_publishing_markers(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("unsafe-publishing")])
            publishing = factory / "ROUND-r01.publishing.json"
            publishing.symlink_to(Path(td) / "missing-publishing")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "unsafe publishing marker"
            ):
                round_txn.publish(factory, 1, reservation["token"])

        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("mismatched-publishing")])
            with mock.patch.object(
                round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
            ):
                with self.assertRaises(OSError):
                    round_txn.publish(factory, 1, reservation["token"])
            publishing = factory / "ROUND-r01.publishing.json"
            payload = json.loads(publishing.read_text())
            payload["token"] = "not-the-reservation-token"
            publishing.write_text(json.dumps(payload) + "\n")

            with self.assertRaisesRegex(
                round_txn.TransactionError, "publishing marker identity mismatch"
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_publish_retry_migrates_a_legacy_v1_publishing_marker(self):
        with tempfile.TemporaryDirectory() as td:
            factory = self.factory(td)
            reservation = round_txn.reserve(factory, 1, 1)
            self.stage(reservation, [thalamic("gate-v1-retry")])

            with mock.patch.object(
                round_txn, "copy_verified_exclusive", side_effect=OSError("boom")
            ):
                with self.assertRaises(OSError):
                    round_txn.publish(factory, 1, reservation["token"])

            publishing = factory / "ROUND-r01.publishing.json"
            legacy = json.loads(publishing.read_text())
            legacy["version"] = 1
            publishing.write_text(json.dumps(legacy) + "\n")

            manifest = round_txn.publish(factory, 1, reservation["token"])

            self.assertEqual(manifest["version"], 2)
            self.assertEqual(
                manifest["execution_verification"]["counts"]["verified"], 1
            )
            self.assertTrue((factory / "ROUND-r01.complete.json").is_file())


if __name__ == "__main__":
    unittest.main()
