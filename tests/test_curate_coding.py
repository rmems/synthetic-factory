import contextlib
import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_coding  # noqa: E402
import curate_gate  # noqa: E402
from curate_coding import (  # noqa: E402
    MAX_DECISION_BASIS_CHARS,
    REASON_BASIS_CONCISED,
    REASON_BASIS_FROM_OBSERVATION,
    REASON_BASIS_FROM_PLAN,
    REASON_BASIS_FROM_REFLECTION,
    REASON_BASIS_FROM_TOOL_CALL,
    REASON_HIDDEN_REASONING_REMOVED,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_NO_RETAINABLE_STEPS,
    REASON_NO_VISIBLE_EVIDENCE,
    REASON_STEP_NOT_OBJECT,
    REASON_STEPS_NOT_ARRAY,
    REASON_THOUGHT_REMOVED,
    REASON_WRAP_RECORD,
    TRANSFORM_VERSION,
    contains_hidden_reasoning_key,
    contains_thought_key,
    curate_episode,
    curate_jsonl,
    curate_step,
    hash_value,
    is_hidden_reasoning_key,
    verify_curation,
    verify_manifest,
)
from validate_run import HIDDEN_THOUGHT_KEYS  # noqa: E402


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


def wrap_record(steps):
    """A Thalamic gate record whose executed_action embeds a coding episode."""
    return {
        "state": {"episode_id": "actf-r02-004", "sim_or_real": "designed"},
        "proposed_action": {
            "action_type": "delegate_to_coding_agent",
            "policy_confidence": 0.71,
            "internal_reasoning": "private gate rationale that must not publish",
            "internal_reasoning_verbatim": "verbatim private gate rationale",
        },
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {
            "goal": "Diagnose the failing build.",
            "steps": steps,
            "outcome": "The visible evidence isolated the defect.",
            "reward": {"success": True},
        },
        "future_outcome": {"success": True},
        "reward_components": {"task_progress": 0.5, "safety": 0.5, "total": 1.0},
        "meta": {"factory": "agentic-coding-trajectory-factory", "round": 2},
    }


class CurateCodingTests(unittest.TestCase):
    def test_migrates_thought_from_visible_reflection(self):
        source = episode([visible_step()])

        curated, manifest = curate_episode(source, source_path="episodes.jsonl")

        self.assertIsNotNone(curated)
        step = curated["steps"][0]
        self.assertFalse(contains_hidden_reasoning_key(curated))
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
        self.assertIn(REASON_HIDDEN_REASONING_REMOVED, manifest["step_actions"][0]["reason_codes"])
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
        self.assertFalse(contains_hidden_reasoning_key(curated))
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

        self.assertFalse(contains_hidden_reasoning_key(curated))
        self.assertEqual(curated["tool_call"]["args"], {"path": "visible.txt"})
        self.assertEqual(manifest["hidden_reasoning_fields_removed"], 2)

    def test_step_without_visible_evidence_is_excluded_with_reason(self):
        source = {"n": 1, "thought": "the only possible source"}

        curated, manifest = curate_step(source, 1)

        self.assertIsNone(curated)
        self.assertEqual(manifest["action"], "excluded")
        self.assertIn(REASON_NO_VISIBLE_EVIDENCE, manifest["reason_codes"])
        self.assertIn(REASON_HIDDEN_REASONING_REMOVED, manifest["reason_codes"])

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

    def test_source_hash_strips_only_the_cr_paired_with_literal_lf(self):
        record = episode([visible_step()])
        payload = json.dumps(record, ensure_ascii=False).encode("utf-8")
        hashes = {}
        with tempfile.TemporaryDirectory() as temporary:
            for label, source_bytes in {
                "no-terminator": payload,
                "lf": payload + b"\n",
                "crlf": payload + b"\r\n",
                "bare-final-cr": payload + b"\r",
                "payload-cr-before-crlf": payload + b"\r\r\n",
            }.items():
                source = Path(temporary) / f"{label}.jsonl"
                source.write_bytes(source_bytes)

                result = curate_jsonl(source)

                self.assertEqual(len(result["manifest"]), 1, label)
                hashes[label] = result["manifest"][0]["source_hash"]

        payload_hash = hashlib.sha256(payload).hexdigest()
        payload_cr_hash = hashlib.sha256(payload + b"\r").hexdigest()
        self.assertEqual(hashes["no-terminator"], payload_hash)
        self.assertEqual(hashes["lf"], payload_hash)
        self.assertEqual(hashes["crlf"], payload_hash)
        self.assertEqual(hashes["bare-final-cr"], payload_cr_hash)
        self.assertEqual(
            hashes["payload-cr-before-crlf"],
            payload_cr_hash,
        )
        self.assertNotEqual(payload_hash, payload_cr_hash)

    def test_directory_writer_preserves_paths_and_emits_one_gate_manifest(self):
        first_record = episode([visible_step(n=1)])
        first_record["id"] = "coding-alpha"
        second_record = episode([visible_step(n=2, reflection="Visible second file.")])
        second_record["id"] = "coding-zeta"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source-run"
            alpha = Path("alpha/nested/episodes.jsonl")
            zeta = Path("zeta/batch-r02.jsonl")
            (source / zeta).parent.mkdir(parents=True)
            (source / zeta).write_text(json.dumps(second_record) + "\n", encoding="utf-8")
            (source / alpha).parent.mkdir(parents=True)
            (source / alpha).write_text(
                "\n" + json.dumps(first_record) + "\n",
                encoding="utf-8",
            )
            output = root / "lane-coding"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(PIPELINES / "curate_coding.py"),
                    str(source),
                    "--output-dir",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            manifest_path = output / curate_coding.RUN_MANIFEST_FILENAME
            manifest = [
                json.loads(line)
                for line in manifest_path.read_text(encoding="utf-8").split("\n")
                if line
            ]

            self.assertEqual(summary["input_files"], 2)
            self.assertEqual(summary["input_records"], 2)
            self.assertEqual(summary["output_records"], 2)
            self.assertEqual(summary["hidden_reasoning_fields_removed"], 2)
            self.assertEqual(summary["wrap_records"], 0)
            self.assertEqual(
                [(item["source_path"], item["source_line"]) for item in manifest],
                [(alpha.as_posix(), 2), (zeta.as_posix(), 1)],
            )
            self.assertTrue((output / alpha).is_file())
            self.assertTrue((output / zeta).is_file())
            self.assertEqual(
                sorted(path.relative_to(output).as_posix() for path in output.rglob("*.jsonl")),
                [alpha.as_posix(), curate_coding.RUN_MANIFEST_FILENAME, zeta.as_posix()],
            )

            lane = {
                "order": 5,
                "bead": "sf-c5l.5",
                "transform": curate_coding.TRANSFORM_NAME,
                "version": curate_coding.TRANSFORM_VERSION,
                "outputs_dir": output,
                "manifest_path": manifest_path,
                "manifest_format": "jsonl",
                "artifacts": [],
            }
            prepared = curate_gate._prepare_lane(  # noqa: SLF001
                lane,
                curate_gate._load_source_records(source),  # noqa: SLF001
            )
            self.assertEqual(len(prepared["entries"]), 2)
            self.assertEqual(
                [record["relative_path"] for record in prepared["records"]],
                [alpha.as_posix(), zeta.as_posix()],
            )

    def test_directory_writer_refuses_clobber_and_preserves_existing_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source-run"
            source.mkdir()
            (source / "episodes.jsonl").write_text(
                json.dumps(episode([visible_step()])) + "\n",
                encoding="utf-8",
            )
            output = root / "lane-coding"
            output.mkdir()
            marker = output / "owned-by-another-run"
            marker.write_text("sentinel", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "refusing to replace"):
                curate_coding.curate_run(source, output)

            self.assertEqual(marker.read_text(encoding="utf-8"), "sentinel")

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

    def _two_file_source(self, root: Path) -> tuple[Path, Path]:
        source = root / "source-run"
        first = episode([visible_step(n=1)])
        first["id"] = "coding-alpha"
        second = episode([visible_step(n=2, reflection="Visible second file.")])
        second["id"] = "coding-zeta"
        alpha = source / "alpha/nested/episodes.jsonl"
        zeta = source / "zeta/batch-r02.jsonl"
        alpha.parent.mkdir(parents=True)
        zeta.parent.mkdir(parents=True)
        alpha.write_text("\n" + json.dumps(first) + "\n", encoding="utf-8")
        zeta.write_text(json.dumps(second) + "\n", encoding="utf-8")
        return source, root / "lane-coding"

    def test_directory_writer_in_process_preserves_tree_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, output = self._two_file_source(Path(temporary))
            summary = curate_coding.curate_run(source, output)
            self.assertEqual(summary["input_files"], 2)
            self.assertEqual(summary["output_records"], 2)
            self.assertTrue((output / curate_coding.RUN_MANIFEST_FILENAME).is_file())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = curate_coding.main([str(source), "--output-dir", str(output) + "-cli"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["input_files"], 2)

            real_write = curate_coding._write_new_jsonl
            calls = {"n": 0}

            def boom(path, values):
                calls["n"] += 1
                if calls["n"] >= 2:
                    raise RuntimeError("inject-write-failure")
                return real_write(path, values)

            rolled = Path(temporary) / "lane-coding-rollback"
            with mock.patch.object(curate_coding, "_write_new_jsonl", boom):
                with self.assertRaisesRegex(RuntimeError, "inject-write-failure"):
                    curate_coding.curate_run(source, rolled)
            self.assertFalse(rolled.exists())

    def test_directory_writer_rejects_symlink_empty_raw_and_nested_dest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, output = self._two_file_source(root)
            linked = root / "linked-source"
            linked.symlink_to(source)
            with self.assertRaisesRegex(ValueError, "must not be a symlink"):
                curate_coding.curate_run(linked, root / "out-link")

            nested_link = source / "zeta" / "alias"
            nested_link.symlink_to(source / "alpha")
            with self.assertRaisesRegex(ValueError, "symlinked path"):
                curate_coding.curate_run(source, root / "out-nested")
            nested_link.unlink()

            empty = root / "empty-run"
            empty.mkdir()
            with self.assertRaisesRegex(ValueError, "holds no JSONL"):
                curate_coding.curate_run(empty, root / "out-empty")

            missing = root / "missing-run"
            with self.assertRaisesRegex(ValueError, "not a directory"):
                curate_coding.curate_run(missing, root / "out-missing")

            reserved = source / curate_coding.RUN_MANIFEST_FILENAME
            reserved.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "aggregate manifest"):
                curate_coding.curate_run(source, root / "out-reserved")
            reserved.unlink()

            with self.assertRaisesRegex(ValueError, "outside the source run"):
                curate_coding.curate_run(source, source / "inside")

            raw = root / "outputs" / "raw" / "lane"
            with self.assertRaisesRegex(ValueError, "immutable raw"):
                curate_coding.curate_run(source, raw)

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
                curate_coding.main(
                    [str(source), "--output-dir", str(output), "--output-jsonl", str(root / "x.jsonl")]
                )
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                curate_coding.main(
                    [str(source / "alpha/nested/episodes.jsonl"), "--output-dir", str(root / "d")]
                )
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                curate_coding.main([str(source)])
            file_source = source / "alpha/nested/episodes.jsonl"
            file_out = root / "one.jsonl"
            file_manifest = root / "one.manifest.jsonl"
            with contextlib.redirect_stdout(io.StringIO()):
                code = curate_coding.main(
                    [
                        str(file_source),
                        "--output-jsonl",
                        str(file_out),
                        "--manifest-jsonl",
                        str(file_manifest),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertTrue(file_out.is_file())
            self.assertTrue(file_manifest.is_file())

            file_a = root / "a.jsonl"
            file_b = root / "b.jsonl"
            with self.assertRaisesRegex(ValueError, "distinct"):
                curate_coding._preflight_destinations([file_a, file_a])
            self.assertFalse(
                curate_coding._unlink_created_file(root / "absent.jsonl", (0, 0))
            )
            self.assertFalse(
                curate_coding._rmdir_created_directory(root / "absent-dir", (0, 0))
            )


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

    def test_undelimited_internal_reasoning_suffixes_are_stripped(self):
        source = episode(
            [
                visible_step(
                    internal_reasoning2="private numbered trace",
                    internal_reasoningverbatim="private verbatim trace",
                )
            ]
        )

        curated, manifest = curate_episode(source)

        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_reasoning_key(curated))
        self.assertNotIn("internal_reasoning2", curated["steps"][0])
        self.assertNotIn("internal_reasoningverbatim", curated["steps"][0])
        self.assertEqual(
            manifest["step_actions"][0]["hidden_reasoning_fields_removed"], 3
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

    def test_internal_reasoning_is_stripped_from_a_plain_episode(self):
        source = episode(
            [
                visible_step(
                    internal_reasoning="private step rationale",
                    internal_reasoning_verbatim="verbatim private step rationale",
                )
            ]
        )

        curated, manifest = curate_episode(source)

        self.assertIsNotNone(curated)
        self.assertFalse(contains_hidden_reasoning_key(curated))
        self.assertNotIn("internal_reasoning", curated["steps"][0])
        self.assertNotIn("internal_reasoning_verbatim", curated["steps"][0])
        self.assertEqual(
            manifest["step_actions"][0]["hidden_reasoning_fields_removed"], 3
        )

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

        curated, manifest = curate_episode(source)

        self.assertEqual(manifest["action"], "modified")
        self.assertIn(REASON_WRAP_RECORD, manifest["reason_codes"])
        self.assertIn(REASON_HIDDEN_REASONING_REMOVED, manifest["reason_codes"])
        violations = verify_manifest([manifest])
        self.assertEqual(violations, [])

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
        for record in result["records"]:
            self.assertFalse(contains_hidden_reasoning_key(record))

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
