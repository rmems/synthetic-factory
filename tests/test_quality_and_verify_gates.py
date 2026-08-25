#!/usr/bin/env python3
"""Regression tests for the quality and execution gates.

Both gates run over untrusted generated JSONL, so malformed records must
produce a verdict rather than an exception, and provenance must be counted
from whichever field carries it.
"""

import copy
import json
import random
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import quality_gate  # noqa: E402
import verify_execution  # noqa: E402

EMBEDDING_FIXTURE = REPO / "tests" / "fixtures" / "embedding-dedup"

# Distinct enough that no pair is a near-duplicate, so a mix test blocks on the
# mix and nothing else.
DISTINCT_NOTES = [
    "the harbour crane lost hoist encoder agreement under a loaded spreader",
    "chlorine residual fell at the far zone sample point during full duty",
    "a feeder breaker tripped on instantaneous overcurrent mid reclose",
    "the vaccine freezer bank drifted upward after a defrost heater stuck",
    "turbine pitch bearing grease pressure spiked under yaw misalignment",
    "the milking robot logged a partial rinse against standing procedure",
]


def write(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def mix_records(synthetic, real):
    """``synthetic`` designed records and ``real`` unknown ones, all distinct."""
    kinds = ["designed"] * synthetic + ["unknown"] * real
    return [
        {"id": f"m-{index}", "state": {"sim_or_real": kind, "note": DISTINCT_NOTES[index]}}
        for index, kind in enumerate(kinds)
    ]


class QualityGate(unittest.TestCase):
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


class ExactDedup(unittest.TestCase):
    def test_exact_duplicate_is_excluded_with_a_reason(self):
        record = {"id": "a", "state": {"sim_or_real": "unknown", "note": DISTINCT_NOTES[0]}}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [record, {**record, "id": "b"}])
            report = quality_gate.audit_run(root)

        self.assertTrue(report["blocked"])
        self.assertEqual(len(report["duplicates"]), 1)
        duplicate = report["duplicates"][0]
        # Legacy report shape (file/line/hash) must survive.
        self.assertEqual(duplicate["file"], "batch.jsonl")
        self.assertEqual(duplicate["line"], 2)
        self.assertTrue(duplicate["hash"])
        self.assertEqual(duplicate["kind"], "exact")
        self.assertIn("already seen at batch.jsonl:1", duplicate["reason"])
        clusters = [c for c in report["duplicate_clusters"] if c["kind"] == "exact"]
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["size"], 2)
        self.assertEqual(clusters[0]["representative"], {"file": "batch.jsonl", "line": 1})
        self.assertEqual(report["counts"]["excluded_records"], 1)


class EmbeddingDedup(unittest.TestCase):
    """The fixture holds one near-duplicate pair that exact hashing cannot see."""

    def test_fixture_near_duplicate_is_excluded_with_a_reason(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE)

        self.assertEqual(report["counts"]["total"], 7)
        # Exact hashing sees nothing: the pair differs inside the dedup view.
        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertTrue(report["blocked"])
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertEqual(report["counts"]["excluded_records"], 1)

        duplicate = report["duplicates"][0]
        self.assertEqual(duplicate["kind"], "embedding")
        self.assertEqual(duplicate["file"], "batch-r01.jsonl")
        # Line 1 is the representative that is kept; line 2 is excluded.
        self.assertEqual(duplicate["line"], 2)
        self.assertEqual(duplicate["duplicate_of"], {"file": "batch-r01.jsonl", "line": 1})
        self.assertGreater(duplicate["similarity"], quality_gate.DEFAULT_EMBEDDING_THRESHOLD)
        self.assertIn("embedding near-duplicate", duplicate["reason"])
        self.assertIn("cosine", duplicate["reason"])

        cluster = [c for c in report["duplicate_clusters"] if c["kind"] == "embedding"][0]
        self.assertEqual(cluster["size"], 2)
        self.assertEqual(cluster["encoder"], quality_gate.EMBEDDING_ENCODER)
        self.assertEqual(cluster["representative"], {"file": "batch-r01.jsonl", "line": 1})
        self.assertIn(
            f"{len(report['blockers'])} embedding near-duplicate record(s)",
            " ".join(report["blockers"]),
        )

    def test_distinct_fixture_records_are_not_flagged(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE)
        excluded = {(d["file"], d["line"]) for d in report["duplicates"]}
        # Every record other than the planted near-duplicate survives.
        self.assertEqual(excluded, {("batch-r01.jsonl", 2)})
        self.assertEqual(report["embedding"]["compared_records"], 7)

    def test_result_is_deterministic(self):
        first = quality_gate.audit_run(EMBEDDING_FIXTURE)
        second = quality_gate.audit_run(EMBEDDING_FIXTURE)
        self.assertEqual(first, second)

    def test_raising_the_threshold_above_the_pair_unblocks(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=0.999)
        self.assertFalse(report["blocked"])
        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["threshold"], 0.999)

    def test_embedding_pass_can_be_disabled(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE, embedding_dedup=False)
        self.assertFalse(report["blocked"])
        self.assertEqual(report["duplicates"], [])
        self.assertFalse(report["embedding"]["enabled"])
        self.assertIn(
            "embedding dedup disabled — only exact-hash duplicates were excluded",
            report["warnings"],
        )

    def test_candidate_cap_is_not_truncated_when_exactly_full(self):
        report = quality_gate.audit_run(EMBEDDING_FIXTURE, max_embedding_pairs=1)
        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertFalse(report["embedding"]["truncated"])
        self.assertFalse(any("recall is partial" in w for w in report["warnings"]))

    def test_candidate_cap_reports_only_when_an_extra_pair_is_omitted(self):
        signature = tuple(range(quality_gate.EMBEDDING_MINHASH_SLOTS))
        pairs, truncated = quality_gate._candidate_pairs(
            [(0, signature), (1, signature), (2, signature)], max_pairs=1
        )
        self.assertEqual(len(pairs), 1)
        self.assertTrue(truncated)

    def test_field_paths_distinguish_equal_values_under_different_keys(self):
        records = [
            {"state": {"sim_or_real": "unknown", "pressure_status": "critical"}},
            {"state": {"sim_or_real": "unknown", "temperature_status": "critical"}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertNotEqual(
            quality_gate.embedding_tokens(records[0]),
            quality_gate.embedding_tokens(records[1]),
        )
        self.assertEqual(report["duplicates"], [])

    def test_mapping_insertion_order_does_not_change_embedding_tokens(self):
        keys = [f"field_{index:03d}" for index in range(120)]
        forward = {key: f"value_{index:03d}" for index, key in enumerate(keys)}
        reverse = {
            key: f"value_{index:03d}"
            for index, key in reversed(list(enumerate(keys)))
        }
        self.assertEqual(
            quality_gate.embedding_tokens({"state": forward}),
            quality_gate.embedding_tokens({"state": reverse}),
        )

        reverse[keys[60]] = "one_minor_change"
        records = [{"state": forward}, {"state": reverse}]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )

    def test_unicode_text_is_preserved_in_embedding_tokens(self):
        records = [
            {"state": {"sim_or_real": "unknown", "note": "冷却水温度上昇"}},
            {"state": {"sim_or_real": "unknown", "note": "港口起重机故障"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertTrue(any("冷却水温度上昇" in token for token in token_sets[0]))
        self.assertTrue(any("港口起重机故障" in token for token in token_sets[1]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["duplicates"], [])

    def test_transitive_cluster_points_every_exclusion_at_retained_record(self):
        common = " ".join(f"common_{index:03d}" for index in range(80))
        records = [
            {"state": {"note": common + " alpha alpha"}},
            {"state": {"note": common + " alpha beta"}},
            {"state": {"note": common + " beta beta"}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root, threshold=0.90)

        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertEqual(len(report["duplicates"]), 2)
        for duplicate in report["duplicates"]:
            self.assertEqual(
                duplicate["duplicate_of"], {"file": "batch.jsonl", "line": 1}
            )
        self.assertEqual(
            report["duplicates"][1]["matched_with"],
            {"file": "batch.jsonl", "line": 2},
        )
        self.assertIn("linked by cosine", report["duplicate_clusters"][0]["reason"])

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=1.5)

    def test_planted_duplicates_are_all_recovered(self):
        """LSH banding may only cost recall, so guard it with planted clones.

        Each clone differs from its source only in ``state.tick`` — invisible
        to exact hashing, ~0.99 cosine to the encoder.
        """
        rng = random.Random(20260823)
        vocabulary = [f"w{index}" for index in range(600)]
        records = [
            {
                "id": f"p-{index}",
                "state": {
                    "sim_or_real": "designed",
                    "tick": index,
                    "observation": " ".join(rng.choice(vocabulary) for _ in range(120)),
                },
            }
            for index in range(120)
        ]
        planted = set()
        for index in rng.sample(range(len(records)), 12):
            clone = copy.deepcopy(records[index])
            clone["id"] = f"p-{index}-clone"
            clone["state"]["tick"] = 900000 + index
            planted.add(clone["id"])
            records.append(clone)
        rng.shuffle(records)
        identifiers = [record["id"] for record in records]

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(
                root, mix_policy=quality_gate.MixPolicy(max_synthetic_ratio=1.0)
            )

        # Exact hashing sees none of them.
        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], len(planted))
        flagged = {identifiers[d["line"] - 1] for d in report["duplicates"]}
        self.assertEqual(len(flagged), len(planted))
        # Every flagged record is either a clone or the source it was cloned
        # from — nothing unrelated was swept in.
        for identifier in flagged:
            self.assertTrue(
                identifier in planted or f"{identifier}-clone" in planted,
                f"unexpected exclusion: {identifier}",
            )


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


class VerifyExecution(unittest.TestCase):
    def test_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution.verify_thalamic("a string", "where")
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)

    def test_non_string_rationale_does_not_raise(self):
        status, _ = verify_execution.verify_thalamic(
            {
                "state": {"sim_or_real": "designed"},
                "safety_decision": {"rationale": {"nested": "object"}},
                "future_outcome": {},
            },
            "where",
        )
        self.assertEqual(status, "failed")

    def test_bridge_with_non_object_trajectory_returns_verdict(self):
        status, reason = verify_execution.verify_record_execution(
            {"language_view": {"trajectory": "oops"}, "spike_events": [1]},
            "where",
        )
        self.assertEqual(status, "inconclusive")
        self.assertIn("not an object", reason)


if __name__ == "__main__":
    unittest.main()
