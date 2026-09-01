#!/usr/bin/env python3
"""Gate-SNN carrier normalization regressions for quality-gate identity."""

import copy
import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from gate_fixtures import thalamic as thalamic_fixture  # noqa: E402
import quality_gate_identity  # noqa: E402


# Exact-identity digest of the deliberately mutated, gate-SNN-free Bridge
# record in ``test_ungated_bridge_hash_keeps_its_published_baseline``.
UNGATED_BRIDGE_IDENTITY_BASELINE = "a6ce0b1a9c3f4981"


def gate_snn_fixture():
    """Return a fresh Bridge record with spike-gate supervision."""

    fixture = TESTS / "fixtures" / "bridge_gate_snn.jsonl"
    return json.loads(fixture.read_text(encoding="utf-8").splitlines()[0])


class QualityGateGateSnnIdentity(unittest.TestCase):
    def test_bridge_carriers_have_one_population_identity(self):
        top_level = gate_snn_fixture()
        gate_snn = copy.deepcopy(top_level["gate_snn"])
        meta = gate_snn_fixture()
        meta["meta"] = {"gate_snn": meta.pop("gate_snn")}
        trajectory = gate_snn_fixture()
        trajectory["language_view"]["trajectory"]["gate_snn"] = trajectory.pop(
            "gate_snn"
        )
        safety = gate_snn_fixture()
        safety["language_view"]["trajectory"]["safety_decision"]["gate_snn"] = (
            safety.pop("gate_snn")
        )

        records = (top_level, meta, trajectory, safety)
        originals = copy.deepcopy(records)
        views = [quality_gate_identity.exact_identity_view(record) for record in records]

        self.assertEqual(views[0]["gate_snn"], gate_snn)
        self.assertTrue(all(view == views[0] for view in views[1:]))
        self.assertEqual(
            {quality_gate_identity.record_hash(record) for record in records},
            {quality_gate_identity.record_hash(top_level)},
        )
        changed = copy.deepcopy(top_level)
        changed_population = changed["gate_snn"]["populations"][0]
        changed_population["neurons"] = 128
        changed_population["spikes"] = 128
        self.assertNotEqual(
            quality_gate_identity.record_hash(top_level),
            quality_gate_identity.record_hash(changed),
        )
        self.assertEqual(records, originals)

    def test_ungated_bridge_hash_keeps_its_published_baseline(self):
        fixture = TESTS / "fixtures" / "bridge_raster_valid.jsonl"
        record = json.loads(fixture.read_text(encoding="utf-8").splitlines()[0])
        record["language_view"]["trajectory"]["safety_decision"] = {
            "decision": "ACCEPT",
            "rationale": "the spike budget is internally consistent",
        }

        self.assertEqual(
            quality_gate_identity.record_hash(record),
            UNGATED_BRIDGE_IDENTITY_BASELINE,
        )

    def test_redundant_and_conflicting_lower_carriers_remain_distinct(self):
        root_only = gate_snn_fixture()
        redundant = gate_snn_fixture()
        selected = redundant["gate_snn"]
        redundant["meta"] = {"gate_snn": copy.deepcopy(selected)}
        trajectory = redundant["language_view"]["trajectory"]
        trajectory["gate_snn"] = copy.deepcopy(selected)
        trajectory["safety_decision"]["gate_snn"] = copy.deepcopy(selected)

        self.assertEqual(
            quality_gate_identity.exact_identity_view(root_only),
            quality_gate_identity.exact_identity_view(redundant),
        )

        conflicting = gate_snn_fixture()
        lower = copy.deepcopy(conflicting["gate_snn"])
        lower["populations"][0]["neurons"] = 128
        lower["populations"][0]["spikes"] = 128
        conflicting["meta"] = {"gate_snn": lower}
        conflict_view = quality_gate_identity.exact_identity_view(conflicting)

        self.assertEqual(conflict_view["gate_snn"], conflicting["gate_snn"])
        self.assertEqual(conflict_view["gate_snn_unselected"], {"meta": lower})
        self.assertNotEqual(
            quality_gate_identity.record_hash(root_only),
            quality_gate_identity.record_hash(conflicting),
        )

    def test_thalamic_root_and_meta_carriers_share_identity(self):
        top_level = thalamic_fixture("thalamic-top")
        meta = thalamic_fixture("thalamic-meta")
        meta["meta"]["gate_snn"] = meta.pop("gate_snn")

        top_view = quality_gate_identity.exact_identity_view(top_level)
        meta_view = quality_gate_identity.exact_identity_view(meta)

        self.assertEqual(top_view["gate_snn"], top_level["gate_snn"])
        self.assertEqual(top_view, meta_view)
        self.assertEqual(
            quality_gate_identity.record_hash(top_level),
            quality_gate_identity.record_hash(meta),
        )

    def test_preference_wrapper_root_and_meta_gate_carriers_share_identity(self):
        pair = {
            "chosen": thalamic_fixture("wrapper-chosen"),
            "rejected": thalamic_fixture("wrapper-rejected"),
            "critique": "the chosen trajectory preserves the safety gate",
        }
        gate_snn = copy.deepcopy(gate_snn_fixture()["gate_snn"])
        root = copy.deepcopy(pair)
        root["gate_snn"] = copy.deepcopy(gate_snn)
        meta = copy.deepcopy(pair)
        meta["meta"] = {"gate_snn": copy.deepcopy(gate_snn)}
        originals = copy.deepcopy((root, meta))

        root_view = quality_gate_identity.exact_identity_view(root)
        meta_view = quality_gate_identity.exact_identity_view(meta)

        self.assertEqual(root_view["gate_snn"], gate_snn)
        self.assertEqual(root_view, meta_view)
        self.assertEqual(
            quality_gate_identity.record_hash(root),
            quality_gate_identity.record_hash(meta),
        )
        changed = copy.deepcopy(root)
        changed_population = changed["gate_snn"]["populations"][0]
        changed_population["neurons"] = 128
        changed_population["spikes"] = 128
        self.assertNotEqual(
            quality_gate_identity.record_hash(root),
            quality_gate_identity.record_hash(changed),
        )
        self.assertEqual((root, meta), originals)

    def test_thalamic_meta_raster_is_normalized_into_identity(self):
        top_level = thalamic_fixture("thalamic-raster")
        meta = thalamic_fixture("thalamic-raster")
        meta["meta"]["raster"] = meta.pop("raster")

        top_view = quality_gate_identity.exact_identity_view(top_level)
        meta_view = quality_gate_identity.exact_identity_view(meta)

        self.assertEqual(meta_view["raster"], meta["meta"]["raster"])
        self.assertEqual(top_view, meta_view)
        changed = copy.deepcopy(meta)
        changed["meta"]["raster"]["routing"]["target"] = "pop_output_100"
        self.assertNotEqual(
            quality_gate_identity.record_hash(meta),
            quality_gate_identity.record_hash(changed),
        )


if __name__ == "__main__":
    unittest.main()
