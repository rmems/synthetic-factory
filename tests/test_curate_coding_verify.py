import copy
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from coding_curation_helpers import (  # noqa: E402
    curated_result,
    episode,
    visible_step,
)
from curate_coding import (  # noqa: E402
    MAX_DECISION_BASIS_CHARS,
    REASON_BASIS_CONCISED,
    REASON_BASIS_FROM_PLAN,
    REASON_HIDDEN_REASONING_REMOVED,
    REASON_INVALID_JSON,
    REASON_NO_RETAINABLE_STEPS,
    REASON_NO_VISIBLE_EVIDENCE,
    REASON_STEPS_EXCLUDED,
    REASON_THOUGHT_REMOVED,
    curate_episode,
    hash_value,
    verify_curation,
    verify_manifest,
)

class VerifyCurationTests(unittest.TestCase):
    def test_clean_run_reports_no_violations(self):
        result = curated_result([[visible_step(), visible_step(n=2)]])

        self.assertEqual(verify_curation(result), [])
        self.assertEqual(verify_curation(result, expected_source_steps=2), [])

    def test_excluded_steps_still_reconcile(self):
        result = curated_result([[visible_step(), {"n": 2, "thought": "only"}]])

        self.assertEqual(verify_curation(result, expected_source_steps=2), [])
        self.assertEqual(result["summary"]["excluded_steps"], 1)

    def test_declared_source_step_total_is_enforced(self):
        result = curated_result([[visible_step()]])

        violations = verify_curation(result, expected_source_steps=77)

        self.assertEqual(len(violations), 1)
        self.assertIn("expected 77 source steps", violations[0])

    def test_step_action_without_reason_codes_is_a_violation(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_actions"][0]["reason_codes"] = []

        violations = verify_curation(result)

        self.assertTrue(any("no reason codes recorded" in item for item in violations))

    def test_exclusion_without_an_exclusion_reason_is_a_violation(self):
        result = curated_result([[visible_step(), {"n": 2, "thought": "only"}]])
        excluded = result["manifest"][0]["step_actions"][1]
        excluded["reason_codes"] = [REASON_THOUGHT_REMOVED]

        violations = verify_curation(result)

        self.assertTrue(
            any("without an exclusion reason code" in item for item in violations)
        )

    def test_step_exclusions_reject_record_or_line_level_reasons(self):
        result = curated_result([[visible_step(), {"n": 2, "thought": "only"}]])
        excluded = result["manifest"][0]["step_actions"][1]
        excluded["thought_fields_removed"] = 0
        excluded["reason_codes"] = [REASON_INVALID_JSON]

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("exactly one step exclusion reason" in item for item in violations),
            violations,
        )
        self.assertTrue(
            any("excluded with impossible reason codes" in item for item in violations),
            violations,
        )

    def test_step_removal_count_and_reason_code_must_agree(self):
        missing_reason = curated_result([[visible_step()]])
        missing_reason_action = missing_reason["manifest"][0]["step_actions"][0]
        for code in (REASON_THOUGHT_REMOVED, REASON_HIDDEN_REASONING_REMOVED):
            if code in missing_reason_action["reason_codes"]:
                missing_reason_action["reason_codes"].remove(code)
                break

        zero_count = curated_result([[visible_step()]])
        zero_count["manifest"][0]["step_actions"][0]["thought_fields_removed"] = 0

        for result in (missing_reason, zero_count):
            with self.subTest(result=result):
                violations = verify_manifest(result["manifest"])
                self.assertTrue(
                    any(
                        "thought removal count and reason code disagree" in item
                        for item in violations
                    ),
                    violations,
                )

    def test_retained_step_without_visible_evidence_source_is_a_violation(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_actions"][0]["evidence_source"] = None

        violations = verify_curation(result)

        self.assertTrue(
            any("without a visible evidence source" in item for item in violations)
        )

    def test_excluded_step_cannot_claim_an_evidence_source(self):
        result = curated_result([[visible_step(), {"n": 2, "thought": "only"}]])
        result["manifest"][0]["step_actions"][1]["evidence_source"] = "plan"

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("excluded step records an evidence source" in item for item in violations),
            violations,
        )

    def test_retained_step_cannot_report_thought_removals(self):
        result = curated_result([[visible_step()]])
        manifest = result["manifest"][0]
        manifest["step_actions"][0]["action"] = "retained"
        manifest["step_counts"]["migrated"] = 0

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("retained step reports thought removals" in item for item in violations),
            violations,
        )

    def test_unchanged_record_cannot_report_transformations(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["action"] = "unchanged"

        violations = verify_manifest(result["manifest"])

        for expected in (
            "unchanged record reports thought removals",
            "unchanged record reports transformed step actions",
            "unchanged record reports transformation reason codes",
        ):
            self.assertTrue(any(expected in item for item in violations), violations)

    def test_modified_record_requires_transformation_evidence(self):
        already_observable = {
            "n": 1,
            "reflection": "The failure is deterministic outside UTC.",
            "decision_basis": "Reflection: The failure is deterministic outside UTC.",
        }
        result = curated_result([[already_observable]])
        self.assertEqual(result["manifest"][0]["action"], "unchanged")
        result["manifest"][0]["action"] = "modified"

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("no transformation evidence" in item for item in violations),
            violations,
        )

    def test_retained_step_cannot_use_exclusion_reasons(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_actions"][0]["reason_codes"].append(
            REASON_NO_VISIBLE_EVIDENCE
        )

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("retained with impossible reason codes" in item for item in violations),
            violations,
        )

    def test_concision_reason_must_match_visible_evidence(self):
        long_step = visible_step(
            reflection="visible evidence " * 40,
            observation="",
        )
        omitted = curated_result([[long_step]])
        omitted_action = omitted["manifest"][0]["step_actions"][0]
        self.assertIn(REASON_BASIS_CONCISED, omitted_action["reason_codes"])
        omitted_action["reason_codes"] = [
            code
            for code in omitted_action["reason_codes"]
            if code != REASON_BASIS_CONCISED
        ]

        invented = curated_result([[visible_step()]])
        invented["manifest"][0]["step_actions"][0]["reason_codes"].append(
            REASON_BASIS_CONCISED
        )

        for result in (omitted, invented):
            with self.subTest():
                violations = verify_curation(result)
                self.assertTrue(
                    any(
                        "concision reason does not match visible evidence" in item
                        for item in violations
                    ),
                    violations,
                )

    def test_source_step_number_must_match_retained_output_step(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_actions"][0]["source_step_number"] = 99

        violations = verify_curation(result)

        self.assertTrue(
            any(
                "source step number does not match the retained output step" in item
                for item in violations
            ),
            violations,
        )

    def test_surviving_thought_key_is_a_violation(self):
        result = curated_result([[visible_step()]])
        result["records"][0]["steps"][0]["thought"] = "leaked"

        violations = verify_curation(result)

        self.assertTrue(
            any("still exposes a thought key" in item for item in violations)
        )

    def test_unlabeled_or_oversized_basis_is_a_violation(self):
        result = curated_result([[visible_step()]])
        result["records"][0]["steps"][0]["decision_basis"] = "x" * (
            MAX_DECISION_BASIS_CHARS + 1
        )

        violations = verify_curation(result)

        self.assertTrue(
            any("does not open with a visible evidence label" in item for item in violations)
        )
        self.assertTrue(
            any(
                f"exceeds {MAX_DECISION_BASIS_CHARS} chars" in item
                for item in violations
            )
        )

    def test_step_counts_that_disagree_with_step_actions_are_a_violation(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_counts"]["retained"] = 0

        violations = verify_curation(result)

        self.assertTrue(
            any("disagree with the recorded step actions" in item for item in violations)
        )

    def test_manifest_missing_its_transform_identity_is_a_violation(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["transform"] = "something_else"
        result["manifest"][0]["source_hash"] = ""

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("is not a coding_observability manifest" in item for item in violations)
        )
        self.assertTrue(
            any("records no valid source hash" in item for item in violations)
        )

    def test_malformed_count_types_are_violations_instead_of_exceptions(self):
        result = curated_result([[visible_step()]])
        counts = result["manifest"][0]["step_counts"]
        counts.update(
            {"source": "1", "retained": None, "migrated": True, "excluded": -1}
        )

        violations = verify_manifest(result["manifest"])

        for key in ("source", "retained", "migrated", "excluded"):
            self.assertTrue(
                any(f"step_counts.{key}" in item for item in violations),
                violations,
            )

    def test_non_object_step_actions_are_violations_instead_of_exceptions(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_actions"][0] = None

        violations = verify_manifest(result["manifest"])

        self.assertTrue(any("is not an object" in item for item in violations))

    def test_invalid_reason_code_values_are_violations_instead_of_exceptions(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_actions"][0]["reason_codes"] = [{}]

        violations = verify_manifest(result["manifest"])

        self.assertTrue(any("invalid reason codes" in item for item in violations))

    def test_decision_basis_must_equal_derived_visible_evidence(self):
        result = curated_result([[visible_step(plan="inspect the real failure")]])
        step = result["records"][0]["steps"][0]
        step["decision_basis"] = "Plan: invented evidence"
        result["manifest"][0]["output_hash"] = hash_value(result["records"][0])

        violations = verify_curation(result)

        self.assertTrue(any("not grounded" in item for item in violations))

    def test_curated_record_must_match_its_manifest_output_hash(self):
        result = curated_result(
            [
                [visible_step(reflection="first visible result")],
                [visible_step(reflection="second visible result")],
            ]
        )
        result["records"].reverse()

        violations = verify_curation(result)

        self.assertEqual(
            sum("output hash does not match" in item for item in violations), 2
        )

    def test_record_exclusion_requires_an_exclusion_reason(self):
        _, manifest = curate_episode(episode([]))
        manifest["reason_codes"] = [REASON_THOUGHT_REMOVED]

        violations = verify_manifest([manifest])

        self.assertTrue(
            any(
                "record excluded without an exclusion reason" in item
                for item in violations
            )
        )

    def test_migrated_count_must_match_step_actions(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_counts"]["migrated"] = 0

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("disagree with the recorded step actions" in item for item in violations)
        )

    def test_hidden_reasoning_alias_is_a_curation_violation(self):
        result = curated_result([[visible_step()]])
        result["records"][0]["steps"][0]["chain_of_thought"] = "private"
        result["manifest"][0]["output_hash"] = hash_value(result["records"][0])

        violations = verify_curation(result)

        self.assertTrue(
            any("still exposes a thought key" in item for item in violations)
        )

    def test_source_and_output_step_indexes_must_be_sequential(self):
        result = curated_result([[visible_step(), visible_step(n=2)]])
        actions = result["manifest"][0]["step_actions"]
        actions[1]["source_step_index"] = 1
        actions[1]["output_step_index"] = 1

        violations = verify_manifest(result["manifest"])

        self.assertTrue(any("source step indexes" in item for item in violations))
        self.assertTrue(
            any("retained output step indexes" in item for item in violations)
        )

    def test_manifest_evidence_source_must_match_the_curated_step(self):
        result = curated_result([[visible_step()]])
        action = result["manifest"][0]["step_actions"][0]
        action["evidence_source"] = "plan"
        action["reason_codes"].append(REASON_BASIS_FROM_PLAN)

        violations = verify_curation(result)

        self.assertTrue(
            any("does not match its manifest action" in item for item in violations)
        )

    def test_summary_must_reconcile_with_manifest_totals(self):
        result = curated_result([[visible_step()]])
        result["summary"]["migrated_steps"] = 0

        violations = verify_curation(result)

        self.assertTrue(any("summary migrated_steps" in item for item in violations))

    def test_hand_built_summary_may_omit_wrap_records(self):
        result = curated_result([[visible_step()]])
        del result["summary"]["wrap_records"]

        self.assertEqual(verify_curation(result), [])

    def test_excluded_record_cannot_claim_retained_steps(self):
        result = curated_result([[visible_step()]])
        manifest = result["manifest"][0]
        manifest.update(
            {
                "action": "excluded",
                "reason_codes": [REASON_NO_RETAINABLE_STEPS],
                "output_hash": None,
                "output_id": None,
            }
        )

        violations = verify_manifest([manifest])

        self.assertTrue(
            any("excluded record retains 1 step" in item for item in violations),
            violations,
        )

    def test_pre_step_exclusion_cannot_invent_step_actions(self):
        result = curated_result([[visible_step()]])
        manifest = result["manifest"][0]
        manifest.update(
            {
                "action": "excluded",
                "reason_codes": [REASON_INVALID_JSON],
                "output_hash": None,
                "output_id": None,
            }
        )

        violations = verify_manifest([manifest], expected_source_steps=1)

        self.assertTrue(
            any("pre-step exclusion must have zero source steps" in item for item in violations),
            violations,
        )

    def test_retained_manifest_must_keep_a_step(self):
        result = curated_result([[{"n": 1, "thought": "only"}]])
        manifest = result["manifest"][0]
        self.assertEqual(manifest["action"], "excluded")
        manifest.update(
            {
                "action": "modified",
                "output_hash": "a" * 64,
                "reason_codes": [REASON_STEPS_EXCLUDED],
            }
        )

        violations = verify_manifest([manifest])

        self.assertTrue(
            any("must keep at least one step" in item for item in violations),
            violations,
        )

    def test_duplicate_manifest_source_locations_are_rejected(self):
        result = curated_result([[visible_step()], [visible_step()]])
        result["manifest"][1] = copy.deepcopy(result["manifest"][0])
        result["records"][1] = copy.deepcopy(result["records"][0])

        violations = verify_curation(result, expected_source_steps=2)

        self.assertTrue(
            any("duplicate manifest source location" in item for item in violations),
            violations,
        )

    def test_manifest_thought_removal_count_matches_step_actions(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["thought_fields_removed"] = 0

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any(
                "thought_fields_removed does not account for the step actions" in item
                for item in violations
            ),
            violations,
        )

    def test_summary_rejects_disagreeing_dual_removal_fields(self):
        result = curated_result([[visible_step()]])
        result["summary"]["thought_fields_removed"] = 0
        result["summary"]["hidden_reasoning_fields_removed"] = 1

        violations = verify_curation(result)

        self.assertTrue(
            any("disagrees with hidden_reasoning_fields_removed" in item for item in violations),
            violations,
        )

    def test_summary_reconciles_thought_removals_and_evidence_sources(self):
        result = curated_result([[visible_step()]])
        result["summary"]["thought_fields_removed"] = 0
        result["summary"]["hidden_reasoning_fields_removed"] = 0
        result["summary"]["decision_basis_sources"] = {"plan": 1}

        violations = verify_curation(result)

        self.assertTrue(
            any(
                "summary thought_fields_removed" in item
                or "summary hidden_reasoning_fields_removed" in item
                for item in violations
            ),
            violations,
        )
        self.assertTrue(
            any("summary decision_basis_sources" in item for item in violations),
            violations,
        )


if __name__ == "__main__":
    unittest.main()
