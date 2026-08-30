#!/usr/bin/env python3
"""Focused regressions for the quality-gate identity projection."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

import quality_gate_identity  # noqa: E402


class QualityGateIdentityRegressions(unittest.TestCase):
    def test_long_horizon_coding_fields_are_exact_identity(self):
        baseline = {
            "id": "coding-episode-a",
            "state": {"repository": "payments", "failing_test": "test_dst_fold"},
            "steps": [{"tool_call": "python3 -m unittest", "outcome": "failed"}],
            "outcome": "resolved",
            "reward": {"task_success": 1.0},
            "codebase_type": "python-service",
            "bug_class": "timezone-conversion",
            "plan": "reproduce the fold, patch conversion, and rerun tests",
        }
        alternatives = {
            "codebase_type": "rust-cli",
            "bug_class": "parser-boundary",
            "plan": "inspect the parser, add a boundary check, and rerun tests",
        }

        view = quality_gate_identity.exact_identity_view(baseline)
        for field, alternative in alternatives.items():
            with self.subTest(field=field):
                changed = copy.deepcopy(baseline)
                changed[field] = alternative
                self.assertIn(field, view)
                self.assertNotEqual(
                    quality_gate_identity.record_hash(baseline),
                    quality_gate_identity.record_hash(changed),
                )


if __name__ == "__main__":
    unittest.main()
