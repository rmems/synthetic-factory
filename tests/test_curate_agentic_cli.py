#!/usr/bin/env python3
"""CLI and cleaned-tree writing rules for agentic curation."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import curate_agentic  # noqa: E402
import curate_agentic_output  # noqa: E402
from curate_agentic import (  # noqa: E402
    contains_hidden_thought_key,
    curate_source,
)
from curate_agentic_fixtures import episode_fixture, step  # noqa: E402
import training_audit  # noqa: E402


def _run_cli(*arguments):
    """Run the agentic curation CLI over ``arguments`` and return the result."""
    return subprocess.run(
        [sys.executable, str(PIPELINES / "curate_agentic.py"), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_factory_batch(factory, records):
    """Write ``records`` as the round-1 batch of a fresh factory directory."""
    factory.mkdir(parents=True)
    (factory / "batch-r01.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records)
    )


def _write_two_factory_source(source_dir):
    """A two-factory source tree: a thought-bearing mill beside a clean one."""
    _write_factory_batch(
        source_dir / "cache-stampede-factory",
        [
            episode_fixture(
                f"cst-r0{index}-singleflight",
                goal="Fix the singleflight TTL stampede",
                steps=[step(1, thought="no")],
                meta={
                    "factory": "cache-stampede-factory",
                    "round": index,
                    "generator": "grok-4.6",
                },
            )
            for index in (1, 2)
        ],
    )
    _write_factory_batch(
        source_dir / "graphql-nplusone-factory",
        [
            episode_fixture(
                f"gql-r0{index}-projection",
                goal="Fix the PostGraphile analyzer projection",
                meta={
                    "factory": "graphql-nplusone-factory",
                    "round": index,
                    "generator": "grok-4.6",
                },
            )
            for index in (1, 2)
        ],
    )


class CurateAgenticCli(unittest.TestCase):
    """The CLI and the cleaned-tree writer must refuse unsafe destinations."""

    def test_cli_bounds_transaction_errors_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "agentic-factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text("{broken\n")
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(episode_fixture("marker-error")) + "\n"
            )

            result = _run_cli(str(factory))

        self.assertEqual(result.returncode, 1)
        self.assertIn("agentic curation failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "episode.jsonl"
            source.write_text(json.dumps(episode_fixture()) + "\n")
            before = list(root.rglob("*"))

            result = _run_cli("--dry-run", str(source))

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["dry_run"])
            self.assertEqual(report["output_records"], 1)
            self.assertFalse(report["mill_family"]["context_complete"])
            self.assertFalse(report["mill_family"]["quarantine_applied"])
            self.assertEqual(list(root.rglob("*")), before)

    def test_cleaned_output_refuses_single_file_or_factory_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = root / "cache-stampede-factory"
            factory.mkdir()
            source = factory / "batch-r01.jsonl"
            source.write_text(json.dumps(episode_fixture()) + "\n")

            for partial_source in (source, factory):
                with self.subTest(source=partial_source):
                    run = curate_source(partial_source)
                    self.assertFalse(
                        run["summary"]["mill_family"]["context_complete"]
                    )
                    with self.assertRaisesRegex(ValueError, "multi-factory"):
                        curate_agentic.write_cleaned_tree(
                            run, root / f"out-{partial_source.name}"
                        )

    def _assert_cleaned_tree(self, dest):
        """The written tree is thought-free and carries one JSON manifest."""
        cleaned = dest / "cache-stampede-factory" / "batch-r01.jsonl"
        self.assertTrue(cleaned.is_file())
        emitted = json.loads(cleaned.read_text().splitlines()[0])
        self.assertFalse(contains_hidden_thought_key(emitted))
        manifest = dest / "CURATE-MANIFEST.json"
        self.assertTrue(manifest.is_file())
        self.assertIsInstance(json.loads(manifest.read_text()), list)
        self.assertFalse((dest / "CURATE-MANIFEST.jsonl").exists())
        audit = training_audit.audit_run(dest)
        self.assertEqual(audit["record_invariants"]["errors"], 0)

    def test_cli_out_writes_new_tree_and_refuses_raw_and_clobber(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_dir = root / "src"
            _write_two_factory_source(source_dir)
            dest = root / "cleaned"

            first = _run_cli(str(source_dir), "--out", str(dest))
            second = _run_cli(str(source_dir), "--out", str(dest))

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self._assert_cleaned_tree(dest)
            self.assertFalse(json.loads(first.stdout)["dry_run"])

            raw_dest = root / "outputs" / "raw" / "forbidden"
            raw = _run_cli(str(source_dir), "--out", str(raw_dest))
            self.assertNotEqual(raw.returncode, 0)
            self.assertFalse(raw_dest.exists())

    def test_cli_refuses_dry_run_with_out(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "e.jsonl"
            source.write_text("{}\n")
            result = _run_cli(
                "--dry-run",
                "--out",
                str(Path(temporary) / "out"),
                str(source),
            )
        self.assertEqual(result.returncode, 2)

    def test_write_cleanup_preserves_the_primary_failure(self):
        run = {
            "records_by_rel": {"nested/batch.jsonl": [episode_fixture()]},
            "decisions": [],
            "summary": {"mill_family": {"quarantine_applied": True}},
        }
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "cleaned"
            # The record writer lives in curate_agentic_output, which is what
            # write_cleaned_tree actually calls; patching the re-export on
            # curate_agentic would not intercept it.
            with mock.patch.object(
                curate_agentic_output,
                "write_new_jsonl",
                side_effect=RuntimeError("writer failed"),
            ), mock.patch.object(Path, "rmdir", side_effect=OSError("cleanup failed")):
                with self.assertRaisesRegex(RuntimeError, "writer failed"):
                    curate_agentic.write_cleaned_tree(run, out)

    def test_write_requires_a_positive_mill_quarantine_gate(self):
        malformed_summaries = {
            "missing": object(),
            "null": None,
            "not-a-mapping": [],
            "missing-mill-family": {},
            "null-mill-family": {"mill_family": None},
            "missing-decision": {"mill_family": {}},
            "false-decision": {
                "mill_family": {"quarantine_applied": False}
            },
            "truthy-non-boolean": {
                "mill_family": {"quarantine_applied": "true"}
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, (name, summary) in enumerate(
                malformed_summaries.items()
            ):
                with self.subTest(name=name):
                    run = {"records_by_rel": {}, "decisions": []}
                    if name != "missing":
                        run["summary"] = summary
                    out = root / f"cleaned-{index}"
                    with self.assertRaisesRegex(ValueError, "multi-factory"):
                        curate_agentic.write_cleaned_tree(run, out)
                    self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
