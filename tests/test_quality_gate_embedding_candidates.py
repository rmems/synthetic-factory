#!/usr/bin/env python3
"""Candidate-channel and bounded-search regressions for embedding dedup."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import write  # noqa: E402
import quality_gate  # noqa: E402
import quality_gate_embedding  # noqa: E402


def _vectors(records):
    token_rows = [
        {"tokens": quality_gate.embedding_tokens(record)}
        for record in records
    ]
    idf = quality_gate_embedding._corpus_idf(
        token_rows, range(len(token_rows))
    )
    return [
        quality_gate_embedding._tfidf_vector(row["tokens"], idf)
        for row in token_rows
    ]


def _lexical_signatures(vectors):
    return [
        (
            index,
            quality_gate_embedding._minhash_signature(
                quality_gate.candidate_sketch_features(vector)
            ),
        )
        for index, vector in enumerate(vectors)
    ]


class EmbeddingCandidateChannels(unittest.TestCase):
    def _audit(self, records, **options):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            return quality_gate.audit_run(root, **options)

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

    def test_boundary_dominated_mixed_vectors_are_nominated(self):
        records = []
        for task in ("repair alpha", "repair beta"):
            state = {f"padding_{index}": " " for index in range(8)}
            state["task"] = task
            records.append({"state": state})

        self.assertEqual(
            quality_gate_embedding._candidate_pairs(
                _lexical_signatures(_vectors(records)), 10
            ),
            ([], False),
        )
        report = self._audit(records, threshold=0.6)

        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertGreater(report["duplicates"][0]["similarity"], 0.6)

    def test_any_nonchain_evidence_gets_a_combined_channel(self):
        boundary = f"{quality_gate_embedding._NONCHAIN_STRING_MARK}boundary"
        mixed = {boundary: 0.01, "lexical": 1.0}
        boundary_only = {boundary: 1.0}

        self.assertEqual(
            set(dict(quality_gate_embedding._candidate_signatures(mixed))),
            {"lexical", "combined"},
        )
        self.assertEqual(
            set(dict(quality_gate_embedding._candidate_signatures(boundary_only))),
            {"combined"},
        )
        self.assertEqual(
            set(
                dict(
                    quality_gate_embedding._candidate_signatures(
                        {"lexical": 1.0}
                    )
                )
            ),
            {"lexical"},
        )

    def test_candidate_pairs_canonicalize_adversarial_signature_entries(self):
        signature_a = tuple(range(quality_gate.EMBEDDING_MINHASH_SLOTS))
        signature_b = tuple(
            value + 1000
            for value in range(quality_gate.EMBEDDING_MINHASH_SLOTS)
        )

        self.assertEqual(
            quality_gate_embedding._candidate_pairs(
                [(0, signature_a), (0, signature_a)], 10
            ),
            ([], False),
        )
        reordered = [
            (1, "lexical", signature_a),
            (0, "lexical", signature_a),
            (0, "lexical", signature_b),
            (1, "lexical", signature_b),
        ]
        self.assertEqual(
            quality_gate_embedding._candidate_pairs(reordered, 10),
            ([(0, 1)], False),
        )

    def test_candidate_cap_is_independent_of_signature_input_order(self):
        signature = tuple(range(quality_gate.EMBEDDING_MINHASH_SLOTS))
        orders = (
            [0, 1, 2],
            [2, 1, 0],
            [1, 2, 0],
        )

        results = []
        for order in orders:
            pairs, truncated = quality_gate_embedding._candidate_pairs(
                [(index, signature) for index in order], 1
            )
            results.append((tuple(pairs), truncated))

        self.assertEqual(results, [(((0, 1),), True)] * len(orders))

    def test_combined_channel_candidate_cap_remains_fail_closed(self):
        records = []
        for task in ("alpha", "ALPHA", "Alpha"):
            state = {f"padding_{index}": " " for index in range(8)}
            state["task"] = task
            records.append({"state": state})

        report = self._audit(records, threshold=0.6, max_embedding_pairs=1)

        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertTrue(report["embedding"]["truncated"])
        self.assertTrue(report["blocked"])
        self.assertTrue(
            any("cannot be certified" in blocker for blocker in report["blockers"])
        )

    def test_additive_cosine_pair_uses_the_combined_channel(self):
        records = [
            {
                "state": {
                    "padding_0": " ",
                    "task": f"common0 common1 common2 {tail}",
                }
            }
            for tail in ("left0", "right0")
        ]
        self.assertEqual(
            quality_gate_embedding._candidate_pairs(
                _lexical_signatures(_vectors(records)), 10
            ),
            ([], False),
        )
        report = self._audit(records, threshold=0.6)

        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertAlmostEqual(
            report["duplicates"][0]["similarity"], 0.621970, places=6
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

                report = self._audit(records)

                self.assertEqual(report["counts"]["duplicate_groups"], 0)
                self.assertEqual(report["embedding"]["candidate_pairs"], 1)
                self.assertEqual(
                    report["counts"]["embedding_duplicate_groups"], 1
                )
                self.assertEqual(report["duplicates"][0]["kind"], "embedding")


if __name__ == "__main__":
    unittest.main()
