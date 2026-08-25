import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from curate_coding import (  # noqa: E402
    HIDDEN_THOUGHT_KEYS,
    MAX_DECISION_BASIS_CHARS,
    REASON_BASIS_FROM_OBSERVATION,
    REASON_BASIS_FROM_PLAN,
    REASON_BASIS_FROM_REFLECTION,
    REASON_BASIS_FROM_TOOL_CALL,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_NO_RETAINABLE_STEPS,
    REASON_NO_VISIBLE_EVIDENCE,
    REASON_STEP_NOT_OBJECT,
    REASON_THOUGHT_REMOVED,
    contains_thought_key,
    curate_episode,
    curate_jsonl,
    curate_step,
    hash_value,
    verify_curation,
    verify_manifest,
)


def visible_step(**overrides):
    step = {
        "n": 1,
        "thought": "private scratch text that must never affect output",
        "tool_call": {"name": "bash", "args": {"command": "pytest -q"}},
        "observation": "Two tests failed with a timezone mismatch.",
        "reflection": "The failure is deterministic outside UTC. Inspect both clocks next.",
    }
    step.update(overrides)
    return step


def episode(steps):
    return {
        "goal": "Diagnose the failing build.",
        "steps": steps,
        "outcome": "The visible evidence isolated the defect.",
        "reward": {"success": True},
        "meta": {"factory": "agentic-coding-trajectory-factory"},
    }


class CurateCodingTests(unittest.TestCase):
    def test_migrates_thought_from_visible_reflection(self):
        source = episode([visible_step()])

        curated, manifest = curate_episode(source, source_path="episodes.jsonl")

        self.assertIsNotNone(curated)
        step = curated["steps"][0]
        self.assertFalse(contains_thought_key(curated))
        self.assertEqual(
            step["decision_basis"],
            "Reflection: The failure is deterministic outside UTC. "
            "Inspect both clocks next.",
        )
        self.assertEqual(step["tool_call"], source["steps"][0]["tool_call"])
        self.assertEqual(manifest["step_counts"], {
            "source": 1,
            "retained": 1,
            "migrated": 1,
            "excluded": 0,
        })
        self.assertIn(REASON_THOUGHT_REMOVED, manifest["step_actions"][0]["reason_codes"])
        self.assertIn(
            REASON_BASIS_FROM_REFLECTION,
            manifest["step_actions"][0]["reason_codes"],
        )

    def test_output_does_not_depend_on_thought_content(self):
        first = episode([visible_step(thought="secret A")])
        second = episode([visible_step(thought="entirely different secret B")])

        first_output, _ = curate_episode(first)
        second_output, _ = curate_episode(second)

        self.assertEqual(first_output, second_output)

    def test_visible_evidence_fallback_order(self):
        fixtures = [
            (
                visible_step(plan="Read the failing test first."),
                REASON_BASIS_FROM_PLAN,
                "Plan:",
            ),
            (
                visible_step(reflection="", plan=""),
                REASON_BASIS_FROM_OBSERVATION,
                "Observation:",
            ),
            (
                visible_step(reflection="", observation="", plan=""),
                REASON_BASIS_FROM_TOOL_CALL,
                "Tool call:",
            ),
        ]

        for source, reason, prefix in fixtures:
            with self.subTest(reason=reason):
                curated, manifest = curate_step(source, 1)
                self.assertIsNotNone(curated)
                self.assertTrue(curated["decision_basis"].startswith(prefix))
                self.assertIn(reason, manifest["reason_codes"])

    def test_existing_basis_cannot_override_visible_evidence(self):
        source = visible_step(
            decision_basis="An unsupported assertion that is not evidence-grounded.",
            thought="remove this",
        )

        curated, manifest = curate_step(source, 1)

        self.assertEqual(
            curated["decision_basis"],
            "Reflection: The failure is deterministic outside UTC. "
            "Inspect both clocks next.",
        )
        self.assertFalse(contains_thought_key(curated))
        self.assertEqual(manifest["action"], "migrated")

    def test_existing_basis_alone_is_not_accepted_as_visible_evidence(self):
        source = {
            "n": 1,
            "thought": "remove this",
            "decision_basis": "Unsupported by any visible field.",
        }

        curated, manifest = curate_step(source, 1)

        self.assertIsNone(curated)
        self.assertIn(REASON_NO_VISIBLE_EVIDENCE, manifest["reason_codes"])

    def test_basis_is_bounded_and_normalized(self):
        source = visible_step(
            reflection="  " + "visible evidence " * 40,
            observation="",
        )

        curated, _ = curate_step(source, 1)

        basis = curated["decision_basis"]
        self.assertLessEqual(len(basis), MAX_DECISION_BASIS_CHARS)
        self.assertNotIn("  ", basis)
        self.assertTrue(basis.endswith("…"))

    def test_nested_thought_keys_are_removed_recursively(self):
        source = visible_step(
            tool_call={
                "name": "inspect",
                "args": {"path": "visible.txt", "thought": "nested scratch"},
            },
            reflection="The visible file confirms the mismatch.",
        )

        curated, manifest = curate_step(source, 1)

        self.assertFalse(contains_thought_key(curated))
        self.assertEqual(curated["tool_call"]["args"], {"path": "visible.txt"})
        self.assertEqual(manifest["thought_fields_removed"], 2)

    def test_all_hidden_reasoning_aliases_are_removed_recursively(self):
        source = visible_step(
            chain_of_thought="private",
            tool_call={
                "name": "inspect",
                "args": {
                    "scratch": "private",
                    "innerMonologue": "private",
                    "visible": "keep",
                },
            },
        )

        curated, manifest = curate_step(source, 1)

        self.assertEqual(
            HIDDEN_THOUGHT_KEYS,
            {"thought", "chain_of_thought", "scratch", "inner_monologue"},
        )
        self.assertFalse(contains_thought_key(curated))
        self.assertEqual(curated["tool_call"]["args"], {"visible": "keep"})
        self.assertEqual(manifest["thought_fields_removed"], 4)

    def test_step_without_visible_evidence_is_excluded_with_reason(self):
        source = {"n": 1, "thought": "the only possible source"}

        curated, manifest = curate_step(source, 1)

        self.assertIsNone(curated)
        self.assertEqual(manifest["action"], "excluded")
        self.assertIn(REASON_NO_VISIBLE_EVIDENCE, manifest["reason_codes"])
        self.assertIn(REASON_THOUGHT_REMOVED, manifest["reason_codes"])

    def test_malformed_step_is_excluded_with_reason(self):
        curated, manifest = curate_step("not an object", 3)

        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_STEP_NOT_OBJECT])

    def test_episode_with_no_retainable_steps_is_excluded(self):
        curated, manifest = curate_episode(episode([{"thought": "only"}]))

        self.assertIsNone(curated)
        self.assertEqual(manifest["reason_codes"], [REASON_NO_RETAINABLE_STEPS])
        self.assertEqual(manifest["step_counts"]["excluded"], 1)

    def test_transform_is_output_idempotent(self):
        source = episode([visible_step(), visible_step(n=2)])

        once, _ = curate_episode(source)
        twice, second_manifest = curate_episode(once)

        self.assertEqual(once, twice)
        self.assertEqual(second_manifest["action"], "unchanged")
        self.assertEqual(second_manifest["step_counts"]["migrated"], 0)

    def test_jsonl_manifest_has_exact_line_hashes_and_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "episodes.jsonl"
            first = json.dumps(episode([visible_step()]), ensure_ascii=False)
            second = json.dumps(episode([{"thought": "unsupported"}]))
            source.write_text(first + "\n\n" + second + "\n", encoding="utf-8")

            result = curate_jsonl(source)

        self.assertEqual(result["summary"]["input_records"], 2)
        self.assertEqual(result["summary"]["output_records"], 1)
        self.assertEqual(result["summary"]["source_steps"], 2)
        self.assertEqual(result["summary"]["retained_steps"], 1)
        self.assertEqual(result["summary"]["excluded_steps"], 1)
        self.assertEqual(result["manifest"][0]["source_line"], 1)
        self.assertEqual(result["manifest"][1]["source_line"], 3)
        self.assertEqual(
            result["manifest"][0]["source_hash"],
            hashlib.sha256(first.encode("utf-8")).hexdigest(),
        )
        self.assertIsNotNone(result["manifest"][0]["output_hash"])

    def test_invalid_json_and_utf8_are_excluded_deterministically(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "episodes.jsonl"
            source.write_bytes(b"{not json}\n\xff\n")

            result = curate_jsonl(source)

        self.assertEqual(result["summary"]["input_records"], 2)
        self.assertEqual(result["summary"]["output_records"], 0)
        self.assertEqual(result["manifest"][0]["reason_codes"], [REASON_INVALID_JSON])
        self.assertEqual(result["manifest"][1]["reason_codes"], [REASON_INVALID_UTF8])

    def test_cli_writes_new_files_and_refuses_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "episodes.jsonl"
            output = root / "new" / "coding.jsonl"
            manifest = root / "new" / "manifest.jsonl"
            source.write_text(json.dumps(episode([visible_step()])) + "\n")
            command = [
                sys.executable,
                str(PIPELINES / "curate_coding.py"),
                str(source),
                "--output-jsonl",
                str(output),
                "--manifest-jsonl",
                str(manifest),
            ]

            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(len(output.read_text().splitlines()), 1)
            self.assertEqual(len(manifest.read_text().splitlines()), 1)

    def test_cli_preflights_all_destinations_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "episodes.jsonl"
            output = root / "new" / "coding.jsonl"
            manifest = root / "existing-manifest.jsonl"
            source.write_text(json.dumps(episode([visible_step()])) + "\n")
            manifest.write_text("sentinel\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_coding.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                    "--manifest-jsonl",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(manifest.read_text(), "sentinel\n")

    def test_cli_refuses_any_destination_under_outputs_raw(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "episodes.jsonl"
            output = root / "outputs" / "raw" / "forbidden.jsonl"
            source.write_text(json.dumps(episode([visible_step()])) + "\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_coding.py"),
                    str(source),
                    "--output-jsonl",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_curating_does_not_mutate_input_object(self):
        source = episode([visible_step()])
        original = copy.deepcopy(source)

        curate_episode(source)

        self.assertEqual(source, original)


def curated_result(steps_per_record):
    """Curate temporary JSONL episodes and return the full curate_jsonl result."""
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / "episodes.jsonl"
        with source.open("w", encoding="utf-8") as handle:
            for steps in steps_per_record:
                handle.write(json.dumps(episode(steps), ensure_ascii=False) + "\n")
        return curate_jsonl(source)


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

    def test_retained_step_without_visible_evidence_source_is_a_violation(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["step_actions"][0]["evidence_source"] = None

        violations = verify_curation(result)

        self.assertTrue(
            any("without a visible evidence source" in item for item in violations)
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


class LegacyCodingManifestFixtureTests(unittest.TestCase):
    """Audit fixture for the three legacy 2026-08-17 coding episodes.

    The raw episode payload is immutable, gitignored evidence, so the committed
    fixture is the transform manifest for that run: source and output hashes,
    per-step reason codes, and counts, with no episode text. It pins the
    recorded result — 77 legacy steps, all migrated with reason codes — so the
    acceptance accounting is checkable without republishing raw evidence.
    """

    FIXTURE = (
        ROOT
        / "tests"
        / "fixtures"
        / "coding-observability"
        / "legacy-2026-08-17-manifest.jsonl"
    )
    LEGACY_SOURCE_STEPS = 77
    RECORD_KEYS = {
        "source_path",
        "source_line",
        "source_hash",
        "transform",
        "transform_version",
        "action",
        "reason_codes",
        "output_id",
        "output_hash",
        "thought_fields_removed",
        "step_counts",
        "step_actions",
    }
    STEP_KEYS = {
        "source_step_index",
        "source_step_number",
        "action",
        "reason_codes",
        "evidence_source",
        "thought_fields_removed",
        "output_step_index",
    }

    def setUp(self):
        self.entries = [
            json.loads(line)
            for line in self.FIXTURE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_fixture_passes_the_lane_acceptance_check(self):
        violations = verify_manifest(
            self.entries, expected_source_steps=self.LEGACY_SOURCE_STEPS
        )

        self.assertEqual(violations, [])

    def test_every_legacy_step_is_migrated_or_excluded_with_reason_codes(self):
        actions = [item for entry in self.entries for item in entry["step_actions"]]

        self.assertEqual(len(self.entries), 3)
        self.assertEqual(len(actions), self.LEGACY_SOURCE_STEPS)
        self.assertTrue(all(item["reason_codes"] for item in actions))
        self.assertEqual(
            {item["action"] for item in actions},
            {"migrated"},
        )
        self.assertEqual(
            {item["evidence_source"] for item in actions},
            {"reflection"},
        )
        self.assertEqual(
            sum(item["thought_fields_removed"] for item in actions),
            self.LEGACY_SOURCE_STEPS,
        )
        for item in actions:
            self.assertIn(REASON_THOUGHT_REMOVED, item["reason_codes"])
            self.assertIn(REASON_BASIS_FROM_REFLECTION, item["reason_codes"])

    def test_fixture_records_provenance_without_raw_episode_payload(self):
        for entry in self.entries:
            self.assertEqual(set(entry), self.RECORD_KEYS)
            self.assertEqual(entry["transform"], "coding_observability")
            self.assertEqual(entry["action"], "modified")
            self.assertTrue(entry["source_hash"])
            self.assertTrue(entry["output_hash"])
            self.assertEqual(
                entry["source_path"],
                "outputs/raw/2026-08-17/agentic-coding-trajectory-factory/episodes.jsonl",
            )
            for item in entry["step_actions"]:
                self.assertEqual(set(item), self.STEP_KEYS)

    def test_fixture_check_is_not_vacuous(self):
        damaged = copy.deepcopy(self.entries)
        damaged[0]["step_actions"][0]["reason_codes"] = []

        violations = verify_manifest(
            damaged, expected_source_steps=self.LEGACY_SOURCE_STEPS
        )

        self.assertTrue(any("no reason codes recorded" in item for item in violations))


class CurateCodingVerifyCliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(PIPELINES / "curate_coding.py"), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_verify_gate_reports_the_expected_step_total(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "episodes.jsonl"
            source.write_text(
                json.dumps(episode([visible_step(), visible_step(n=2)])) + "\n",
                encoding="utf-8",
            )

            result = self.run_cli(str(source), "--verify", "--expect-source-steps", "2")

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(
                summary["verification"],
                {"expected_source_steps": 2, "violations": []},
            )

    def test_verify_gate_fails_and_writes_nothing_on_a_step_count_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "episodes.jsonl"
            output = root / "new" / "coding.jsonl"
            manifest = root / "new" / "manifest.jsonl"
            source.write_text(
                json.dumps(episode([visible_step()])) + "\n", encoding="utf-8"
            )

            result = self.run_cli(
                str(source),
                "--output-jsonl",
                str(output),
                "--manifest-jsonl",
                str(manifest),
                "--expect-source-steps",
                "77",
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("VIOLATION: expected 77 source steps", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(manifest.exists())

    def test_verify_gate_rejects_a_negative_expected_step_total(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "episodes.jsonl"
            source.write_text(
                json.dumps(episode([visible_step()])) + "\n", encoding="utf-8"
            )

            result = self.run_cli(str(source), "--expect-source-steps", "-1")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not be negative", result.stderr)

    def test_default_run_stays_silent_about_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "episodes.jsonl"
            source.write_text(
                json.dumps(episode([visible_step()])) + "\n", encoding="utf-8"
            )

            result = self.run_cli(str(source))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("verification", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
