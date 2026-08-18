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


if __name__ == "__main__":
    unittest.main()
