#!/usr/bin/env python3
"""Whole-run readiness, determinism, immutability, and CLI contracts."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
from compose_curated_test_support import build_source_run  # noqa: E402


class ComposeCuratedRunContracts(unittest.TestCase):
    """Exercise corpus-level output and operator-facing contracts."""

    def test_empty_composition_is_never_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text(
                json.dumps({"unknown": "shape"}) + "\n", encoding="utf-8"
            )
            summary = compose_curated.compose_run(root / "run", root / "curated")

            self.assertEqual(summary["counts"]["retained"], 0)
            self.assertFalse(summary["audit"]["training_ready"])
            self.assertEqual(
                summary["audit"]["blockers"], [compose_curated.REASON_EMPTY_CORPUS]
            )

    def test_composition_is_deterministic_and_leaves_the_source_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            before = {
                path: path.read_bytes() for path in sorted(source.rglob("*.jsonl"))
            }

            first = compose_curated.compose_run(source, root / "curated-a")
            second = compose_curated.compose_run(source, root / "curated-b")

            self.assertEqual(first["manifest"]["sha256"], second["manifest"]["sha256"])
            self.assertEqual(
                first["reward_sidecars"]["sha256"], second["reward_sidecars"]["sha256"]
            )
            self.assertEqual(
                [item["sha256"] for item in first["outputs"]],
                [item["sha256"] for item in second["outputs"]],
            )
            self.assertEqual(first["counts"], second["counts"])
            self.assertEqual(
                {path: path.read_bytes() for path in sorted(source.rglob("*.jsonl"))},
                before,
            )

    def test_cli_reports_strict_blockers_and_refuses_existing_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = compose_curated.main(
                    ["--strict", str(source), str(root / "curated")]
                )
            self.assertEqual(status, 0)
            self.assertTrue(json.loads(stdout.getvalue())["audit"]["training_ready"])

            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = compose_curated.main([str(source), str(root / "curated")])
            self.assertEqual(status, 2)
            self.assertIn("refusing to overwrite", stderr.getvalue())

            blocked = root / "blocked-run" / "thalamic-trajectory-factory"
            blocked.mkdir(parents=True)
            (blocked / "batch-r01.jsonl").write_text(
                json.dumps({"unknown": "shape"}) + "\n", encoding="utf-8"
            )
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = compose_curated.main(
                    ["--strict", str(root / "blocked-run"), str(root / "curated-blocked")]
                )
            self.assertEqual(status, 1)
            self.assertIn(compose_curated.REASON_EMPTY_CORPUS, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
