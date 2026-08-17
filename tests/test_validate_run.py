#!/usr/bin/env python3
"""validate_run.py must not write manifest.json unless --write is passed."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATE = REPO / "pipelines" / "validate_run.py"

# Minimal record that passes the thalamic shape check (required keys + decision).
TINY_THALAMIC = {
    "state": {"episode_id": "tiny-001"},
    "proposed_action": {"action_type": "noop"},
    "safety_decision": {"decision": "ACCEPT", "rationale": "test fixture"},
    "executed_action": {"action_type": "noop"},
    "future_outcome": {"success": "full"},
    "reward_components": {"total": 0.0},
}

EXPECTED_TOTALS = {
    "files": 1,
    "records": 1,
    "by_kind": {"thalamic": 1},
    "error_count": 0,
}


def _tiny_run_dir(tmp: Path) -> Path:
    run_dir = tmp / "run"
    run_dir.mkdir()
    (run_dir / "tiny.jsonl").write_text(json.dumps(TINY_THALAMIC) + "\n")
    return run_dir


def _invoke(*args):
    return subprocess.run(
        [sys.executable, str(VALIDATE), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class ValidateRunWriteFlag(unittest.TestCase):
    def test_default_does_not_create_manifest(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), EXPECTED_TOTALS)
            self.assertFalse(
                (run_dir / "manifest.json").exists(),
                "default invoke must not create manifest.json",
            )

    def test_write_creates_manifest_with_matching_totals(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            result = _invoke("--write", str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            stdout_totals = json.loads(result.stdout)
            self.assertEqual(stdout_totals, EXPECTED_TOTALS)
            manifest_path = run_dir / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["totals"], stdout_totals)

    def test_default_does_not_overwrite_existing_manifest(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            sentinel = {"sentinel": True, "files": []}
            manifest_path = run_dir / "manifest.json"
            manifest_path.write_text(json.dumps(sentinel) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(manifest_path.read_text()), sentinel)

    def test_non_object_line_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "junk.jsonl").write_text("null\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("must be a JSON object", result.stderr)


if __name__ == "__main__":
    unittest.main()
