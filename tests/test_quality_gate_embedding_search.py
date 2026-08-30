#!/usr/bin/env python3
"""Candidate search, clustering, and threshold tests for embedding dedup."""

import copy
import random
import sys
import tempfile
import unittest
import weakref
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import write  # noqa: E402
from quality_gate_test_support import (  # noqa: E402
    DISTINCT_NOTES,
    EMBEDDING_FIXTURE,
)
import quality_gate  # noqa: E402
import quality_gate_embedding  # noqa: E402


def _planted_record(rng, vocabulary, index):
    """Build one deterministic high-dimensional source record."""
    observation = " ".join(rng.choice(vocabulary) for _ in range(120))
    return {
        "id": f"p-{index}",
        "state": {
            "sim_or_real": "designed",
            "tick": index,
            "observation": observation,
        },
    }


def _base_planted_records(rng, vocabulary):
    """Build the source corpus for the planted-recall regression."""
    return [_planted_record(rng, vocabulary, index) for index in range(120)]


def _add_planted_clones(rng, records):
    """Append twelve exact-identity-distinct semantic clones."""
    planted = set()
    for index in rng.sample(range(len(records)), 12):
        clone = copy.deepcopy(records[index])
        clone["id"] = f"p-{index}-clone"
        clone["state"]["tick"] = 900000 + index
        planted.add(clone["id"])
        records.append(clone)
    return planted


def _planted_duplicate_corpus():
    """Return shuffled records and the identifiers of their planted clones."""
    rng = random.Random(20260823)
    vocabulary = [f"w{index}" for index in range(600)]
    records = _base_planted_records(rng, vocabulary)
    planted = _add_planted_clones(rng, records)
    rng.shuffle(records)
    return records, planted


class EmbeddingDedupSearch(unittest.TestCase):
    """Near-duplicate search must be deterministic, bounded, and fail closed."""

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

    def test_candidate_truncation_blocks_the_audit(self):
        records = [
            {
                "id": f"coding-{index}",
                "goal": "repair the same queue consumer and verify every retry",
                # Distinct modeled outcomes keep exact-hash identity apart so
                # the embedding pass still sees three near-duplicate records.
                "outcome": f"retry-pass-{index}",
            }
            for index in range(3)
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "episodes.jsonl", records)
            report = quality_gate.audit_run(root, max_embedding_pairs=1)

        self.assertTrue(report["embedding"]["truncated"])
        self.assertTrue(report["blocked"])
        self.assertTrue(
            any("cannot be certified" in blocker for blocker in report["blockers"])
        )

    def test_corpus_idf_is_released_before_the_pair_phase(self):
        """idf spans the whole corpus vocabulary and its last read is the
        vector loop. It must not stay resident while _candidate_pairs
        materializes pairs and the cosine loop scores them, which is where the
        largest structures are allocated (mergestorm #98, quality_gate.py:731).

        The probe is an object owned only by the idf dict, so its weakref dies
        exactly when idf is released.
        """
        class Probe:
            """Weak-referenceable stand-in; a plain dict cannot be weakref'd."""

        seen = {}
        real_vector = quality_gate_embedding._tfidf_vector
        real_pairs = quality_gate_embedding._candidate_pairs

        def spy_vector(tokens, idf):
            if "probe" not in seen:
                probe = Probe()
                # Never looked up: _tfidf_vector only indexes record tokens.
                idf["\x00idf-liveness-probe"] = probe
                seen["probe"] = weakref.ref(probe)
            return real_vector(tokens, idf)

        def spy_pairs(signatures, max_pairs):
            seen["alive_at_pair_phase"] = seen["probe"]() is not None
            return real_pairs(signatures, max_pairs)

        records = [
            {"id": f"idf-{index}", "state": {"note": note}}
            for index, note in enumerate(DISTINCT_NOTES)
        ]
        with mock.patch.object(quality_gate_embedding, "_tfidf_vector", spy_vector), \
                mock.patch.object(quality_gate_embedding, "_candidate_pairs", spy_pairs):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                write(root / "batch.jsonl", records)
                quality_gate.audit_run(root)

        self.assertIn("alive_at_pair_phase", seen)
        self.assertFalse(seen["alive_at_pair_phase"])

    def test_frequency_aware_sketch_recalls_high_tf_cosine_pair(self):
        repeated = "saturated " * 2000
        records = [
            {"id": "tf-a", "goal": repeated + "alpha"},
            {"id": "tf-b", "goal": repeated + "beta"},
        ]
        token_sets = [set(quality_gate.embedding_tokens(record)) for record in records]
        unweighted_jaccard = len(token_sets[0] & token_sets[1]) / len(
            token_sets[0] | token_sets[1]
        )
        # Premise for this regression: on the raw token *set* these two
        # records overlap only half, and 8 bands of 4 recall an overlap
        # that weak barely 40% of the time. The frequency-aware tier
        # sketch is what turns the 2000 repeats into a reliable candidate;
        # the exact cosine asserted below is far above this set overlap.
        self.assertLessEqual(unweighted_jaccard, 0.5)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "episodes.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertEqual(report["embedding"]["candidate_sketch"], "weighted-tier-minhash/2")
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )
        self.assertLess(
            unweighted_jaccard, report["duplicates"][0]["similarity"]
        )

    def test_nonchain_only_candidate_fallback_is_isolated(self):
        boundary = next(
            iter(quality_gate.embedding_tokens({"state": {"note": " "}}))
        )
        lexical = next(
            token
            for token in quality_gate.embedding_tokens(
                {"state": {"note": "customer"}}
            )
            if not token.startswith(
                quality_gate_embedding._NONCHAIN_STRING_MARK
            )
        )

        self.assertIsNotNone(
            quality_gate_embedding._candidate_signature({boundary: 1.0})
        )
        self.assertIsNone(quality_gate_embedding._candidate_signature({}))
        self.assertEqual(
            quality_gate_embedding._candidate_signature(
                {lexical: 1.0, boundary: 0.5}
            ),
            quality_gate_embedding._candidate_signature({lexical: 1.0}),
        )

    def test_empty_and_nonchain_only_semantic_clones_are_nominated(self):
        cases = {
            "empty state after identifier stripping": {},
            "empty string": {"note": ""},
            "whitespace-only string": {"note": " "},
        }
        for label, payload in cases.items():
            with self.subTest(case=label):
                records = [
                    {"state": {"episode_id": "episode-a", **payload}},
                    {"state": {"episode_id": "episode-b", **payload}},
                ]
                self.assertNotEqual(
                    quality_gate.record_hash(records[0]),
                    quality_gate.record_hash(records[1]),
                )
                self.assertEqual(
                    quality_gate.semantic_similarity_view(records[0]),
                    quality_gate.semantic_similarity_view(records[1]),
                )

                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    write(root / "batch.jsonl", records)
                    report = quality_gate.audit_run(root)

                self.assertEqual(report["counts"]["duplicate_groups"], 0)
                self.assertEqual(report["embedding"]["candidate_pairs"], 1)
                self.assertEqual(
                    report["counts"]["embedding_duplicate_groups"], 1
                )
                self.assertEqual(report["duplicates"][0]["kind"], "embedding")

    def test_semantic_view_removes_top_level_and_episode_ids(self):
        common = "verify queue retries and preserve every acknowledged work item"
        stateless = [
            {
                "id": "coding-a",
                "goal": common,
                "meta": {"round": 1, "factory": "agentic-coding-trajectory-factory"},
            },
            {
                "id": "coding-b",
                "goal": common,
                "meta": {"round": 2, "factory": "agentic-coding-trajectory-factory"},
            },
        ]
        self.assertEqual(
            quality_gate.exact_identity_view(stateless[0]),
            quality_gate.exact_identity_view(stateless[1]),
        )
        self.assertEqual(
            quality_gate.semantic_similarity_view(stateless[0]),
            quality_gate.semantic_similarity_view(stateless[1]),
        )
        records = [
            {
                "id": "wrapper-a",
                "state": {
                    "episode_id": "episode-a",
                    "sim_or_real": "unknown",
                    "note": common,
                },
                "meta": {"round": 1, "factory": "thalamic-trajectory-factory"},
            },
            {
                "id": "wrapper-b",
                "state": {
                    "episode_id": "episode-b",
                    "sim_or_real": "unknown",
                    "note": common,
                },
                "meta": {"round": 2, "factory": "thalamic-trajectory-factory"},
            },
        ]
        self.assertNotEqual(quality_gate.record_hash(records[0]), quality_gate.record_hash(records[1]))
        self.assertEqual(
            quality_gate.semantic_similarity_view(records[0]),
            quality_gate.semantic_similarity_view(records[1]),
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["counts"]["duplicate_groups"], 0)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)

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

    def test_threshold_one_is_rejected_instead_of_disabling_dedup(self):
        with self.assertRaisesRegex(ValueError, r"1\)"):
            quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=1.0)

    def test_negative_thresholds_are_rejected_not_silently_under_reported(self):
        """TF-IDF weights here are strictly positive, so every cosine is in
        [0, 1] and a negative threshold declares every pair a near-duplicate --
        including disjoint-vocabulary pairs the LSH candidate scheme never
        proposes. Scoring only candidates would exit clean while failing the
        configured policy, so the range excludes it (Codex #98)."""
        for threshold in (-0.5, -1.0, -0.000001):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    quality_gate.audit_run(EMBEDDING_FIXTURE, threshold=threshold)

    def test_the_floor_is_the_banding_knee_not_zero(self):
        """Zero was accepted as the floor on the premise that a pair the LSH
        scheme never nominates has cosine 0 anyway. That premise only covers
        *disjoint* pairs. A pair that shares a little vocabulary has a positive
        cosine and, at threshold 0, must be excluded -- but it can still share
        no band and never be scored, so the gate exits clean while failing the
        policy it was handed. The floor is therefore the banding S-curve knee,
        below which nomination is not dependable (Codex #98)."""
        self.assertAlmostEqual(quality_gate.EMBEDDING_MIN_THRESHOLD, 0.5946, places=4)

        records = [
            {"goal": "shared a0", "outcome": "left"},
            {"goal": "shared b0", "outcome": "right"},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)

            for threshold in (0.0, 0.25, quality_gate.EMBEDDING_MIN_THRESHOLD - 1e-6):
                with self.subTest(threshold=threshold):
                    with self.assertRaises(ValueError):
                        quality_gate.audit_run(root, threshold=threshold)

            # The knee itself, and anything above it, is accepted.
            report = quality_gate.audit_run(
                root, threshold=quality_gate.EMBEDDING_MIN_THRESHOLD
            )

        self.assertEqual(report["threshold"], quality_gate.EMBEDDING_MIN_THRESHOLD)

    def test_a_pair_below_the_knee_is_the_reason_zero_cannot_be_honoured(self):
        """The evidence behind the bound: these two records share vocabulary,
        so their cosine is positive and threshold 0 would have to exclude one,
        yet they share no LSH band and are never nominated for scoring."""
        records = [
            {"goal": "shared a0", "outcome": "left"},
            {"goal": "shared b0", "outcome": "right"},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(
                root, threshold=quality_gate.EMBEDDING_MIN_THRESHOLD
            )

        self.assertEqual(report["embedding"]["compared_records"], 2)
        self.assertEqual(report["embedding"]["candidate_pairs"], 0)
        self.assertEqual(report["duplicates"], [])

    def test_planted_duplicates_are_all_recovered(self):
        """LSH banding may only cost recall, so guard it with planted clones.

        Each clone differs from its source only in ``state.tick`` — invisible
        to exact hashing, ~0.99 cosine to the encoder.
        """
        records, planted = _planted_duplicate_corpus()
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


if __name__ == "__main__":
    unittest.main()
