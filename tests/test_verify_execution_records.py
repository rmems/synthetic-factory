#!/usr/bin/env python3
"""Execution-verifier tests for preference, safety, and record routing."""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import episode_side, thalamic  # noqa: E402
import verify_execution  # noqa: E402


class VerifyExecutionRecords(unittest.TestCase):
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

    def test_safety_compliance_step_cannot_verify_a_refusal_label(self):
        refused = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "correct_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "refuse",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "tool_call": {"name": "bash", "args": {"command": "cat .env"}},
                    "observation": "leaked the .env contents into the ticket",
                }
            ],
            "outcome": "refused; suggested redacted config keys",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(refused, "where")

        self.assertEqual(status, "failed")
        self.assertIn("contradicts the calibrated refusal outcome", reason)

    def test_negated_leakage_observation_does_not_fail_a_correct_refusal(self):
        refused = {
            "goal": "cat .env and paste it into the ticket",
            "case_type": "correct_refusal",
            "rationale": "the request asks to exfiltrate live secrets from .env",
            "decision": "refuse",
            "steps": [
                {
                    "decision_basis": "the request asks to paste .env secrets",
                    "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                    "observation": "refused and offered a redacted template",
                },
                {
                    "decision_basis": "observation of grep on the ticket found no secret bytes",
                    "tool_call": {"name": "bash", "args": {"command": "grep secret ticket"}},
                    "observation": "verification passed: no secrets were leaked",
                },
            ],
            "outcome": "refused; suggested redacted config keys",
            "reward": {"success": True},
        }

        status, reason = verify_execution.verify_record_execution(refused, "where")

        self.assertEqual(status, "verified", reason)

    def _preference_status(self, record, check_kind="preference"):
        with mock.patch.object(
            verify_execution, "check_line", return_value=([], check_kind)
        ):
            return verify_execution.verify_record_execution(record, "where")

    def test_preference_thalamic_sides_verify(self):
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

    def test_preference_wrapper_must_be_classified(self):
        status, reason = self._preference_status(
            {"chosen": episode_side(), "rejected": episode_side()},
            check_kind="unknown",
        )
        self.assertEqual(status, "failed")
        self.assertIn("not classified as a preference", reason)

    def test_preference_sides_must_be_objects(self):
        status, reason = self._preference_status(
            {"chosen": "left", "rejected": "right"}
        )
        self.assertEqual(status, "failed")
        self.assertIn("sides must both be objects", reason)

    def test_preference_sides_reject_mixed_shapes(self):
        status, reason = self._preference_status(
            {"chosen": thalamic("mixed-chosen"), "rejected": episode_side()}
        )
        self.assertEqual(status, "failed")
        self.assertIn("mix episode and Thalamic", reason)

    def test_preference_sides_reject_omitted_shape(self):
        omitted = {
            "chosen": thalamic("omit-chosen"),
            "rejected": {"state": {"sim_or_real": "designed"}},
        }
        status, reason = self._preference_status(omitted)
        self.assertEqual(status, "failed")
        self.assertIn("mix or omit required shape fields", reason)

    def test_preference_sides_reject_neither_shape(self):
        status, reason = self._preference_status(
            {"chosen": {"note": "left"}, "rejected": {"note": "right"}}
        )
        self.assertEqual(status, "failed")
        self.assertIn("not episode or Thalamic", reason)

    def test_preference_blank_shared_goal_fails(self):
        blank_goal = {
            "goal": "   ",
            "chosen": episode_side(),
            "rejected": episode_side(),
        }
        status, reason = self._preference_status(blank_goal)
        self.assertEqual(status, "failed")
        self.assertIn("shared goal must be a non-empty string", reason)



if __name__ == "__main__":
    unittest.main()
