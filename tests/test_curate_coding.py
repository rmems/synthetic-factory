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


if __name__ == "__main__":
    unittest.main()
