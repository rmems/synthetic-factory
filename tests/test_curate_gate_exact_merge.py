#!/usr/bin/env python3
"""Regression coverage for exact-decimal lane-delta conflict detection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))

import curate_gate  # noqa: E402
from exact_json import parse_finite_json_float  # noqa: E402


class ExactMergeTests(unittest.TestCase):
    def test_merge_rejects_conflicting_exact_decimal_lane_changes(self):
        """Binary-float equality must not hide incompatible retained decimals."""

        baseline = {"metric": parse_finite_json_float("0.0")}
        current = {"metric": parse_finite_json_float("1.0")}
        lane_value = {"metric": parse_finite_json_float("1.0000000000000001")}

        with self.assertRaisesRegex(
            curate_gate.GateError,
            r"lane 'spike' conflicts with an earlier lane at source.jsonl:7/metric",
        ):
            curate_gate._merge_lane_delta(
                baseline,
                current,
                lane_value,
                source_key=("source.jsonl", 7),
                transform="spike",
            )

    def test_same_json_keeps_json_number_types_distinct(self):
        """Integer and decimal JSON values remain unequal despite Python equality."""

        self.assertFalse(curate_gate._same_json(1, 1.0))


if __name__ == "__main__":
    unittest.main()
