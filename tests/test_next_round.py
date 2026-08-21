#!/usr/bin/env python3
"""next_round.py allocates max(existing)+1 and refuses an occupied batch-rNN."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NEXT_ROUND = REPO / "pipelines" / "next_round.py"
ROUNDS_FIXTURE = REPO / "tests" / "fixtures" / "rounds"


def _invoke(*args):
    return subprocess.run(
        [sys.executable, str(NEXT_ROUND), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _index_entries(payload):
    """Normalize NEXT_ROUND.json to {factory_name: entry}."""
    if not isinstance(payload, dict):
        raise AssertionError(f"index must be an object, got {type(payload)}")
    fac = payload.get("factories", payload)
    if isinstance(fac, list):
        return {entry["factory"]: entry for entry in fac}
    if isinstance(fac, dict):
        out = {}
        for key, value in fac.items():
            if isinstance(value, dict) and "next_round" in value:
                out[value.get("factory", key)] = value
        if out:
            return out
    raise AssertionError(f"unrecognized NEXT_ROUND.json shape: {payload!r}")


def _episode(record_id, round_number):
    return {
        "id": record_id,
        "goal": "keep the marker-mode fixture valid",
        "steps": [
            {
                "n": 1,
                "decision_basis": "The fixture needs a valid legacy record.",
                "tool_call": {"name": "noop", "args": {}},
                "observation": "recorded",
            }
        ],
        "outcome": "fixture recorded",
        "reward": {"success": True},
        "meta": {"factory": "factory", "round": round_number, "generator": "grok-4.6"},
    }


class NextRoundFromFilenames(unittest.TestCase):
    def test_batch_r02_and_notes_r07_next_is_8(self):
        result = _invoke(str(ROUNDS_FIXTURE))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["factory"], ROUNDS_FIXTURE.name)
        self.assertEqual(payload["next_round"], 8)
        self.assertEqual(payload["write"], "batch-r08.jsonl")
        self.assertEqual(payload["notes"], "NOTES-r08.md")
        self.assertIn(2, payload["existing"])
        self.assertIn(7, payload["existing"])

    def test_only_trajectories_jsonl_next_is_2(self):
        with tempfile.TemporaryDirectory() as raw:
            factory = Path(raw) / "r1-only"
            factory.mkdir()
            (factory / "trajectories.jsonl").write_text("{}\n")
            result = _invoke(str(factory))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["factory"], "r1-only")
            self.assertEqual(payload["next_round"], 2)
            self.assertEqual(payload["write"], "batch-r02.jsonl")
            self.assertEqual(payload["notes"], "NOTES-r02.md")
            self.assertEqual(payload["existing"], [1])


class NextRoundRefuseOccupied(unittest.TestCase):
    def test_allocate_zero_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            factory = Path(raw) / "invalid"
            factory.mkdir()
            result = _invoke("--allocate", "0", str(factory))
            self.assertEqual(result.returncode, 1)
            self.assertIn("at least 1", result.stderr)

    def test_allocate_8_fails_when_batch_r08_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            factory = Path(raw) / "occupied"
            factory.mkdir()
            batch = factory / "batch-r08.jsonl"
            batch.write_text('{"meta": {"round": 8}}\n')
            before = batch.read_bytes()

            result = _invoke("--allocate", "8", str(factory))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertEqual(batch.read_bytes(), before)
            self.assertEqual(
                {p.name for p in factory.iterdir()},
                {"batch-r08.jsonl"},
            )

            default = _invoke(str(factory))
            self.assertEqual(default.returncode, 0, default.stderr)
            self.assertEqual(json.loads(default.stdout)["next_round"], 9)


class NextRoundWriteIndex(unittest.TestCase):
    def test_write_index_two_factory_subdirs(self):
        with tempfile.TemporaryDirectory() as raw:
            run_root = Path(raw) / "run"
            alpha = run_root / "factory-alpha"
            beta = run_root / "factory-beta"
            empty = run_root / "empty-dir"
            alpha.mkdir(parents=True)
            beta.mkdir()
            empty.mkdir()
            (alpha / "batch-r02.jsonl").write_text('{"meta": {"round": 2}}\n')
            (beta / "NOTES-r03.md").write_text("# notes\n")
            (run_root / "manifest.json").write_text("{}\n")

            result = _invoke("--write-index", str(run_root))
            self.assertEqual(result.returncode, 0, result.stderr)
            index_path = run_root / "NEXT_ROUND.json"
            self.assertTrue(index_path.is_file())
            payload = json.loads(index_path.read_text())
            entries = _index_entries(payload)
            self.assertEqual(set(entries), {"factory-alpha", "factory-beta"})
            self.assertEqual(entries["factory-alpha"]["next_round"], 3)
            self.assertEqual(entries["factory-alpha"]["write"], "batch-r03.jsonl")
            self.assertEqual(entries["factory-beta"]["next_round"], 4)
            self.assertEqual(entries["factory-beta"]["notes"], "NOTES-r04.md")
            self.assertFalse((alpha / "batch-r03.jsonl").exists())
            self.assertFalse((beta / "batch-r04.jsonl").exists())
            self.assertEqual(
                {p.name for p in alpha.iterdir()},
                {"batch-r02.jsonl"},
            )
            self.assertEqual(
                {p.name for p in beta.iterdir()},
                {"NOTES-r03.md"},
            )


class NextRoundMarkerMode(unittest.TestCase):
    def test_marker_mode_ignores_uncommitted_filename_claims(self):
        with tempfile.TemporaryDirectory() as raw:
            factory = Path(raw) / "factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "legacy_baseline": 2,
                        "commit_point": "ROUND-rNN.complete.json",
                    }
                )
                + "\n"
            )
            (factory / "batch-r01.jsonl").write_text(json.dumps(_episode("legacy-1", 1)) + "\n")
            (factory / "batch-r02.jsonl").write_text(json.dumps(_episode("legacy-2", 2)) + "\n")
            batch = factory / "batch-r03.jsonl"
            batch.write_text(json.dumps(_episode("committed", 3)) + "\n")
            notes = factory / "NOTES-r03.md"
            notes.write_text("committed notes\n")
            marker = factory / "ROUND-r03.complete.json"
            marker.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "factory": "factory",
                        "round": 3,
                        "records": 1,
                        "expected_records": 1,
                        "commit_point": marker.name,
                        "files": [
                            {
                                "name": batch.name,
                                "sha256": hashlib.sha256(batch.read_bytes()).hexdigest(),
                            },
                            {
                                "name": notes.name,
                                "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                )
                + "\n"
            )
            (factory / "batch-r99.jsonl").write_text("{not-json\n")
            (factory / "NOTES-r88.md").write_text("uncommitted\n")

            result = _invoke(str(factory))

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["next_round"], 4)
            self.assertEqual(payload["write"], "batch-r04.jsonl")

    def test_corrupt_marker_state_exits_cleanly_without_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            factory = Path(raw) / "factory"
            factory.mkdir()
            (factory / ".round-marker-mode.json").write_text("{broken\n")
            result = _invoke(str(factory))
            self.assertEqual(result.returncode, 1)
            self.assertIn("cannot read transaction file", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
