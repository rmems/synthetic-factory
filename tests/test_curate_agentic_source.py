#!/usr/bin/env python3
"""Source-tree scanning rules for agentic curation: markers, links, decoding."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from curate_agentic import (  # noqa: E402
    ACTION_EXCLUDED,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_RECORD_NOT_OBJECT,
    REASON_SIDES_NOT_OBJECTS,
    curate_record,
    curate_source,
)
from curate_agentic_fixtures import (  # noqa: E402
    episode_fixture,
    preference_fixture,
    step,
)
from round_txn import TransactionError  # noqa: E402


def _write_committed_round(factory):
    """A marker-mode factory whose round 1 is closed by a complete marker."""
    factory.mkdir()
    (factory / ".round-marker-mode.json").write_text(
        '{"version":1,"legacy_baseline":0,"commit_point":"ROUND-rNN.complete.json"}\n'
    )
    batch = factory / "batch-r01.jsonl"
    notes = factory / "NOTES-r01.md"
    batch.write_text(json.dumps(episode_fixture("committed")) + "\n")
    notes.write_text("Novel coverage: 80%\n")
    (factory / "ROUND-r01.complete.json").write_text(
        json.dumps(
            {
                "version": 1,
                "factory": factory.name,
                "round": 1,
                "records": 1,
                "expected_records": 1,
                "commit_point": "ROUND-r01.complete.json",
                "files": [
                    {
                        "name": batch.name,
                        "sha256": hashlib.sha256(batch.read_bytes()).hexdigest(),
                    },
                    {
                        "name": notes.name,
                        "sha256": hashlib.sha256(notes.read_bytes()).hexdigest(),
                    },
                ],
            }
        )
        + "\n"
    )


class CurateAgenticSourceScan(unittest.TestCase):
    """curate_source must scan a tree the way the round marker allows."""

    def test_curate_source_scans_tree_and_handles_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            empty = curate_source(root / "missing-source")
            self.assertEqual(empty["summary"]["input_records"], 0)
            self.assertEqual(empty["summary"]["output_records"], 0)
            self.assertEqual(empty["decisions"], [])

            factory = root / "long-horizon-coding-factory"
            factory.mkdir()
            (factory / "batch-r01.jsonl").write_text(
                json.dumps(episode_fixture())
                + "\n"
                + json.dumps(episode_fixture(steps=[step(1, thought="x")]))
                + "\n{not json}\n",
                encoding="utf-8",
            )
            (root / "tool-use-preference-factory").mkdir()
            (root / "tool-use-preference-factory" / "batch-r01.jsonl").write_text(
                json.dumps(
                    preference_fixture(
                        chosen={"goal": "keep this problem"},
                        rejected={"goal": "change the problem"},
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            run = curate_source(root)

        self.assertEqual(run["summary"]["input_records"], 4)
        self.assertEqual(run["summary"]["output_records"], 2)
        self.assertEqual(run["summary"]["excluded_records"], 2)
        self.assertIn(
            REASON_INVALID_JSON,
            [item["reason_codes"][0] for item in run["decisions"] if item["action"] == ACTION_EXCLUDED],
        )
        self.assertEqual(run["summary"]["preference"]["goal_impure"], 1)

    def test_marker_mode_excludes_uncommitted_batches(self):
        with tempfile.TemporaryDirectory() as temporary:
            factory = Path(temporary) / "agentic-factory"
            _write_committed_round(factory)
            (factory / "batch-r02.jsonl").write_text(
                json.dumps(episode_fixture("uncommitted")) + "\n"
            )
            (factory / "ROUND-r02.publishing.json").write_text("{}\n")

            run = curate_source(factory)

        self.assertEqual(run["summary"]["files"], 1)
        self.assertEqual(run["summary"]["input_records"], 1)
        self.assertEqual(set(run["records_by_rel"]), {"batch-r01.jsonl"})

    def test_marker_mode_excludes_uncommitted_batches_in_nested_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = root / "agentic-factory"
            _write_committed_round(factory)
            work = factory / "work"
            work.mkdir()
            (work / "batch-r02.jsonl").write_text(
                json.dumps(episode_fixture("uncommitted")) + "\n"
            )

            run = curate_source(root)

        self.assertEqual(run["summary"]["files"], 1)
        self.assertEqual(run["summary"]["input_records"], 1)
        self.assertEqual(set(run["records_by_rel"]), {"agentic-factory/batch-r01.jsonl"})

    def test_marker_mode_rejects_unsafe_entries(self):
        for kind in ("directory", "dangling_symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                factory = Path(temporary) / "agentic-factory"
                factory.mkdir()
                (factory / "batch-r01.jsonl").write_text(
                    json.dumps(episode_fixture("uncommitted")) + "\n"
                )
                mode = factory / ".round-marker-mode.json"
                if kind == "directory":
                    mode.mkdir()
                else:
                    mode.symlink_to(factory / "missing-marker-mode.json")

                with self.assertRaisesRegex(TransactionError, "unsafe marker mode file"):
                    curate_source(factory)

    def test_legacy_curation_ignores_symlinked_jsonl(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = root / "agentic-factory"
            factory.mkdir()
            outside = root / "outside.jsonl"
            outside.write_text(json.dumps(episode_fixture("outside")) + "\n")
            (factory / "batch-r01.jsonl").symlink_to(outside)

            run = curate_source(factory)

        self.assertEqual(run["summary"]["files"], 0)
        self.assertEqual(run["summary"]["input_records"], 0)

    def test_exclusion_reasons_cover_non_object_sides_and_invalid_utf8(self):
        curated, decision = curate_record(["not", "an", "object"])
        self.assertIsNone(curated)
        self.assertEqual(decision["reason_codes"], [REASON_RECORD_NOT_OBJECT])

        preference = preference_fixture()
        preference["chosen"] = "not an object"
        curated, decision = curate_record(preference)
        self.assertIsNone(curated)
        self.assertEqual(decision["reason_codes"], [REASON_SIDES_NOT_OBJECTS])

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "invalid.jsonl"
            source.write_bytes(b"\xff\n")
            run = curate_source(source)
        self.assertEqual(run["summary"]["input_records"], 1)
        self.assertEqual(run["summary"]["output_records"], 0)
        self.assertEqual(
            run["decisions"][0]["reason_codes"], [REASON_INVALID_UTF8]
        )

    def test_nonstandard_json_numeric_constants_are_invalid_json(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                source = Path(temporary) / "invalid.jsonl"
                source.write_text(
                    json.dumps(episode_fixture()).replace(
                        '"reward": {"success": true}',
                        f'"reward": {{"success": true, "score": {value}}}',
                    )
                    + "\n"
                )

                run = curate_source(source)

                self.assertEqual(run["summary"]["input_records"], 1)
                self.assertEqual(run["summary"]["output_records"], 0)
                self.assertEqual(
                    run["decisions"][0]["reason_codes"], [REASON_INVALID_JSON]
                )


if __name__ == "__main__":
    unittest.main()
