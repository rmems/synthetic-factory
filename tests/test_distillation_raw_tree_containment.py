#!/usr/bin/env python3
"""Raw-data-safety containment for the distillation JSONL writer.

Every destination ``distill_jsonl.write_jsonl`` touches must pass through
``raw_tree_guard`` -- the one raw-path detector in this repository, which
also recognises another checkout's ``outputs/raw``, symlink aliases and bind
mounts of the raw root -- before it creates so much as a directory.

Extracted from PR #138 (the fixture-builder half of these tests stays with
the builder there). Every test here fails against #138 at 75642831, where
``write_jsonl`` only checked ``destination.exists()``. Destructive paths are
exercised only inside disposable temporary directories.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import raw_tree_guard  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402

RECORDS = [{"id": "r1", "value": 1}, {"id": "r2", "value": 2}]



def _tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file below ``root`` with its exact bytes, nested files included."""

    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _write_evidence(batch: Path) -> None:
    batch.parent.mkdir(parents=True)
    batch.write_text('{"id": "published-evidence"}\n', encoding="utf-8")




class DistillJsonlWriterRawTreeGuard(unittest.TestCase):
    """oracle_grounded.distill_jsonl.write_jsonl, through the contract facade."""

    def test_refuses_a_direct_outputs_raw_destination_before_creating_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "outputs" / "raw" / "demo-run" / "fault-recovery"
            with self.assertRaises(oc.ContractError) as caught:
                oc.write_jsonl(destination / "batch-r01.jsonl", RECORDS)
            self.assertIn("immutable raw evidence", str(caught.exception))
            # The refusal happens before mkdir(parents=True), so not even the
            # factory directory appears inside the raw tree.
            self.assertFalse((root / "outputs").exists())

    def test_refuses_another_checkouts_outputs_raw_and_leaves_its_bytes_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "other-checkout"
            raw = other / "outputs" / "raw"
            _write_evidence(raw / "run-a" / "factory" / "batch-r01.jsonl")
            before = _tree_bytes(other)
            for destination in (
                raw / "run-a" / "factory" / "batch-r02.jsonl",
                raw / "run-b" / "factory" / "batch-r01.jsonl",
            ):
                with self.subTest(destination=destination.relative_to(other)):
                    with self.assertRaises(oc.ContractError) as caught:
                        oc.write_jsonl(destination, RECORDS)
                    self.assertIn("immutable raw evidence", str(caught.exception))
            self.assertEqual(_tree_bytes(other), before)

    def test_refuses_an_alias_of_the_raw_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_root = root / "evidence-root"
            evidence_root.mkdir()
            alias = root / "alias-raw"
            alias.symlink_to(evidence_root, target_is_directory=True)
            with mock.patch.object(raw_tree_guard, "DEFAULT_RAW_OUTPUT_ROOT", evidence_root):
                for destination in (
                    alias / "run" / "factory" / "batch-r01.jsonl",
                    evidence_root / "run" / "factory" / "batch-r01.jsonl",
                ):
                    with self.subTest(destination=destination.relative_to(root)):
                        with self.assertRaises(oc.ContractError) as caught:
                            oc.write_jsonl(destination, RECORDS)
                        self.assertIn("immutable raw evidence", str(caught.exception))
            self.assertEqual(list(evidence_root.iterdir()), [])

    def test_still_writes_outside_the_raw_tree_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "outputs" / "cleaned" / "run" / "batch-r01.jsonl"
            self.assertEqual(oc.write_jsonl(destination, RECORDS), 2)
            self.assertEqual(len(destination.read_text(encoding="utf-8").splitlines()), 2)
            with self.assertRaises(oc.ContractError) as caught:
                oc.write_jsonl(destination, RECORDS)
            self.assertIn("refusing to overwrite", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
