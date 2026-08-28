import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from coding_curation_helpers import (  # noqa: E402
    PIPELINES,
    ROOT,
    curated_result,
    episode,
    visible_step,
)
from curate_coding import (  # noqa: E402
    REASON_BASIS_FROM_REFLECTION,
    REASON_HIDDEN_REASONING_REMOVED,
    TRANSFORM_VERSION,
    curate_episode,
    hash_value,
    verify_curation,
    verify_manifest,
)

class VerifyCurationShapeTests(unittest.TestCase):
    def test_manifest_collection_and_entry_shapes_are_reported(self):
        self.assertEqual(
            verify_manifest({"manifest": "not a list"}),
            ["manifest collection is not a list"],
        )

        violations = verify_manifest([None])

        self.assertEqual(violations, ["manifest entry None is not an object"])

    def test_manifest_metadata_shape_violations_do_not_raise(self):
        result = curated_result([[visible_step()]])
        manifest = result["manifest"][0]
        manifest.update(
            {
                "source_path": "",
                "source_line": 0,
                "transform_version": "unexpected",
                "action": "unexpected",
                "reason_codes": "not a list",
                "thought_fields_removed": -1,
                "step_counts": None,
            }
        )

        violations = verify_manifest([manifest])

        for expected in (
            "manifest records no source path",
            "source line must be a positive integer",
            "manifest transform version",
            "reason codes are not a list",
            "unknown record action",
            "thought_fields_removed must be a non-negative integer",
            "manifest records no step accounting",
        ):
            self.assertTrue(any(expected in item for item in violations), violations)

    def test_excluded_record_cannot_keep_output_identity(self):
        _, manifest = curate_episode(episode([]))
        manifest["output_hash"] = "0" * 64
        manifest["output_id"] = "forbidden-output-id"

        violations = verify_manifest([manifest])

        self.assertTrue(
            any("excluded record still records an output hash" in item for item in violations)
        )
        self.assertTrue(
            any("excluded record still records an output ID" in item for item in violations)
        )

    def test_retained_record_requires_a_valid_output_hash(self):
        result = curated_result([[visible_step()]])
        result["manifest"][0]["output_hash"] = "not-a-hash"

        violations = verify_manifest(result["manifest"])

        self.assertTrue(
            any("retained record records no valid output hash" in item for item in violations)
        )

    def test_step_action_shape_violations_do_not_raise(self):
        malformed = curated_result([[visible_step()]])["manifest"][0]
        malformed_action = malformed["step_actions"][0]
        malformed_action.update(
            {
                "source_step_index": 0,
                "action": "unexpected",
                "reason_codes": "not a list",
                "thought_fields_removed": -1,
            }
        )

        excluded = curated_result([[{"n": 1, "thought": "only"}]])["manifest"][0]
        excluded["step_actions"][0]["output_step_index"] = 1

        retained = curated_result([[visible_step()]])["manifest"][0]
        retained["step_actions"][0]["output_step_index"] = 0
        retained["step_counts"]["source"] = 2

        violations = verify_manifest([malformed, excluded, retained])

        for expected in (
            "reason codes are not a list",
            "source step index must be a positive integer",
            "thought_fields_removed must be a non-negative integer",
            "unknown step action",
            "excluded step keeps an output index",
            "retained output step index must be a positive integer",
            "2 source steps but 1 step actions",
        ):
            self.assertTrue(any(expected in item for item in violations), violations)

    def test_curation_top_level_shapes_are_reported(self):
        self.assertEqual(
            verify_curation(None),
            ["curation result is not an object"],
        )

        invalid_records = curated_result([[visible_step()]])
        invalid_records["records"] = {"not": "a list"}
        record_violations = verify_curation(invalid_records)

        invalid_summary = curated_result([[visible_step()]])
        invalid_summary["summary"] = []
        summary_violations = verify_curation(invalid_summary)

        self.assertIn("curated records are not a list", record_violations)
        self.assertIn("curation summary is not an object", summary_violations)

    def test_curated_record_structure_guards_are_reported(self):
        no_steps = curated_result([[visible_step()]])
        no_steps["records"][0]["steps"] = []
        no_steps["manifest"][0]["output_hash"] = hash_value(no_steps["records"][0])

        non_object_step = curated_result([[visible_step()]])
        non_object_step["records"][0]["steps"][0] = "not an object"
        non_object_step["manifest"][0]["output_hash"] = hash_value(
            non_object_step["records"][0]
        )

        ungrounded = curated_result([[visible_step()]])
        step = ungrounded["records"][0]["steps"][0]
        for field in ("plan", "reflection", "observation", "tool_call"):
            step.pop(field, None)
        ungrounded["manifest"][0]["output_hash"] = hash_value(
            ungrounded["records"][0]
        )

        cases = (
            (no_steps, "curated record has no retained steps"),
            (non_object_step, "curated step is not an object"),
            (ungrounded, "decision_basis has no visible evidence to ground it"),
        )
        for result, expected in cases:
            with self.subTest(expected=expected):
                violations = verify_curation(result)
                self.assertTrue(any(expected in item for item in violations), violations)

    def test_curation_record_binding_guards_do_not_raise(self):
        non_serializable = curated_result([[visible_step()]])
        non_serializable["records"][0]["opaque"] = object()

        wrong_id = curated_result([[visible_step()]])
        wrong_id["manifest"][0]["output_id"] = "wrong-output-id"

        malformed_action = curated_result([[visible_step()]])
        malformed_action["manifest"][0]["step_actions"][0] = None

        out_of_range_action = curated_result([[visible_step()]])
        out_of_range_action["manifest"][0]["step_actions"][0][
            "output_step_index"
        ] = 2

        cases = (
            (non_serializable, "curated record is not JSON-serializable"),
            (wrong_id, "output ID does not match its manifest entry"),
            (malformed_action, "step action None is not an object"),
            (out_of_range_action, "retained output step indexes"),
        )
        for result, expected in cases:
            with self.subTest(expected=expected):
                violations = verify_curation(result)
                self.assertTrue(any(expected in item for item in violations), violations)

class LegacyCodingManifestFixtureTests(unittest.TestCase):
    """Audit fixture for the three legacy 2026-08-17 coding episodes.

    The raw episode payload is immutable, gitignored evidence, so the committed
    fixture is the transform manifest for that run: source and output hashes,
    per-step reason codes, and counts, with no episode text. It pins the
    recorded result — 77 legacy steps, all migrated with reason codes — so the
    acceptance accounting is checkable without republishing raw evidence.

    After a TRANSFORM_VERSION bump, regenerate from the gitignored raw run into
    a new path (the CLI refuses to clobber) and copy the payload-free manifest
    over this fixture::

        python3 pipelines/curate_coding.py \\
          outputs/raw/2026-08-17/agentic-coding-trajectory-factory/episodes.jsonl \\
          --verify --expect-source-steps 77 \\
          --manifest-jsonl /tmp/legacy-2026-08-17-manifest.jsonl
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
        "hidden_reasoning_fields_removed",
        "steps_path",
        "step_counts",
        "step_actions",
    }
    STEP_KEYS = {
        "source_step_index",
        "source_step_number",
        "action",
        "reason_codes",
        "evidence_source",
        "hidden_reasoning_fields_removed",
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
            sum(item["hidden_reasoning_fields_removed"] for item in actions),
            self.LEGACY_SOURCE_STEPS,
        )
        for item in actions:
            self.assertIn(REASON_HIDDEN_REASONING_REMOVED, item["reason_codes"])
            self.assertIn(REASON_BASIS_FROM_REFLECTION, item["reason_codes"])

    def test_fixture_records_provenance_without_raw_episode_payload(self):
        for entry in self.entries:
            self.assertEqual(set(entry), self.RECORD_KEYS)
            self.assertEqual(entry["transform"], "coding_observability")
            self.assertIn(str(entry["transform_version"]), {"2", "3", TRANSFORM_VERSION})
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

    def test_verify_gate_writes_output_after_a_clean_run(self):
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
                "--verify",
                "--expect-source-steps",
                "1",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(output.read_text(encoding="utf-8").splitlines()), 1)
            self.assertEqual(len(manifest.read_text(encoding="utf-8").splitlines()), 1)

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
