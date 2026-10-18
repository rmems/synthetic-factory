#!/usr/bin/env python3
"""Lane-authentication tests for the curation gate (pipelines/curate_gate.py).

Lane-output authentication in the curation gate: every non-empty lane needs a
manifest that accounts for each source record with a known action and reason
codes, and whose hashes, ids, paths and transform match the outputs it
describes, including consolidated outputs matched back to one source identity.
"""

import json
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import (  # noqa: E402
    CurateGateAssertionsMixin,
    rewrite_json,
    temp_root,
)
from gate_fixture import (  # noqa: E402
    PIPELINES,
    GateFixture,
    _lane_manifest_entry,
    _preference,
    _read_jsonl,
    _thalamic,
    _write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_rewards  # noqa: E402

_OUTPUT_MISMATCH = "output records do not match its manifest"
_PREFERENCE_TRANSFORM = "same-context-preference-curation"
_FACTORY_A_BATCH = "factory-a/batch-r01.jsonl"
_FACTORY_B_BATCH = "factory-b/batch-r02.jsonl"


class LaneAuthenticationTests(CurateGateAssertionsMixin, unittest.TestCase):
    """Lane outputs are admitted only when their manifest authenticates them."""

    def setUp(self):
        self.root = temp_root(self)

    def test_reward_converter_emits_a_manifest_the_gate_can_authenticate(self):
        source_run = self.root / "raw"
        source = source_run / "thalamic-mini" / "batch-r01.jsonl"
        record = _thalamic("reward-cli")
        _write_jsonl(source, [record])
        outputs = self.root / "lane-reward"
        output = outputs / "thalamic-mini" / "batch-r01.jsonl"
        sidecars = outputs / "reward-sidecars.jsonl"
        manifest = outputs / "manifest.json"

        curate_rewards.convert_jsonl(
            source,
            output,
            sidecars,
            source_path="thalamic-mini/batch-r01.jsonl",
            manifest_path=manifest,
        )
        lane = {
            "order": 4,
            "bead": "sf-c5l.4",
            "transform": "reward_ontology",
            "version": curate_rewards.REWARD_TRANSFORM_VERSION,
            "outputs_dir": outputs,
            "manifest_path": manifest,
            "manifest_format": "json",
            "artifacts": [
                {
                    "kind": curate_gate.REWARD_SIDECAR_KIND,
                    "source_path": sidecars,
                    "destination": Path("reward-sidecars.jsonl"),
                }
            ],
        }

        prepared = curate_gate._prepare_lane(  # noqa: SLF001
            lane,
            curate_gate._load_source_records(source_run),  # noqa: SLF001
        )

        self.assertEqual(len(prepared["entries"]), 1)
        self.assertEqual(len(prepared["records"]), 1)
        self.assertEqual(prepared["entries"][0]["action"], "retained")
        self.assertEqual(
            prepared["records"][0]["record"][curate_rewards.ANNOTATION_FIELD]["ontology_version"],
            curate_rewards.ONTOLOGY_VERSION,
        )

    def _assert_plan_edit_refused(self, mutate, message):
        """Edit the integration plan, then assert `integrate` refuses it and writes nothing."""
        fixture = GateFixture(self.root)
        rewrite_json(fixture.plan_path, mutate)
        self.assert_integrate_refused_without_output(fixture, message)

    def _assert_manifest_edit_refused(self, lane_index, mutate, *messages):
        """Edit one lane manifest, then assert `integrate` refuses it and writes nothing."""
        fixture = GateFixture(self.root)
        rewrite_json(fixture.manifest_paths[lane_index], mutate)
        self.assert_integrate_refused_without_output(fixture, *messages)

    def test_integrate_requires_a_manifest_for_every_lane(self):
        self._assert_plan_edit_refused(
            lambda plan: plan["lanes"][4].pop("manifest"),
            "needs a non-empty string 'manifest'",
        )

    def test_integrate_rejects_unaccounted_source_records(self):
        fixture = GateFixture(self.root)
        _write_jsonl(
            fixture.source_run / "unaccounted" / "batch-r03.jsonl",
            [_thalamic("missing-disposition")],
        )

        self.assert_integrate_refused_without_output(
            fixture,
            "lack a retained output or an explicit exclusion/quarantine",
            "unaccounted/batch-r03.jsonl:1",
        )

    def test_integrate_requires_known_actions_and_reason_codes(self):
        for name, mutate, message in (
            (
                "missing-action",
                lambda entries: entries[0].pop("action"),
                "needs an explicit action",
            ),
            (
                "unknown-action",
                lambda entries: entries[0].update(action="invented"),
                "unsupported action",
            ),
            (
                "terminal-without-reason",
                lambda entries: entries[-1].update(reason_codes=[]),
                "needs at least one reason code",
            ),
            (
                "scalar-reason-code",
                lambda entries: entries[-1].update(reason_codes="INVALID_JSON"),
                "must be a list of non-empty strings",
            ),
        ):
            with self.subTest(name=name):
                fixture = GateFixture(self.root / name)
                rewrite_json(fixture.manifest_paths[0], mutate)

                self.assert_integrate_refused_without_output(fixture, message)

    def test_integrate_rejects_output_tampered_after_manifest_creation(self):
        fixture = GateFixture(self.root)
        output = fixture.lane_core / "thalamic-mini" / "batch-r02.jsonl"
        records = _read_jsonl(output)
        records[0]["state"]["env"] = "tampered after identity manifest"
        _write_jsonl(output, records)

        self.assert_integrate_refused_without_output(fixture, _OUTPUT_MISMATCH)

    def test_integrate_rejects_manifest_source_hash_not_matching_source_run(self):
        self._assert_manifest_edit_refused(
            1,
            lambda entries: entries[0].update(source_hash="f" * 64),
            "source hash does not match",
        )

    def test_integrate_rejects_manifest_output_id_not_matching_output_record(self):
        self._assert_manifest_edit_refused(
            1,
            lambda entries: entries[0].update(output_id="self-resealed-forged-output-id"),
            "output_id",
            "does not match authenticated output record",
        )

    def test_integrate_rejects_output_moved_to_an_undeclared_path(self):
        fixture = GateFixture(self.root)
        source = fixture.lane_core / "thalamic-mini" / "batch-r02.jsonl"
        moved = fixture.lane_core / "other-factory" / "batch-r02.jsonl"
        moved.parent.mkdir(parents=True)
        source.rename(moved)

        self.assert_integrate_refused_without_output(fixture, _OUTPUT_MISMATCH)

    def test_integrate_rejects_a_manifest_from_another_lane(self):
        self._assert_plan_edit_refused(
            lambda plan: plan["lanes"][1].update(manifest="lane-tag/manifest.json"),
            "declares transform 'tag_taxonomy'",
        )

    def test_integrate_rejects_a_lane_with_zero_records(self):
        fixture = GateFixture(self.root)
        tag_output = fixture.lane_tag / "thalamic-mini" / "batch-r02.jsonl"
        tag_output.write_text("\n")

        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def _consolidated_preference_lane(self, sources, consolidated):
        """Write one-record sources, their consolidated output and a retained manifest."""
        source_run = self.root / "raw"
        outputs = self.root / "lane-preference"
        manifest_path = outputs / "manifest.json"
        for source_path, record in sources:
            _write_jsonl(source_run / source_path, [record])
        _write_jsonl(outputs / "consolidated" / "preferences.jsonl", consolidated)
        source_records = curate_gate._load_source_records(source_run)
        entries = [
            _lane_manifest_entry(
                "retained",
                1,
                transform=_PREFERENCE_TRANSFORM,
                version="1.0.0",
                source_path=source_path,
                record=record,
                source_hash=source_records[(source_path, 1)]["source_hash"],
            )
            for source_path, record in sources
        ]
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(entries), encoding="utf-8")
        lane = {
            "order": 3,
            "bead": "sf-c5l.3",
            "transform": _PREFERENCE_TRANSFORM,
            "version": "1.0.0",
            "outputs_dir": outputs,
            "manifest_path": manifest_path,
            "manifest_format": "json",
            "artifacts": [],
        }
        return lane, source_records

    def test_preference_lane_authenticates_consolidated_outputs_by_source_identity(self):
        first = _preference("pref-first")
        second = _preference("pref-second")
        lane, source_records = self._consolidated_preference_lane(
            ((_FACTORY_A_BATCH, first), (_FACTORY_B_BATCH, second)),
            [first, second],
        )

        prepared = curate_gate._prepare_lane(lane, source_records)

        self.assertEqual(
            [record["source_path"] for record in prepared["records"]],
            [_FACTORY_A_BATCH, _FACTORY_B_BATCH],
        )
        self.assertEqual(
            {record["relative_path"] for record in prepared["records"]},
            {"consolidated/preferences.jsonl"},
        )

    def test_preference_lane_rejects_ambiguous_duplicate_consolidated_outputs(self):
        record = _preference("same-preference")
        lane, source_records = self._consolidated_preference_lane(
            ((_FACTORY_A_BATCH, record), (_FACTORY_B_BATCH, record)),
            [record, record],
        )

        with self.assertRaisesRegex(curate_gate.GateError, "multiple source identities"):
            curate_gate._prepare_lane(lane, source_records)


if __name__ == '__main__':
    unittest.main()
