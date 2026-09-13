#!/usr/bin/env python3
"""Behavioral checks for immutable compose-stage inputs."""

import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))


class ComposeContextContract(unittest.TestCase):
    def test_source_coordinates_cannot_change_between_lane_calls(self):
        """Mutation must not redirect a later stage to different evidence."""

        try:
            from compose_curated_context import SourceCoordinates
        except ModuleNotFoundError:
            self.fail("compose_curated_context.SourceCoordinates is missing")

        source = SourceCoordinates("factory/batch.jsonl", 3, "a" * 64)
        with self.assertRaises(FrozenInstanceError):
            source.line = 4


if __name__ == "__main__":
    unittest.main()
