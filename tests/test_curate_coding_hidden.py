import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from coding_curation_helpers import (  # noqa: E402
    episode,
    visible_step,
    wrap_record,
)
from curate_coding import (  # noqa: E402
    MAX_DECISION_BASIS_CHARS,
    REASON_HIDDEN_REASONING_REMOVED,
    REASON_NO_RETAINABLE_STEPS,
    REASON_NO_VISIBLE_EVIDENCE,
    REASON_STEPS_NOT_ARRAY,
    REASON_WRAP_RECORD,
    contains_hidden_reasoning_key,
    curate_episode,
    curate_jsonl,
    is_hidden_reasoning_key,
    verify_curation,
    verify_manifest,
)
from validate_run import HIDDEN_THOUGHT_KEYS  # noqa: E402

class HiddenReasoningKeyTests(unittest.TestCase):
    def test_audit_vocabulary_and_every_internal_reasoning_variant_is_hidden(self):
        for key in (
            *sorted(HIDDEN_THOUGHT_KEYS),
            "Thought",
            "reasoning",
            "Reasoning",
            "internal_reasoning",
            "internalReasoning",
            "internal_reasoning_verbatim",
            "internal_reasoning_optimizer",
            "internal_reasoning_as_stated",
            "internal_reasoning2",
            "internal_reasoningverbatim",
        ):
            with self.subTest(key=key):
                self.assertTrue(is_hidden_reasoning_key(key))

    def _assert_plain_step_keys_removed(self, source, missing_keys, removed):
        curated, manifest = curate_episode(source)
        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_reasoning_key(curated))
        step = curated["steps"][0]
        for key in missing_keys:
            self.assertNotIn(key, step)
        self.assertEqual(
            manifest["step_actions"][0]["hidden_reasoning_fields_removed"], removed
        )
        return curated, manifest

    def test_plain_episode_internal_reasoning_variants_are_stripped(self):
        cases = (
            (
                "undelimited suffixes",
                {
                    "internal_reasoning2": "private numbered trace",
                    "internal_reasoningverbatim": "private verbatim trace",
                },
                ("internal_reasoning2", "internal_reasoningverbatim"),
            ),
            (
                "delimited fields",
                {
                    "internal_reasoning": "private step rationale",
                    "internal_reasoning_verbatim": "verbatim private step rationale",
                },
                ("internal_reasoning", "internal_reasoning_verbatim"),
            ),
        )
        for label, extra, missing_keys in cases:
            with self.subTest(label=label):
                self._assert_plain_step_keys_removed(
                    episode([visible_step(**extra)]),
                    missing_keys,
                    3,
                )

    def test_complete_audit_vocabulary_is_stripped_from_a_wrap_record(self):
        source = wrap_record(
            [
                visible_step(
                    chain_of_thought="private chain",
                    scratch="private scratch",
                    inner_monologue="private monologue",
                )
            ]
        )

        curated, manifest = curate_episode(source)

        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_reasoning_key(curated))
        step = curated["executed_action"]["steps"][0]
        for key in HIDDEN_THOUGHT_KEYS:
            self.assertNotIn(key, step)
        # Two gate-level internal_reasoning fields plus all four scratch-pad
        # keys on the embedded coding step.
        self.assertEqual(manifest["hidden_reasoning_fields_removed"], 6)

    def test_visible_evidence_keys_are_not_hidden(self):
        for key in (
            "plan",
            "reflection",
            "observation",
            "tool_call",
            "decision_basis",
            "thoughts",
            "reasoning_flaw",
            "safety_decision",
        ):
            with self.subTest(key=key):
                self.assertFalse(is_hidden_reasoning_key(key))

    def test_output_does_not_depend_on_internal_reasoning_content(self):
        first = episode([visible_step(internal_reasoning="secret A")])
        second = episode(
            [visible_step(internal_reasoning="an entirely different secret B")]
        )

        first_output, _ = curate_episode(first)
        second_output, _ = curate_episode(second)

        self.assertEqual(first_output, second_output)

    def test_reasoning_is_stripped_from_wrap_gate_and_embedded_step(self):
        source = wrap_record([visible_step(reasoning="private step trace")])
        source["proposed_action"]["reasoning"] = "private gate trace"

        curated, manifest = curate_episode(source)

        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_reasoning_key(curated))
        self.assertNotIn("reasoning", curated["proposed_action"])
        self.assertNotIn("reasoning", curated["executed_action"]["steps"][0])
        self.assertFalse(is_hidden_reasoning_key("reasoning_flaw"))
        # Two gate-level internal_reasoning* fields, wrap-level reasoning,
        # plus thought and reasoning on the embedded coding step.
        self.assertEqual(manifest["hidden_reasoning_fields_removed"], 5)


class WrapRecordTests(unittest.TestCase):
    def test_wrap_record_is_curated_through_executed_action(self):
        source = wrap_record([visible_step()])

        curated, manifest = curate_episode(source, source_path="wraps.jsonl")

        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_reasoning_key(curated))
        self.assertNotIn("internal_reasoning", curated["proposed_action"])
        self.assertNotIn("internal_reasoning_verbatim", curated["proposed_action"])
        # The visible half of the gate record survives untouched.
        self.assertEqual(
            curated["proposed_action"]["action_type"], "delegate_to_coding_agent"
        )
        self.assertEqual(curated["safety_decision"], source["safety_decision"])
        step = curated["executed_action"]["steps"][0]
        self.assertEqual(
            step["decision_basis"],
            "Reflection: The failure is deterministic outside UTC. "
            "Inspect both clocks next.",
        )
        self.assertLessEqual(len(step["decision_basis"]), MAX_DECISION_BASIS_CHARS)
        self.assertEqual(manifest["steps_path"], "executed_action.steps")
        self.assertIn(REASON_WRAP_RECORD, manifest["reason_codes"])
        self.assertIn(REASON_HIDDEN_REASONING_REMOVED, manifest["reason_codes"])
        self.assertEqual(manifest["step_counts"], {
            "source": 1,
            "retained": 1,
            "migrated": 1,
            "excluded": 0,
        })
        # 2 on proposed_action plus 1 thought on the wrapped step.
        self.assertEqual(manifest["hidden_reasoning_fields_removed"], 3)

    def test_wrap_record_step_without_visible_evidence_is_excluded(self):
        source = wrap_record([{"n": 1, "thought": "the only possible source"}])

        curated, manifest = curate_episode(source)

        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_NO_RETAINABLE_STEPS])
        self.assertEqual(manifest["steps_path"], "executed_action.steps")
        self.assertIn(
            REASON_NO_VISIBLE_EVIDENCE, manifest["step_actions"][0]["reason_codes"]
        )

    def test_wrap_record_curation_is_output_idempotent(self):
        source = wrap_record([visible_step(), visible_step(n=2)])

        once, _ = curate_episode(source)
        twice, second_manifest = curate_episode(once)

        self.assertEqual(once, twice)
        self.assertEqual(second_manifest["action"], "unchanged")
        self.assertEqual(second_manifest["step_counts"]["migrated"], 0)

    def test_wrap_record_initial_migration_passes_verification(self):
        source = wrap_record([visible_step()])

        _, manifest = curate_episode(source)

        self.assertEqual(manifest["action"], "modified")
        self.assertIn(REASON_WRAP_RECORD, manifest["reason_codes"])
        self.assertIn(REASON_HIDDEN_REASONING_REMOVED, manifest["reason_codes"])
        violations = verify_manifest([manifest])
        self.assertEqual(violations, [])

    def test_wrap_record_passes_verify_curation(self):
        source = wrap_record([visible_step()])
        curated, manifest = curate_episode(source)
        result = {
            "records": [curated],
            "manifest": [manifest],
            "summary": {
                "input_records": 1,
                "output_records": 1,
                "excluded_records": 0,
                "source_steps": 1,
                "retained_steps": 1,
                "migrated_steps": 1,
                "excluded_steps": 0,
                "hidden_reasoning_fields_removed": manifest[
                    "hidden_reasoning_fields_removed"
                ],
                "decision_basis_sources": {"reflection": 1},
            },
        }

        self.assertEqual(verify_curation(result), [])

    def test_wrap_record_idempotent_second_pass_passes_verification(self):
        source = wrap_record([visible_step()])

        once, _ = curate_episode(source)
        twice, second_manifest = curate_episode(once)

        self.assertEqual(once, twice)
        self.assertEqual(second_manifest["action"], "unchanged")
        self.assertEqual(second_manifest["reason_codes"], [REASON_WRAP_RECORD])
        violations = verify_manifest([second_manifest])
        self.assertEqual(violations, [])

    def test_top_level_steps_win_over_a_wrapped_step_array(self):
        source = episode([visible_step()])
        source["executed_action"] = {"steps": [{"n": 9, "thought": "ignored"}]}

        curated, manifest = curate_episode(source)

        self.assertEqual(manifest["steps_path"], "steps")
        self.assertNotIn(REASON_WRAP_RECORD, manifest["reason_codes"])
        self.assertEqual(len(curated["steps"]), 1)
        # The nested array is still scrubbed, just not curated as the episode.
        self.assertFalse(contains_hidden_reasoning_key(curated))

    def test_record_without_any_step_array_is_excluded(self):
        source = wrap_record([visible_step()])
        source["executed_action"].pop("steps")

        curated, manifest = curate_episode(source)

        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_STEPS_NOT_ARRAY])
        self.assertIsNone(manifest["steps_path"])

    def test_jsonl_summary_counts_wrap_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "mixed.jsonl"
            source.write_text(
                json.dumps(episode([visible_step()]), ensure_ascii=False)
                + "\n"
                + json.dumps(wrap_record([visible_step()]), ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )

            result = curate_jsonl(source)

        self.assertEqual(result["summary"]["input_records"], 2)
        self.assertEqual(result["summary"]["output_records"], 2)
        self.assertEqual(result["summary"]["wrap_records"], 1)
        self.assertEqual(result["summary"]["hidden_reasoning_fields_removed"], 4)
        self.assertEqual(verify_curation(result), [])
        result["summary"]["wrap_records"] = 0
        violations = verify_curation(result)
        self.assertTrue(any("summary wrap_records" in item for item in violations))
        for record in result["records"]:
            self.assertFalse(contains_hidden_reasoning_key(record))


if __name__ == "__main__":
    unittest.main()
