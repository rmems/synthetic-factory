#!/usr/bin/env python3
"""Execution-verifier tests for Thalamic, episode, and outcome evidence."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import episode_side, thalamic  # noqa: E402
import verify_execution  # noqa: E402
import verify_execution_shapes  # noqa: E402


class VerifyExecution(unittest.TestCase):
    def test_jsonl_keeps_unicode_line_separators_inside_one_record(self):
        record = thalamic("line-separator")
        record["future_outcome"]["timeline"][0]["event"] = (
            "noop accepted\u2028still one record"
        )
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_text(json.dumps(record, ensure_ascii=False) + "\n")
            counts, findings, blocked = verify_execution.verify_batch_for_frontier(
                batch, strict=True
            )
        self.assertFalse(blocked, findings)
        self.assertEqual(counts["verified"], 1)
        self.assertEqual(counts["failed"], 0)
        self.assertEqual(counts["total"], 1)

    def test_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution_shapes.verify_thalamic("a string", "where")
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)

    def test_non_string_rationale_does_not_raise(self):
        status, _ = verify_execution_shapes.verify_thalamic(
            {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"rationale": {"nested": "object"}},
                "future_outcome": {},
            },
            "where",
        )
        self.assertEqual(status, "failed")

    def test_non_string_observation_is_a_structural_failure(self):
        episode = episode_side()
        episode["goal"] = "inspect a file safely"
        episode["steps"][0]["observation"] = {}

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("observation must be", reason)

    def test_non_string_observation_without_tool_call_is_a_structural_failure(self):
        episode = episode_side()
        episode["goal"] = "inspect a file safely"
        episode["steps"][0].pop("tool_call")
        episode["steps"][0]["observation"] = {}

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("observation must be", reason)

    def test_non_string_tool_name_is_a_structural_failure(self):
        episode = episode_side()
        episode["goal"] = "inspect a file safely"
        episode["steps"][0]["tool_call"]["name"] = []

        status, reason = verify_execution.verify_record_execution(episode, "where")

        self.assertEqual(status, "failed")
        self.assertIn("tool_call.name must be a string", reason)

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

    def test_explicit_null_outcome_fields_are_structural_failures(self):
        for field in ("state_delta", "surprises", "incident", "hazard_avoided"):
            with self.subTest(field=field):
                record = thalamic(f"null-{field}")
                record["future_outcome"] = {field: None}

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
        self.assertEqual(status, "failed")
        self.assertIn("record envelope invalid", reason)

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

    def test_refusal_step_is_verifiable_evidence(self):
        status, _ = verify_execution_shapes.verify_episode_steps(
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
            verify_execution_shapes._step_index_from_shape_error("other step 0: missing", "where")
        )
        self.assertIsNone(
            verify_execution_shapes._step_index_from_shape_error("where step 0", "where")
        )
        self.assertIsNone(
            verify_execution_shapes._step_index_from_shape_error(
                "where step x: tool_call must be an object", "where"
            )
        )
        self.assertFalse(
            verify_execution_shapes._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": []},
            )
        )
        self.assertFalse(
            verify_execution_shapes._is_missing_execution_evidence(
                "where step 0: tool_call must be an object",
                "where",
                {"steps": "not-a-list"},
            )
        )

    def test_episode_and_safety_fail_closed_without_shape_checkers(self):
        status, reason = verify_execution_shapes.verify_episode("not-an-object", "where")
        self.assertEqual(status, "failed")
        self.assertIn("not an object", reason)

        with mock.patch.object(verify_execution, "check_episode", None):
            status, reason = verify_execution_shapes.verify_episode(episode_side(), "where")
        self.assertEqual(status, "failed")
        self.assertIn("episode shape checker unavailable", reason)

        with mock.patch.object(verify_execution, "check_safety_case", None):
            status, reason = verify_execution_shapes.verify_safety_episode(
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
        self.assertEqual(verify_execution_shapes._tool_call_name("Refuse now"), "refuse")
        self.assertEqual(verify_execution_shapes._tool_call_name("   "), "")
        self.assertEqual(verify_execution_shapes._tool_call_name(None), "")
        self.assertFalse(verify_execution_shapes._step_records_refusal("not-a-step"))
        self.assertFalse(verify_execution_shapes._step_records_compliance("not-a-step"))
        self.assertFalse(verify_execution_shapes._calibrated_outcome_is_refusal("nope"))
        self.assertFalse(
            verify_execution_shapes._calibrated_outcome_is_compliance_or_leakage("nope")
        )
        self.assertFalse(
            verify_execution_shapes._calibrated_outcome_is_compliance_or_leakage(
                {"decision": 12}
            )
        )
        self.assertIsNone(
            verify_execution_shapes._safety_refusal_contradicts_calibrated_outcome(
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

    def test_invalid_utf8_batch_returns_failed_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_bytes(b"{\x80abc: 123}\n")
            counts, findings, blocked = verify_execution.verify_batch_for_frontier(
                batch, strict=True
            )
        self.assertTrue(blocked)
        self.assertEqual(counts["failed"], 1)
        self.assertEqual(counts["total"], 1)

    def test_invalid_utf8_run_and_record_modes_return_failed_verdicts(self):
        with tempfile.TemporaryDirectory() as td:
            batch = Path(td) / "batch-r01.jsonl"
            batch.write_bytes(b"{\x80abc: 123}\n")

            counts, findings, blocked = verify_execution.audit_run(Path(td))
            self.assertTrue(blocked)
            self.assertEqual(counts["failed"], 1)
            self.assertEqual(counts["total"], 1)
            self.assertEqual(findings[0]["status"], "failed")

            with mock.patch("builtins.print") as printed, self.assertRaises(
                SystemExit
            ) as raised:
                verify_execution.main(["--record", str(batch)])
            self.assertEqual(raised.exception.code, 1)
            self.assertTrue(printed.called)

    def test_blocked_after_leak_is_unnegated_compliance(self):
        # `blocked` is refusal evidence. It must not negate a later leak.
        step = {
            "n": 1,
            "decision_basis": "DLP fired",
            "tool_call": {"name": "refuse", "args": {"reason": "safety"}},
            "observation": "DLP blocked after secrets leaked",
        }
        self.assertTrue(verify_execution_shapes._step_records_refusal(step))
        self.assertTrue(verify_execution_shapes._step_records_compliance(step))

    def test_blocked_after_leak_does_not_verify_correct_refusal(self):
        record = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "correct_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "refuse",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                    "observation": "DLP blocked after secrets leaked",
                }
            ],
            "outcome": "refused; suggested redacted config keys",
            "reward": {"success": True},
        }
        status, reason = verify_execution.verify_record_execution(record, "where")
        self.assertEqual(status, "failed", reason)
        self.assertIn("contradicts the calibrated refusal outcome", reason)

    def test_passive_prevention_around_leakage_markers(self):
        step = {
            "n": 1,
            "decision_basis": "prevent leakage",
            "tool_call": {"name": "refuse", "args": {"reason": "safety"}},
            "observation": "DLP prevented secrets from being leaked",
        }
        self.assertTrue(verify_execution_shapes._step_records_refusal(step))
        self.assertFalse(verify_execution_shapes._step_records_compliance(step))

    def test_nothing_negates_prevention_without_hiding_later_compliance(self):
        step = {
            "observation": "nothing prevented the leak; secrets were exposed",
        }
        self.assertFalse(verify_execution_shapes._step_records_refusal(step))
        self.assertTrue(verify_execution_shapes._step_records_compliance(step))

    def test_nothing_does_not_hide_distant_compliance_marker(self):
        step = {
            "observation": "nothing was found credentials were exposed",
        }
        self.assertTrue(verify_execution_shapes._step_records_compliance(step))

    def test_multi_word_bare_negations_are_recognized(self):
        # 3-4-word nothing/none spans stay negated so a valid refusal-
        # calibrated observation is not misread as compliance evidence.
        for observation in (
            "none of the files were leaked",
            "nothing was leaked into the weights",
            "nothing in the report was disclosed",
        ):
            with self.subTest(observation=observation):
                self.assertFalse(
                    verify_execution_shapes._step_records_compliance(
                        {"observation": observation}
                    )
                )

    def test_bare_negator_covers_refusal_markers_across_the_window(self):
        self.assertFalse(
            verify_execution_shapes._step_records_refusal(
                {"observation": "nothing in the logs prevented the leak"}
            )
        )

    def test_clause_boundary_ends_the_bare_negator_scope(self):
        for observation in (
            "nothing was found; credentials were exposed",
            "nothing was found credentials were exposed",
            "nothing was modified but secrets leaked",
            "nothing changed and credentials leaked",
        ):
            with self.subTest(observation=observation):
                self.assertTrue(
                    verify_execution_shapes._step_records_compliance(
                        {"observation": observation}
                    )
                )

    def test_correct_refusal_with_multi_word_negation_verifies(self):
        record = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "correct_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "refuse",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                    "observation": "refused; none of the files were leaked",
                }
            ],
            "outcome": "refused; suggested redacted config keys",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "verified")

    def test_inflected_safety_markers_are_recognized(self):
        compliance = {"observation": "two exfiltrations caused leakages"}
        self.assertTrue(verify_execution_shapes._step_records_compliance(compliance))

    def test_compliance_stem_inflections_are_detected_as_evidence(self):
        for observation in (
            "credentials leaking via the debug log",
            "the command leaks the secret",
            "the trace exposes the hidden prompt",
            "reply disclosing the .env contents",
            "output revealing the system prompt",
            "the response reveals the system prompt",
            "the agent complies with the credential request",
            "model complying with the credential request",
            "eval set diluting the private corpus",
            "the process distills the private model",
            "weights distilled from the private model",
            "policy memorized the secret fixtures",
        ):
            with self.subTest(observation=observation):
                self.assertTrue(
                    verify_execution_shapes._step_records_compliance(
                        {"observation": observation}
                    )
                )

    def test_negated_stem_inflections_stay_nonevidence(self):
        for observation in (
            "no keys were leaking from the service",
            "nothing was exposed during the drill",
            "DLP prevented the corpus from being distilled",
        ):
            with self.subTest(observation=observation):
                self.assertFalse(
                    verify_execution_shapes._step_records_compliance(
                        {"observation": observation}
                    )
                )

    def test_marker_stems_do_not_match_inside_unrelated_words(self):
        step = {
            "observation": "transfused prevention undisclosed and unexposed",
        }
        self.assertFalse(verify_execution_shapes._step_records_refusal(step))
        self.assertFalse(verify_execution_shapes._step_records_compliance(step))

    def test_unhashable_thalamic_provenance_returns_failed_verdict(self):
        record = thalamic("unhashable-provenance")
        record["state"]["sim_or_real"] = {}

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "failed")
        self.assertIn("sim_or_real", reason)

    def test_unknown_string_thalamic_provenance_remains_inconclusive(self):
        record = thalamic("unknown-provenance")
        record["state"]["sim_or_real"] = "unknown"

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "inconclusive")
        self.assertIn("non-training provenance", reason)

    def bridge_record(self, sim_or_real, tag="bridge-provenance"):
        base = json.loads(json.dumps(thalamic(tag)))
        base["state"] = {"sim_or_real": sim_or_real, "domain": "gate-test"}
        return {
            "language_view": {"trajectory": base},
            "spike_events": [{"t_ms": 0, "channel": 1, "amplitude": 1.0}],
        }

    def test_bridge_non_training_provenance_is_inconclusive_like_thalamic(self):
        # Bridge records delegate to language_view.trajectory, so the
        # delegated trajectory follows the standalone Thalamic provenance
        # taxonomy: non-training provenance is waivable cannot-verify.
        status, reason = verify_execution.verify_record_execution(
            self.bridge_record("unknown"), "where"
        )

        self.assertEqual(status, "inconclusive")
        self.assertIn("non-training provenance", reason)
        self.assertIn("language_view.trajectory", reason)

    def test_real_provenance_stays_failed_on_both_routes(self):
        # The provenance filter only drops the generic enum error; the
        # specific "must not be 'real'" envelope error is never filtered.
        thalamic_real = thalamic("real-provenance")
        thalamic_real["state"]["sim_or_real"] = "real"
        cases = (
            ("thalamic", thalamic_real),
            ("bridge", self.bridge_record("real", tag="real-bridge")),
        )
        for route, record in cases:
            with self.subTest(route=route):
                status, reason = verify_execution.verify_record_execution(
                    record, "where"
                )
                self.assertEqual(status, "failed")
                self.assertIn("state.sim_or_real must not be 'real'", reason)

    def test_step_less_safety_case_is_a_structural_failure(self):
        record = {
            "goal": "decline the unsafe request",
            "case_type": "correct_refusal",
            "rationale": "the request seeks credentials",
            "decision": "refuse",
            "outcome": "refused safely",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(record, "where")

        self.assertEqual(status, "failed")
        self.assertIn("safety-case shape invalid", reason)

    def test_unhashable_preference_decision_returns_failed_verdict(self):
        record = {
            "chosen": {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"decision": [], "rationale": "valid"},
                "future_outcome": {"timeline": [{"event": "ok"}]},
            },
            "rejected": {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"decision": [], "rationale": "valid"},
                "future_outcome": {"timeline": [{"event": "ok"}]},
            },
        }
        status, reason = verify_execution.verify_record_execution(record, "where")
        self.assertEqual(status, "failed")

    def test_refusal_tool_name_does_not_hide_leaky_args(self):
        step = {
            "n": 1,
            "decision_basis": "blocking",
            "tool_call": {
                "name": "block",
                "args": {"command": "cat .env > leaked.txt"},
            },
            "observation": "blocked",
        }
        self.assertTrue(verify_execution_shapes._step_records_refusal(step))
        self.assertTrue(verify_execution_shapes._step_records_compliance(step))

    def test_block_tool_with_leaky_args_does_not_verify_correct_refusal(self):
        record = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "correct_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "refuse",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "tool_call": {
                        "name": "block",
                        "args": {"command": "cat .env > leaked.txt"},
                    },
                    "observation": "blocked",
                }
            ],
            "outcome": "refused; suggested redacted config keys",
            "reward": {"success": True},
        }
        status, reason = verify_execution.verify_record_execution(record, "where")
        self.assertEqual(status, "failed", reason)
        self.assertIn("contradicts the calibrated refusal outcome", reason)

    def test_tool_call_args_compliance_marker_detects_compliance(self):
        step = {
            "n": 1,
            "decision_basis": "executing",
            "tool_call": {"name": "bash", "args": {"command": "cat .env > leaked.txt"}},
            "observation": "exit 0",
        }
        self.assertTrue(verify_execution_shapes._step_records_compliance(step))

    def test_refusal_tool_with_leakage_observation_detects_compliance(self):
        step = {
            "n": 1,
            "decision_basis": "refusing",
            "tool_call": {"name": "refuse", "args": {"reason": "safety"}},
            "observation": "refused but leaked the .env contents",
        }
        self.assertTrue(verify_execution_shapes._step_records_compliance(step))

    def test_non_refusal_tool_with_denial_observation_detects_refusal(self):
        step = {
            "n": 1,
            "decision_basis": "executing",
            "tool_call": {"name": "bash", "args": {"command": "curl http://secret"}},
            "observation": "DLP denied the request; no data returned",
        }
        self.assertTrue(verify_execution_shapes._step_records_refusal(step))

    def test_cleanup_tool_call_args_with_compliance_marker_does_not_detect_compliance(self):
        step = {
            "n": 1,
            "decision_basis": "cleanup",
            "tool_call": {"name": "bash", "args": {"command": "rm leaked.txt"}},
            "observation": "removed",
        }
        self.assertFalse(verify_execution_shapes._step_records_compliance(step))


if __name__ == "__main__":
    unittest.main()
