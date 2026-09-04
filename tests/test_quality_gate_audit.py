#!/usr/bin/env python3
"""Audit, mix-policy, manifest, and reward-shape quality-gate tests."""

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import write  # noqa: E402
from quality_gate_test_support import (  # noqa: E402
    DISTINCT_NOTES,
    EMBEDDING_FIXTURE,
    mix_records,
)
import quality_gate  # noqa: E402
from exact_json import MAX_JSON_NESTING_DEPTH  # noqa: E402

class QualityGate(unittest.TestCase):
    def test_exact_valid_source_depth_is_not_expanded_past_identity_limit(self):
        identity_depth = MAX_JSON_NESTING_DEPTH // 2 + 1
        nested = "[" * identity_depth + "0" + "]" * identity_depth
        payload = (
            '{"id":"deep","state":{"sim_or_real":"real","extension":'
            + nested
            + "}}\n"
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "batch.jsonl").write_text(payload, encoding="utf-8")

            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["total"], 1)
        self.assertEqual(report["counts"]["malformed_lines"], 0)
        self.assertEqual(report["counts"]["unique_hashes"], 1)

    def test_source_beyond_exact_depth_limit_remains_malformed(self):
        nested = "[" * (MAX_JSON_NESTING_DEPTH + 1) + "0" + "]" * (
            MAX_JSON_NESTING_DEPTH + 1
        )
        payload = (
            '{"id":"too-deep","state":{"sim_or_real":"real","extension":'
            + nested
            + "}}\n"
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "batch.jsonl").write_text(payload, encoding="utf-8")

            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(report["counts"]["malformed_lines"], 1)
        self.assertIn(
            "JSON nesting",
            report["errors"]["malformed_examples"][0]["error"],
        )

    def test_record_hash_survives_malformed_preference_records(self):
        for malformed in (
            {"chosen": {"state": {"a": 1}}},           # no rejected side
            {"chosen": "not-an-object", "rejected": None},
            {"chosen": {}, "rejected": 5},
        ):
            digest = quality_gate.record_hash(malformed)
            self.assertIsInstance(digest, str)
            self.assertTrue(digest)

    def test_provenance_counts_sim_or_real_without_top_level_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "f" / "batch.jsonl", [
                {"id": "a", "state": {"sim_or_real": "designed"}},
                {"id": "b", "state": {"sim_or_real": "simulated"}},
            ])
            report = quality_gate.audit_run(root)

        mix = report["mix"] if "mix" in report else report
        self.assertEqual(mix["provenance"].get("designed"), 1)
        self.assertEqual(mix["provenance"].get("simulated"), 1)
        self.assertEqual(mix["synthetic"], 2)

    def test_provenance_falls_back_to_top_level_kind(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "f" / "batch.jsonl", [
                {"id": "a", "state": {}, "provenance": {"kind": "hil"}},
            ])
            report = quality_gate.audit_run(root)

        mix = report["mix"] if "mix" in report else report
        self.assertEqual(mix["provenance"].get("hil"), 1)

    def test_non_object_line_does_not_crash_provenance_counting(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [["not", "an", "object"], 7, "loose string"])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["total"], 3)
        self.assertEqual(report["mix"]["unlabeled"], 3)

    def test_bare_cr_does_not_create_two_valid_quality_gate_records(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "batch.jsonl"
            path.write_bytes(b'{"id":"first"}\r{"id":"second"}\n')

            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["total"], 0)
        self.assertEqual(report["counts"]["malformed_lines"], 1)
        self.assertTrue(report["blocked"])

    def test_preference_side_provenance_counts_once_per_pair(self):
        pair = {
            # A promoted wrapper can carry a generic top-level unknown stamp;
            # the shared side provenance is the record's meaningful label.
            "provenance": {"kind": "unknown"},
            "chosen": {
                "state": {"sim_or_real": "designed", "note": "preferred"},
            },
            "rejected": {
                "state": {"sim_or_real": "designed", "note": "unsafe"},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "preferences.jsonl", [pair])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["mix"]["synthetic"], 1)
        self.assertEqual(report["mix"]["unlabeled"], 0)
        self.assertEqual(report["mix"]["provenance"], {"designed": 1})
        self.assertTrue(report["blocked"])
        self.assertTrue(any("synthetic_ratio 1.00" in b for b in report["blockers"]))

    def test_bridge_trajectory_provenance_precedes_wrapper_unknown(self):
        bridge = {
            "provenance": {"kind": "unknown"},
            "language_view": {
                "trajectory": {"state": {"sim_or_real": "hil", "note": "rig"}},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "bridges.jsonl", [bridge])
            report = quality_gate.audit_run(root)

        self.assertEqual(report["mix"]["provenance"], {"hil": 1})
        self.assertEqual(report["mix"]["synthetic"], 1)

    def test_stateless_factory_record_is_counted_as_designed(self):
        record = {
            "id": "agentic-1",
            "goal": "repair the queue consumer without dropping work",
            "steps": [],
            "outcome": "recovered",
            "meta": {"factory": "agentic-coding-trajectory-factory"},
            "provenance": {"kind": "unknown", "claimed": None},
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "episodes.jsonl", [record])
            report = quality_gate.audit_run(
                root,
                mix_policy=quality_gate.MixPolicy(max_synthetic_ratio=1.0),
            )

        self.assertEqual(report["mix"]["provenance"], {"designed": 1})
        self.assertEqual(report["mix"]["synthetic"], 1)
        self.assertEqual(report["mix"]["unlabeled"], 0)


class MixEnforcement(unittest.TestCase):
    def test_mix_outside_policy_blocks_instead_of_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=3, real=1))
            report = quality_gate.audit_run(root)

        self.assertAlmostEqual(report["mix"]["synthetic_ratio"], 0.75)
        self.assertTrue(report["blocked"])
        self.assertTrue(any("synthetic_ratio 0.75" in b for b in report["blockers"]))
        self.assertEqual(report["duplicates"], [])

    def test_mix_inside_tolerance_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=2, real=3))
            report = quality_gate.audit_run(root)

        self.assertAlmostEqual(report["mix"]["synthetic_ratio"], 0.4)
        self.assertFalse(report["blocked"])
        self.assertTrue(any("synthetic_ratio 0.40" in w for w in report["warnings"]))

    def test_mix_on_target_is_silent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            report = quality_gate.audit_run(root)

        self.assertAlmostEqual(report["mix"]["synthetic_ratio"], 0.2)
        self.assertFalse(report["blocked"])
        self.assertEqual(report["warnings"], [])

    def test_ceiling_is_configurable(self):
        policy = quality_gate.MixPolicy(max_synthetic_ratio=0.9)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=3, real=1))
            report = quality_gate.audit_run(root, mix_policy=policy)

        self.assertFalse(report["blocked"])
        self.assertEqual(report["mix_policy"]["max_synthetic_ratio"], 0.9)

    def test_default_policy_is_thirty_seventy_and_blocking(self):
        policy = quality_gate.MixPolicy()
        self.assertEqual(policy.target, 0.30)
        self.assertEqual(policy.ceiling, 0.50)
        self.assertTrue(policy.as_dict()["blocking"])

    def test_optional_floor_blocks_a_corpus_with_too_little_synthetic(self):
        policy = quality_gate.MixPolicy(min_synthetic_ratio=0.25)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", mix_records(synthetic=0, real=5))
            report = quality_gate.audit_run(root, mix_policy=policy)

        self.assertTrue(report["blocked"])
        self.assertTrue(any("floor 0.25" in b for b in report["blockers"]))

    def test_unlabeled_records_are_reported_and_can_block(self):
        records = [
            {"id": f"u-{i}", "state": {"note": DISTINCT_NOTES[i]}} for i in range(4)
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            warn_only = quality_gate.audit_run(root)
            blocking = quality_gate.audit_run(
                root, mix_policy=quality_gate.MixPolicy(max_unlabeled_ratio=0.5)
            )

        self.assertEqual(warn_only["mix"]["unlabeled_ratio"], 1.0)
        self.assertFalse(warn_only["blocked"])
        self.assertTrue(any("unlabeled_ratio" in w for w in warn_only["warnings"]))
        self.assertTrue(blocking["blocked"])
        self.assertTrue(any("unlabeled_ratio 1.00" in b for b in blocking["blockers"]))

    def test_unsatisfiable_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            quality_gate.MixPolicy(min_synthetic_ratio=0.9).validate()
        with self.assertRaises(ValueError):
            quality_gate.MixPolicy(target=2.0).validate()

    def test_empty_run_does_not_block_on_mix(self):
        with tempfile.TemporaryDirectory() as td:
            report = quality_gate.audit_run(Path(td))
        self.assertEqual(report["counts"]["total"], 0)
        self.assertFalse(report["blocked"])

    def test_empty_run_blocks_when_a_synthetic_floor_is_configured(self):
        with tempfile.TemporaryDirectory() as td:
            report = quality_gate.audit_run(
                Path(td),
                mix_policy=quality_gate.MixPolicy(min_synthetic_ratio=0.1),
            )
        self.assertTrue(report["blocked"])
        self.assertTrue(any("floor 0.10" in blocker for blocker in report["blockers"]))


class CuratedManifest(unittest.TestCase):
    def run_cli(self, argv):
        """Run the CLI quietly and return its exit code."""
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as caught:
                quality_gate.main(argv)
        return caught.exception.code

    def test_manifest_carries_mix_ratio_and_duplicate_report(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "curated" / "quality-manifest.json"
            code = self.run_cli(
                [str(EMBEDDING_FIXTURE), "--json", "--manifest", str(manifest_path)]
            )
            self.assertEqual(code, 1)
            manifest = json.loads(manifest_path.read_text())

        self.assertEqual(manifest["schema"], "quality-manifest/1")
        self.assertEqual(manifest["run_dir"], str(EMBEDDING_FIXTURE))
        self.assertIn("synthetic_ratio", manifest["mix"])
        self.assertEqual(manifest["mix_policy"]["max_synthetic_ratio"], 0.5)
        self.assertEqual(len(manifest["duplicate_clusters"]), 1)
        self.assertEqual(manifest["duplicate_clusters"][0]["kind"], "embedding")
        self.assertTrue(manifest["duplicates"][0]["reason"])
        self.assertIn("unique_shapes", manifest["reward_shapes"])

    def test_cli_exits_zero_on_a_clean_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            self.assertEqual(self.run_cli([str(root)]), 0)

    def test_cli_rejects_an_unsatisfiable_policy(self):
        code = self.run_cli([str(EMBEDDING_FIXTURE), "--min-synthetic-ratio", "0.9"])
        self.assertEqual(code, 2)

    def test_cli_rejects_missing_run_without_writing_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "missing-run"
            manifest = root / "curated" / "quality-manifest.json"
            code = self.run_cli([str(missing), "--manifest", str(manifest)])
            self.assertEqual(code, 2)
            self.assertFalse(manifest.exists())

    def test_cli_refuses_to_overwrite_an_audited_jsonl_with_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            batch = root / "batch.jsonl"
            write(batch, mix_records(synthetic=1, real=4))
            before = batch.read_bytes()

            code = self.run_cli([str(root), "--manifest", str(batch)])

            self.assertEqual(code, 2)
            self.assertEqual(batch.read_bytes(), before)

    def test_cli_refuses_existing_or_in_run_manifest_targets(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "run"
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            existing = base / "existing.json"
            existing.write_text("sentinel\n")

            existing_code = self.run_cli(
                [str(root), "--manifest", str(existing)]
            )
            in_run = root / "quality-manifest.json"
            in_run_code = self.run_cli([str(root), "--manifest", str(in_run)])

            self.assertEqual(existing_code, 2)
            self.assertEqual(existing.read_text(), "sentinel\n")
            self.assertEqual(in_run_code, 2)
            self.assertFalse(in_run.exists())

    def test_cli_does_not_write_a_manifest_unless_asked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            write(root / "batch.jsonl", mix_records(synthetic=1, real=4))
            self.assertEqual(self.run_cli([str(root)]), 0)
            self.assertEqual([p.name for p in sorted(root.iterdir())], ["batch.jsonl"])


class RewardShapeReport(unittest.TestCase):
    def test_reward_vocabulary_is_reported_not_blocked(self):
        records = [
            {"id": "r-0", "state": {"sim_or_real": "unknown", "note": DISTINCT_NOTES[0]},
             "reward_components": {"process": 0.1, "world": -0.2}},
            {"id": "r-1", "state": {"sim_or_real": "unknown", "note": DISTINCT_NOTES[1]},
             "reward_components": {"process": 0.3, "latency_ms": 12}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        rewards = report["reward_shapes"]
        self.assertEqual(rewards["records_with_reward_components"], 2)
        self.assertEqual(rewards["unique_component_keys"], 3)
        self.assertEqual(rewards["unique_shapes"], 2)
        self.assertFalse(report["blocked"])


if __name__ == "__main__":
    unittest.main()
