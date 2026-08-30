#!/usr/bin/env python3
"""Focused regressions for the quality-gate identity projection."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import write  # noqa: E402
import quality_gate  # noqa: E402
import quality_gate_identity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[1]


class QualityGateIdentityRegressions(unittest.TestCase):
    @staticmethod
    def _bridge_fixture():
        fixture = REPO_ROOT / "tests/fixtures/bridge_raster_valid.jsonl"
        record = json.loads(fixture.read_text(encoding="utf-8").splitlines()[0])
        record["language_view"]["trajectory"]["safety_decision"] = {
            "decision": "ACCEPT",
            "rationale": "the spike budget is internally consistent",
        }
        return record

    @staticmethod
    def _gate_compute(neurons, rate, window_s):
        spikes = round(neurons * rate * window_s)
        return {
            "per_check": [
                {
                    "neurons": neurons,
                    "mean_rate_hz": rate,
                    "window_s": window_s,
                    "spikes": spikes,
                }
            ],
            "total_energy_pJ": spikes * 23,
        }

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

    def test_bridge_gate_compute_budget_is_modeled_identity(self):
        first = self._bridge_fixture()
        second = copy.deepcopy(first)
        first["id"] = "bridge-compute-a"
        second["id"] = "bridge-compute-b"
        first["gate_compute"] = self._gate_compute(100, 10, 0.02)
        second["gate_compute"] = self._gate_compute(1000, 50, 0.05)

        first_exact = quality_gate_identity.exact_identity_view(first)
        second_exact = quality_gate_identity.exact_identity_view(second)
        self.assertEqual(first_exact["gate_compute"], first["gate_compute"])
        self.assertNotEqual(first_exact, second_exact)
        self.assertNotEqual(
            quality_gate_identity.record_hash(first),
            quality_gate_identity.record_hash(second),
        )
        self.assertNotEqual(
            quality_gate_identity.semantic_similarity_view(first),
            quality_gate_identity.semantic_similarity_view(second),
        )
        self.assertNotEqual(
            quality_gate.embedding_tokens(first),
            quality_gate.embedding_tokens(second),
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [first, second])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["counts"]["unique_hashes"], 2)
        self.assertEqual(report["counts"]["excluded_records"], 0)

    def test_bridge_gate_compute_carriers_have_one_canonical_identity(self):
        budget = self._gate_compute(512, 25, 0.04)
        top_level = self._bridge_fixture()
        trajectory = self._bridge_fixture()
        safety_decision = self._bridge_fixture()
        top_level["gate_compute"] = copy.deepcopy(budget)
        trajectory["language_view"]["trajectory"]["gate_compute"] = copy.deepcopy(
            budget
        )
        safety_decision["language_view"]["trajectory"]["safety_decision"][
            "gate_compute"
        ] = copy.deepcopy(budget)

        records = (top_level, trajectory, safety_decision)
        originals = copy.deepcopy(records)
        exact_views = [quality_gate_identity.exact_identity_view(item) for item in records]
        semantic_views = [
            quality_gate_identity.semantic_similarity_view(item) for item in records
        ]

        self.assertTrue(all(view == exact_views[0] for view in exact_views[1:]))
        self.assertTrue(all(view == semantic_views[0] for view in semantic_views[1:]))
        self.assertEqual(
            {quality_gate_identity.record_hash(item) for item in records},
            {quality_gate_identity.record_hash(top_level)},
        )
        self.assertEqual(
            [quality_gate.embedding_tokens(item) for item in records],
            [quality_gate.embedding_tokens(top_level)] * 3,
        )
        self.assertEqual(records, originals)

    def test_bridge_safety_only_carrier_does_not_leave_an_empty_wrapper(self):
        budget = self._gate_compute(256, 20, 0.025)
        top_level = self._bridge_fixture()
        top_level["language_view"]["trajectory"].pop("safety_decision")
        safety_only = copy.deepcopy(top_level)
        top_level["gate_compute"] = copy.deepcopy(budget)
        safety_only["language_view"]["trajectory"]["safety_decision"] = {
            "gate_compute": copy.deepcopy(budget)
        }

        safety_view = quality_gate_identity.exact_identity_view(safety_only)
        self.assertNotIn(
            "safety_decision", safety_view["language_view"]["trajectory"]
        )
        self.assertEqual(
            safety_view,
            quality_gate_identity.exact_identity_view(top_level),
        )

    def test_bridge_equal_lower_precedence_carriers_are_redundant(self):
        budget = self._gate_compute(400, 30, 0.03)

        root_only = self._bridge_fixture()
        root_only["gate_compute"] = copy.deepcopy(budget)
        root_redundant = copy.deepcopy(root_only)
        root_trajectory = root_redundant["language_view"]["trajectory"]
        root_trajectory["gate_compute"] = copy.deepcopy(budget)
        root_trajectory["safety_decision"]["gate_compute"] = copy.deepcopy(budget)
        root_snapshot = copy.deepcopy(root_redundant)
        self.assertEqual(
            quality_gate_identity.exact_identity_view(root_redundant),
            quality_gate_identity.exact_identity_view(root_only),
        )
        self.assertEqual(root_redundant, root_snapshot)

        trajectory_only = self._bridge_fixture()
        trajectory_only["language_view"]["trajectory"]["gate_compute"] = (
            copy.deepcopy(budget)
        )
        trajectory_redundant = copy.deepcopy(trajectory_only)
        trajectory_redundant["language_view"]["trajectory"]["safety_decision"][
            "gate_compute"
        ] = copy.deepcopy(budget)
        self.assertEqual(
            quality_gate_identity.exact_identity_view(trajectory_redundant),
            quality_gate_identity.exact_identity_view(trajectory_only),
        )

    def test_bridge_gate_compute_precedence_preserves_unselected_content(self):
        preferred = self._gate_compute(100, 10, 0.02)
        conflicting = self._gate_compute(1000, 50, 0.05)

        root_selected = self._bridge_fixture()
        root_trajectory = root_selected["language_view"]["trajectory"]
        root_selected["gate_compute"] = copy.deepcopy(preferred)
        root_trajectory["gate_compute"] = copy.deepcopy(conflicting)
        root_trajectory["safety_decision"]["gate_compute"] = "malformed-budget"
        root_view = quality_gate_identity.exact_identity_view(root_selected)
        self.assertEqual(root_view["gate_compute"], preferred)
        self.assertEqual(root_view["language_view"]["trajectory"]["gate_compute"], conflicting)
        self.assertEqual(
            root_view["language_view"]["trajectory"]["safety_decision"][
                "gate_compute"
            ],
            "malformed-budget",
        )

        trajectory_selected = self._bridge_fixture()
        trajectory_view = trajectory_selected["language_view"]["trajectory"]
        trajectory_view["gate_compute"] = copy.deepcopy(preferred)
        trajectory_view["safety_decision"]["gate_compute"] = copy.deepcopy(
            conflicting
        )
        normalized_trajectory = quality_gate_identity.exact_identity_view(
            trajectory_selected
        )
        normalized_trajectory_view = normalized_trajectory["language_view"][
            "trajectory"
        ]
        self.assertEqual(normalized_trajectory["gate_compute"], preferred)
        self.assertNotIn("gate_compute", normalized_trajectory_view)
        self.assertEqual(
            normalized_trajectory_view["safety_decision"]["gate_compute"],
            conflicting,
        )

        safety_selected = self._bridge_fixture()
        safety_view = safety_selected["language_view"]["trajectory"]
        safety_view["gate_compute"] = "malformed-budget"
        safety_view["safety_decision"]["gate_compute"] = copy.deepcopy(preferred)
        normalized_safety = quality_gate_identity.exact_identity_view(safety_selected)
        normalized_safety_view = normalized_safety["language_view"]["trajectory"]
        self.assertEqual(normalized_safety["gate_compute"], preferred)
        self.assertEqual(normalized_safety_view["gate_compute"], "malformed-budget")
        self.assertNotIn(
            "gate_compute", normalized_safety_view["safety_decision"]
        )


if __name__ == "__main__":
    unittest.main()
