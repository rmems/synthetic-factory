"""Tests for pipelines/oracle_grounded/parity_destination.py -- the outputs/raw guard."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parity_contract_support import contract  # noqa: E402


class RawTreeDestinationGuard(unittest.TestCase):
    """Generator CLIs may never land a round beneath immutable outputs/raw."""

    def test_rejects_a_lexical_raw_destination(self):
        self.assertIsNotNone(
            contract.raw_tree_destination_error("outputs/raw/2026-08-31/batch.jsonl")
        )

    def test_rejects_an_absolute_raw_destination(self):
        self.assertIsNotNone(
            contract.raw_tree_destination_error(
                "/anywhere/outputs/raw/2026-08-31/batch.jsonl"
            )
        )

    def test_rejects_a_dotdot_respelling(self):
        # Lexical parts alone never spell outputs/raw here; only the
        # resolved form does.
        self.assertIsNotNone(
            contract.raw_tree_destination_error(
                "outputs/staging/../raw/2026-08-31/batch.jsonl"
            )
        )

    def test_rejects_a_symlink_detour(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "outputs" / "raw"
            raw.mkdir(parents=True)
            innocent = Path(tmp) / "innocent"
            innocent.symlink_to(raw, target_is_directory=True)
            self.assertIsNotNone(
                contract.raw_tree_destination_error(innocent / "batch.jsonl")
            )

    def test_accepts_staging_and_scratch_destinations(self):
        self.assertIsNone(
            contract.raw_tree_destination_error("outputs/staging/run/batch.jsonl")
        )
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(
                contract.raw_tree_destination_error(Path(tmp) / "run" / "batch.jsonl")
            )

    def test_does_not_match_a_prefix_named_directory(self):
        # outputs/rawer is not outputs/raw; the guard matches exact path
        # parts, not string prefixes.
        self.assertIsNone(
            contract.raw_tree_destination_error("outputs/rawer/run/batch.jsonl")
        )


if __name__ == "__main__":
    unittest.main()
