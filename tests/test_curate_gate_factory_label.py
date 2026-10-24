#!/usr/bin/env python3
"""Factory-label gate: path slug versus meta.factory and reviewed id prefixes.

A record that names another factory from inside a thalamic file must fail
integrate. The gate fixture's honest corpus, whose placeholder ``meta.factory``
is not a factory label, must still integrate and promote.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import temp_root  # noqa: E402
from gate_fixture import GateFixture, _episode, _preference, _thalamic  # noqa: E402

_PIPELINES = _TESTS.parent / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_gate_factory_label as factory_label  # noqa: E402
import curate_gate_gates  # noqa: E402

_RIGHTS_PASS = mock.patch.object(
    curate_gate_gates,
    "evaluate_rights",
    return_value=({"passed": True, "enforced": False}, []),
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


class FactoryLabelGateTests(unittest.TestCase):
    """The gate judges one cleaned tree without the rest of integrate."""

    def test_unrecognized_meta_factory_and_unmapped_prefix_pass(self):
        root = temp_root(self)
        _write_jsonl(
            root / "thalamic-mini" / "batch.jsonl",
            [
                {"id": "t-1", "meta": {"factory": "fixture"}},
                {"id": "zz-r12-local", "meta": {"factory": "fixture"}},
                {"id": "episode-1"},
            ],
        )
        report = factory_label.factory_label_gate(root)
        self.assertTrue(report["passed"])
        self.assertEqual(report["count"], 0)

    def test_meta_factory_matching_the_path_passes(self):
        root = temp_root(self)
        _write_jsonl(
            root / "thalamic-mini" / "batch.jsonl",
            [{"id": "t-1", "meta": {"factory": "thalamic-mini"}}],
        )
        report = factory_label.factory_label_gate(root)
        self.assertTrue(report["passed"])

    def test_meta_factory_naming_another_factory_fails(self):
        root = temp_root(self)
        _write_jsonl(
            root / "thalamic-mini" / "batch.jsonl",
            [{"id": "t-1", "meta": {"factory": "bridge-factory"}}],
        )
        report = factory_label.factory_label_gate(root)
        self.assertFalse(report["passed"])
        self.assertEqual(report["count"], 1)
        example = report["examples"][0]
        self.assertEqual(example["source"], "thalamic-mini/batch.jsonl:1")
        self.assertEqual(example["path_factory"], "thalamic-mini")
        self.assertEqual(example["meta_factory"], ["bridge-factory"])
        self.assertNotIn("id_prefix", example)

    def test_borrowed_prefix_with_matching_meta_factory_passes(self):
        """A leftover id may borrow another mill's prefix when meta.factory matches."""
        root = temp_root(self)
        _write_jsonl(
            root / "api-contract-migration-factory" / "batch.jsonl",
            [
                {
                    "id": "dbc-r3714-buildkit-cache-mount-id-leftover",
                    "meta": {"factory": "api-contract-migration-factory"},
                }
            ],
        )
        report = factory_label.factory_label_gate(root)
        self.assertTrue(report["passed"])
        self.assertEqual(report["count"], 0)
        self.assertEqual(report["examples"], [])
        note = report["prefix_notes"][0]
        self.assertEqual(note["id_prefix"], "dbc")
        self.assertEqual(note["prefix_home"], "docker-build-cache-factory")
        self.assertEqual(note["path_factory"], "api-contract-migration-factory")
        self.assertNotIn("meta_factory", note)

    def test_prefix_without_a_meta_disagreement_is_a_note(self):
        foreign = temp_root(self)
        _write_jsonl(
            foreign / "thalamic-mini" / "batch.jsonl",
            [{"id": "gql-r12-spill"}],
        )
        foreign_report = factory_label.factory_label_gate(foreign)
        self.assertTrue(foreign_report["passed"])
        self.assertEqual(foreign_report["count"], 0)
        note = foreign_report["prefix_notes"][0]
        self.assertEqual(note["id_prefix"], "gql")
        self.assertEqual(note["prefix_home"], "graphql-nplusone-factory")
        self.assertNotIn("meta_factory", note)

        native = temp_root(self)
        _write_jsonl(
            native / "graphql-nplusone-factory" / "batch.jsonl",
            [{"id": "gql-r12-native", "meta": {"factory": "graphql-nplusone-factory"}}],
        )
        native_report = factory_label.factory_label_gate(native)
        self.assertTrue(native_report["passed"])
        self.assertEqual(native_report["prefix_notes"], [])

    def test_unmapped_prefix_does_not_invent_a_home(self):
        root = temp_root(self)
        _write_jsonl(
            root / "thalamic-mini" / "batch.jsonl",
            [{"id": "zz-r12-local"}],
        )
        self.assertTrue(factory_label.factory_label_gate(root)["passed"])


class FactoryLabelIntegrateTests(unittest.TestCase):
    """integrate fails closed on a misfiled factory and promotes an honest corpus."""

    def setUp(self):
        self.root = temp_root(self)
        self.enterContext(_RIGHTS_PASS)

    def test_honest_corpus_integrates_and_promotes(self):
        fixture = GateFixture(self.root)
        self.assertEqual(fixture.integrate(), 0)
        manifest = fixture.manifest()
        self.assertTrue(manifest["gates"]["factory_label"]["passed"])
        self.assertTrue(manifest["training_ready"])
        review = fixture.accepted_review()
        code, report, stderr = fixture.promote_report(review)
        self.assertEqual(code, 0, stderr)
        self.assertTrue(report["promoted"])

    def test_meta_factory_mismatch_fails_integrate_and_does_not_promote(self):
        records = [_thalamic("t-1"), _preference(), _episode()]
        records[0]["meta"]["factory"] = "bridge-factory"
        fixture = GateFixture(self.root, thalamic_records=records)
        self.assertEqual(fixture.integrate(), 1)
        manifest = fixture.manifest()
        gate = manifest["gates"]["factory_label"]
        self.assertFalse(gate["passed"])
        self.assertEqual(gate["examples"][0]["meta_factory"], ["bridge-factory"])
        self.assertEqual(gate["examples"][0]["path_factory"], "thalamic-mini")
        self.assertFalse(manifest["training_ready"])
        self.assertIn(f"{factory_label.FACTORY_LABEL_MISMATCH}:1", manifest["blockers"])
        review = fixture.accepted_review()
        code, report, stderr = fixture.promote_report(review)
        self.assertEqual(code, 1, stderr)
        self.assertFalse(report["promoted"])
        self.assertTrue(
            any(
                blocker.startswith(f"{factory_label.FACTORY_LABEL_MISMATCH}:")
                for blocker in report["blockers"]
            )
        )


if __name__ == "__main__":
    unittest.main()
