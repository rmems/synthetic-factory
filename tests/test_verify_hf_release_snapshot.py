"""Tests for the release verifier's raw_snapshot provenance declaration checks."""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
import verify_hf_release

SNAPSHOT_REVISION = "a" * 40
SNAPSHOT_DIGEST = "b" * 64


def snapshot_errors(snapshot: object) -> tuple[tuple[tuple[str, str], ...], list[str]]:
    """Validate one raw_snapshot declaration; return the accepted entries and the errors."""

    errors: list[str] = []
    entries = verify_hf_release._snapshot_entries({"raw_snapshot": snapshot}, errors)
    return entries, errors


def snapshot_with(files: object, revision: object = SNAPSHOT_REVISION) -> dict:
    return {"revision": revision, "files": files}


class RawSnapshotDeclarationTests(unittest.TestCase):
    def test_valid_declaration_is_accepted(self) -> None:
        path = "data/raw/batch-r01.jsonl"
        entries, errors = snapshot_errors(
            snapshot_with([{"path": path, "sha256": SNAPSHOT_DIGEST}])
        )
        self.assertEqual(errors, [])
        self.assertEqual(entries, ((path, SNAPSHOT_DIGEST),))

    def test_unusable_snapshot_is_refused_before_its_files(self) -> None:
        cases = {
            "provenance missing raw_snapshot": None,
            "40-character immutable revision": snapshot_with([], revision="main"),
            "at least one raw payload file": snapshot_with([]),
        }
        for expected, snapshot in cases.items():
            with self.subTest(expected=expected):
                entries, errors = snapshot_errors(snapshot)
                self.assertEqual(entries, ())
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(expected, errors[0])

    def test_each_bad_file_declaration_is_reported(self) -> None:
        cases = {
            "must be an object": "data/raw/batch-r01.jsonl",
            "unsafe payload path: 7": {"path": 7, "sha256": SNAPSHOT_DIGEST},
            "unsafe payload path: 'data/other/x.jsonl'": {
                "path": "data/other/x.jsonl",
                "sha256": SNAPSHOT_DIGEST,
            },
            "unsafe payload path: 'data/raw/../x.jsonl'": {
                "path": "data/raw/../x.jsonl",
                "sha256": SNAPSHOT_DIGEST,
            },
            "invalid sha256 for data/raw/x.jsonl": {"path": "data/raw/x.jsonl", "sha256": "z"},
        }
        for expected, declaration in cases.items():
            with self.subTest(expected=expected):
                entries, errors = snapshot_errors(snapshot_with([declaration]))
                self.assertEqual(entries, ())
                self.assertEqual(len(errors), 1, errors)
                self.assertIn(expected, errors[0])

    def test_repeated_payload_path_is_reported(self) -> None:
        declaration = {"path": "data/raw/batch-r01.jsonl", "sha256": SNAPSHOT_DIGEST}
        _entries, errors = snapshot_errors(snapshot_with([declaration, declaration]))
        self.assertEqual(errors, ["raw_snapshot repeats a payload path"])


if __name__ == "__main__":
    unittest.main()
