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
    def _audit(records):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            return quality_gate.audit_run(root)

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

    def _bridge_preference_side(self, suffix, action_record_id):
        record = self._bridge_fixture()
        trajectory = record["language_view"]["trajectory"]
        trajectory["id"] = f"bridge-trajectory-{suffix}"
        trajectory["meta"] = {"factory": "bridge", "round": suffix}
        trajectory["provenance"] = {
            "kind": "designed",
            "claimed": f"simulation-{suffix}",
        }
        trajectory["state"]["episode_id"] = f"bridge-episode-{suffix}"
        trajectory["state"]["trajectory_id"] = f"trajectory-state-{suffix}"
        trajectory["state"]["provenance"] = {
            "kind": "designed",
            "claimed": f"state-simulation-{suffix}",
        }
        trajectory["executed_action"] = {
            "action_type": "load_record",
            "record_id": action_record_id,
        }
        return record

    @staticmethod
    def _wrap_bridge(record, scope):
        if scope == "standalone":
            return record
        other = {
            "state": {"task": "compare the same bridge record"},
            "executed_action": {"record_id": "preference-other-42"},
            "outcome": "comparison complete",
        }
        pair = {"chosen": copy.deepcopy(other), "rejected": copy.deepcopy(other)}
        pair[scope] = record
        return pair

    @staticmethod
    def _bridge_side(view, scope):
        return view if scope == "standalone" else view[scope]

    @staticmethod
    def _raster_variant(label, neurons, rate, window_ms):
        spikes = round(neurons * rate * window_ms / 1000)
        return {
            "window_ms": window_ms,
            "neurons": neurons,
            "mean_rate_hz": rate,
            "spikes": spikes,
            "energy_pJ": spikes * 23,
            "energy_uJ": spikes * 23e-6,
            "routing": {
                "source": f"{label}-source-{neurons}",
                "target": f"{label}-target-{rate}",
                "table": [
                    {
                        "from": f"{label}-source-{neurons}",
                        "to": f"{label}-target-{rate}",
                        "weight": 0.625,
                    }
                ],
            },
            "excerpt": [
                {"t_ms": 1.5, "neuron_id": 1, "channel": f"{label}-onset"},
                {
                    "t_ms": window_ms - 1,
                    "neuron_id": neurons - 1,
                    "channel": f"{label}-offset",
                },
            ],
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

        report = self._audit([first, second])

        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["counts"]["unique_hashes"], 2)
        self.assertEqual(report["counts"]["excluded_records"], 0)

    def test_bridge_raster_root_and_meta_carriers_share_identity(self):
        for scope in ("standalone", "chosen", "rejected"):
            with self.subTest(scope=scope):
                top_level = self._bridge_fixture()
                meta_carried = self._bridge_fixture()
                meta_carried["meta"] = {"raster": meta_carried.pop("raster")}
                for record in (top_level, meta_carried):
                    record["language_view"]["trajectory"]["executed_action"] = {
                        "record_id": "modeled-raster-asset-42"
                    }
                top_object = self._wrap_bridge(top_level, scope)
                meta_object = self._wrap_bridge(meta_carried, scope)
                originals = copy.deepcopy((top_object, meta_object))

                top_exact = quality_gate_identity.exact_identity_view(top_object)
                meta_exact = quality_gate_identity.exact_identity_view(meta_object)
                self.assertEqual(top_exact, meta_exact)
                self.assertEqual(
                    quality_gate_identity.semantic_similarity_view(top_object),
                    quality_gate_identity.semantic_similarity_view(meta_object),
                )
                self.assertEqual(
                    quality_gate_identity.record_hash(top_object),
                    quality_gate_identity.record_hash(meta_object),
                )
                side = self._bridge_side(
                    quality_gate_identity.semantic_similarity_view(meta_object), scope
                )
                self.assertEqual(
                    side["language_view"]["trajectory"]["executed_action"][
                        "record_id"
                    ],
                    "modeled-raster-asset-42",
                )
                self.assertEqual((top_object, meta_object), originals)

        root_record = self._bridge_fixture()
        meta_record = self._bridge_fixture()
        meta_record["meta"] = {"raster": meta_record.pop("raster")}
        report = self._audit([root_record, meta_record])
        self.assertEqual(len(report["duplicates"]), 1)

    def test_bridge_malformed_root_raster_survives_meta_selection(self):
        malformed_values = (
            "malformed root raster alpha with no structured spike evidence",
            ["malformed", "root", "raster", "omega", 8, 13, 21, 34],
        )
        for scope in ("standalone", "chosen", "rejected"):
            with self.subTest(scope=scope):
                objects = []
                selected_raster = None
                for malformed in malformed_values:
                    bridge = self._bridge_fixture()
                    selected_raster = bridge.pop("raster")
                    bridge["raster"] = copy.deepcopy(malformed)
                    bridge["meta"] = {"raster": copy.deepcopy(selected_raster)}
                    bridge["language_view"]["trajectory"]["executed_action"] = {
                        "record_id": "modeled-raster-asset-42"
                    }
                    objects.append(self._wrap_bridge(bridge, scope))
                originals = copy.deepcopy(objects)
                views = [
                    quality_gate_identity.exact_identity_view(item) for item in objects
                ]
                sides = [self._bridge_side(view, scope) for view in views]

                self.assertTrue(all(side["raster"] == selected_raster for side in sides))
                self.assertEqual(
                    sides[0]["raster_unselected"],
                    {"root": malformed_values[0]},
                )
                self.assertEqual(
                    sides[1]["raster_unselected"],
                    {"root": malformed_values[1]},
                )
                self.assertNotEqual(views[0], views[1])
                self.assertNotEqual(
                    quality_gate_identity.semantic_similarity_view(objects[0]),
                    quality_gate_identity.semantic_similarity_view(objects[1]),
                )
                self.assertNotEqual(
                    quality_gate_identity.record_hash(objects[0]),
                    quality_gate_identity.record_hash(objects[1]),
                )
                semantic_side = self._bridge_side(
                    quality_gate_identity.semantic_similarity_view(objects[0]), scope
                )
                self.assertEqual(
                    semantic_side["language_view"]["trajectory"]["executed_action"][
                        "record_id"
                    ],
                    "modeled-raster-asset-42",
                )
                self.assertEqual(objects, originals)
                report = self._audit(objects)
                self.assertEqual(report["duplicates"], [])
                self.assertEqual(report["counts"]["excluded_records"], 0)

    def test_bridge_root_raster_preserves_nonredundant_meta_carrier(self):
        selected = self._bridge_fixture()["raster"]
        conflicting = self._raster_variant("conflicting", 8000, 50, 50)
        malformed_values = (
            "malformed lower raster alpha without a routing table",
            ["malformed", "lower", "raster", "omega", 55, 89, 144],
        )
        for scope in ("standalone", "chosen", "rejected"):
            with self.subTest(scope=scope):
                root_only = self._bridge_fixture()
                redundant = self._bridge_fixture()
                reordered_selected = dict(reversed(list(selected.items())))
                redundant["meta"] = {"raster": copy.deepcopy(reordered_selected)}
                conflict = self._bridge_fixture()
                conflict["meta"] = {"raster": copy.deepcopy(conflicting)}
                malformed = []
                for value in malformed_values:
                    record = self._bridge_fixture()
                    record["meta"] = {"raster": copy.deepcopy(value)}
                    malformed.append(record)
                records = [root_only, redundant, conflict, *malformed]
                for record in records:
                    record["language_view"]["trajectory"]["executed_action"] = {
                        "record_id": "modeled-raster-asset-42"
                    }
                objects = [self._wrap_bridge(item, scope) for item in records]
                originals = copy.deepcopy(objects)
                views = [
                    quality_gate_identity.exact_identity_view(item) for item in objects
                ]
                sides = [self._bridge_side(view, scope) for view in views]

                self.assertEqual(views[0], views[1])
                self.assertNotIn("raster_unselected", sides[1])
                self.assertEqual(
                    sides[2]["raster_unselected"], {"meta": conflicting}
                )
                self.assertEqual(
                    sides[3]["raster_unselected"],
                    {"meta": malformed_values[0]},
                )
                self.assertEqual(
                    sides[4]["raster_unselected"],
                    {"meta": malformed_values[1]},
                )
                self.assertNotEqual(views[0], views[2])
                self.assertNotEqual(views[3], views[4])
                self.assertNotEqual(
                    quality_gate_identity.semantic_similarity_view(objects[0]),
                    quality_gate_identity.semantic_similarity_view(objects[2]),
                )
                self.assertEqual(objects, originals)
                report = self._audit([objects[2], objects[3], objects[4]])
                self.assertEqual(report["duplicates"], [])
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

    def test_bridge_malformed_root_survives_nested_budget_normalization(self):
        budget = self._gate_compute(640, 15, 0.05)
        for carrier in ("trajectory", "safety_decision"):
            with self.subTest(carrier=carrier):
                first = self._bridge_fixture()
                second = copy.deepcopy(first)
                first["gate_compute"] = "malformed-root-alpha"
                second["gate_compute"] = "malformed-root-omega"
                for record in (first, second):
                    trajectory = record["language_view"]["trajectory"]
                    if carrier == "trajectory":
                        trajectory["gate_compute"] = copy.deepcopy(budget)
                    else:
                        trajectory["gate_compute"] = "malformed-nested-carrier"
                        trajectory["safety_decision"]["gate_compute"] = (
                            copy.deepcopy(budget)
                        )

                first_view = quality_gate_identity.exact_identity_view(first)
                second_view = quality_gate_identity.exact_identity_view(second)
                self.assertEqual(first_view["gate_compute"], budget)
                self.assertEqual(second_view["gate_compute"], budget)
                self.assertEqual(
                    first_view["gate_compute_unselected"],
                    {"root": "malformed-root-alpha"},
                )
                self.assertEqual(
                    second_view["gate_compute_unselected"],
                    {"root": "malformed-root-omega"},
                )
                self.assertNotEqual(
                    quality_gate_identity.record_hash(first),
                    quality_gate_identity.record_hash(second),
                )
                self.assertNotEqual(
                    quality_gate_identity.semantic_similarity_view(first),
                    quality_gate_identity.semantic_similarity_view(second),
                )
                report = self._audit([first, second])
                self.assertEqual(report["duplicates"], [])
                self.assertEqual(report["counts"]["excluded_records"], 0)

    def test_bridge_bookkeeping_is_stripped_inside_each_preference_arm(self):
        common_side = {
            "state": {"task": "compare the same bridge record"},
            "executed_action": {"action": "hold"},
            "outcome": "comparison complete",
        }
        for arm in ("chosen", "rejected"):
            with self.subTest(arm=arm):
                first = {
                    "chosen": copy.deepcopy(common_side),
                    "rejected": copy.deepcopy(common_side),
                }
                second = copy.deepcopy(first)
                first[arm] = self._bridge_preference_side("a", "modeled-asset-42")
                second[arm] = self._bridge_preference_side("b", "modeled-asset-42")

                self.assertNotEqual(
                    quality_gate_identity.record_hash(first),
                    quality_gate_identity.record_hash(second),
                )
                first_view = quality_gate_identity.semantic_similarity_view(first)
                second_view = quality_gate_identity.semantic_similarity_view(second)
                self.assertEqual(first_view, second_view)
                trajectory = first_view[arm]["language_view"]["trajectory"]
                self.assertNotIn("id", trajectory)
                self.assertNotIn("meta", trajectory)
                self.assertNotIn("provenance", trajectory)
                self.assertNotIn("episode_id", trajectory["state"])
                self.assertNotIn("trajectory_id", trajectory["state"])
                self.assertNotIn("provenance", trajectory["state"])
                self.assertEqual(
                    trajectory["executed_action"]["record_id"],
                    "modeled-asset-42",
                )
                report = self._audit([first, second])
                self.assertEqual(len(report["duplicates"]), 1)
                self.assertEqual(report["duplicates"][0]["kind"], "embedding")
                self.assertEqual(report["duplicates"][0]["similarity"], 1.0)

                different_action = copy.deepcopy(second)
                different_action[arm]["language_view"]["trajectory"][
                    "executed_action"
                ]["record_id"] = "modeled-asset-99"
                self.assertNotEqual(
                    first_view,
                    quality_gate_identity.semantic_similarity_view(different_action),
                )

    def test_bridge_sidecar_normalization_composes_with_preference_arms(self):
        budget = self._gate_compute(320, 25, 0.04)
        top_level = self._bridge_fixture()
        nested = self._bridge_fixture()
        top_level["gate_compute"] = copy.deepcopy(budget)
        nested["language_view"]["trajectory"]["gate_compute"] = copy.deepcopy(
            budget
        )
        rejected = {
            "state": {"task": "compare the same bridge record"},
            "executed_action": {"action": "hold"},
        }
        top_pair = {"chosen": top_level, "rejected": copy.deepcopy(rejected)}
        nested_pair = {"chosen": nested, "rejected": copy.deepcopy(rejected)}

        self.assertEqual(
            quality_gate_identity.exact_identity_view(top_pair),
            quality_gate_identity.exact_identity_view(nested_pair),
        )
        self.assertEqual(
            quality_gate_identity.semantic_similarity_view(top_pair),
            quality_gate_identity.semantic_similarity_view(nested_pair),
        )


if __name__ == "__main__":
    unittest.main()
