#!/usr/bin/env python3
"""Focused regressions for the split quality-gate embedding encoder."""

import math
import sys
import unittest
import weakref
from collections import Counter
from pathlib import Path
from unittest import mock


PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
sys.path.insert(0, str(PIPELINES))

import quality_gate_embedding as embedding  # noqa: E402


def _pair_vectors(left, right):
    """Build corpus-consistent vectors for two token counters."""
    document_frequency = Counter()
    document_frequency.update(left.keys())
    document_frequency.update(right.keys())
    idf = {
        token: math.log(3 / (count + 1)) + 1.0
        for token, count in document_frequency.items()
    }
    return embedding._tfidf_vector(left, idf), embedding._tfidf_vector(right, idf)


class EmbeddingOrderRegressions(unittest.TestCase):
    def test_adjacent_edges_do_not_alias_on_legacy_short_digest_collision(self):
        left = "A token33795 A"
        right = "A token104439 A"
        self.assertEqual(
            embedding._element_digest(left)[:8],
            embedding._element_digest(right)[:8],
        )

        forward_tokens = embedding.embedding_tokens(
            {"state": {"sequence": [left, right]}}
        )
        reverse_tokens = embedding.embedding_tokens(
            {"state": {"sequence": [right, left]}}
        )

        self.assertNotEqual(forward_tokens, reverse_tokens)

    def test_directed_list_edges_distinguish_shared_boundary_reversal(self):
        forward = {"state": {"sequence": ["A B A", "A C A"]}}
        reverse = {"state": {"sequence": ["A C A", "A B A"]}}

        forward_tokens = embedding.embedding_tokens(forward)
        reverse_tokens = embedding.embedding_tokens(reverse)
        self.assertNotEqual(forward_tokens, reverse_tokens)

        forward_edges = {
            token for token in forward_tokens if token.startswith(embedding._ORDER_MARK)
        }
        reverse_edges = {
            token for token in reverse_tokens if token.startswith(embedding._ORDER_MARK)
        }
        self.assertNotEqual(forward_edges, reverse_edges)
        self.assertTrue(any("adj:" in token for token in forward_edges))

        forward_vector, reverse_vector = _pair_vectors(
            forward_tokens, reverse_tokens
        )
        self.assertLess(embedding._cosine(forward_vector, reverse_vector), 1.0)

    def test_repeated_elements_retain_position_features(self):
        tokens = embedding.embedding_tokens(
            {"state": {"sequence": ["alpha", "beta", "alpha"]}}
        )
        order_features = [
            token for token in tokens if token.startswith(embedding._ORDER_MARK)
        ]
        self.assertTrue(any("adj:" in token for token in order_features))
        self.assertTrue(any("pos:" in token for token in order_features))

    def test_leading_insertion_preserves_shared_sequence_similarity(self):
        shared = [
            {
                "n": index,
                "decision_basis": f"inspect subsystem {index} for the fault",
                "tool_call": f"pytest tests/test_subsystem_{index}.py",
                "observation": f"subsystem {index} reported a clean run",
            }
            for index in range(1, 26)
        ]
        preamble = {
            "n": 0,
            "decision_basis": "read the brief before touching the repo",
            "tool_call": "cat BRIEF.md",
            "observation": "the brief names the failing module",
        }
        plain = {
            "goal": "find the failing subsystem and repair it",
            "steps": shared,
            "outcome": "the failing subsystem was repaired",
        }
        padded = {**plain, "steps": [preamble, *shared]}

        plain_tokens = embedding.embedding_tokens(plain)
        padded_tokens = embedding.embedding_tokens(padded)
        plain_vector, padded_vector = _pair_vectors(plain_tokens, padded_tokens)

        self.assertGreater(embedding._cosine(plain_vector, padded_vector), 0.90)
        plain_edges = {token for token in plain_tokens if "adj:" in token}
        padded_edges = {token for token in padded_tokens if "adj:" in token}
        self.assertEqual(len(plain_edges - padded_edges), 0)

        records = [
            {"file": "batch.jsonl", "line": 1, "tokens": plain_tokens.copy()},
            {"file": "batch.jsonl", "line": 2, "tokens": padded_tokens.copy()},
        ]
        duplicates, _clusters, stats = embedding._embedding_duplicates(
            records, 0.90, embedding.DEFAULT_MAX_EMBEDDING_PAIRS
        )
        self.assertEqual(stats["candidate_pairs"], 1)
        self.assertEqual(len(duplicates), 1)


class EmbeddingResourceRegressions(unittest.TestCase):
    def test_candidate_cap_only_truncates_when_a_pair_is_omitted(self):
        signature = tuple(range(embedding.EMBEDDING_MINHASH_SLOTS))
        exact, exact_truncated = embedding._candidate_pairs(
            [(0, signature), (1, signature)], max_pairs=1
        )
        capped, capped_truncated = embedding._candidate_pairs(
            [(0, signature), (1, signature), (2, signature)], max_pairs=1
        )
        self.assertEqual(exact, [(0, 1)])
        self.assertFalse(exact_truncated)
        self.assertEqual(capped, [(0, 1)])
        self.assertTrue(capped_truncated)

    def test_corpus_idf_is_released_before_candidate_generation(self):
        class Probe:
            pass

        seen = {}
        real_vector = embedding._tfidf_vector
        real_pairs = embedding._candidate_pairs

        def spy_vector(tokens, idf):
            if "probe" not in seen:
                probe = Probe()
                idf["\x00idf-liveness-probe"] = probe
                seen["probe"] = weakref.ref(probe)
            return real_vector(tokens, idf)

        def spy_pairs(signatures, max_pairs):
            seen["alive_at_pair_phase"] = seen["probe"]() is not None
            return real_pairs(signatures, max_pairs)

        records = [
            {
                "file": "batch.jsonl",
                "line": index,
                "tokens": embedding.embedding_tokens(record),
            }
            for index, record in enumerate(
                (
                    {"state": {"note": "inspect the queue retry path"}},
                    {"state": {"note": "verify the turbine safety interlock"}},
                ),
                1,
            )
        ]
        with mock.patch.object(embedding, "_tfidf_vector", spy_vector), mock.patch.object(
            embedding, "_candidate_pairs", spy_pairs
        ):
            embedding._embedding_duplicates(
                records,
                embedding.DEFAULT_EMBEDDING_THRESHOLD,
                embedding.DEFAULT_MAX_EMBEDDING_PAIRS,
            )

        self.assertIn("alive_at_pair_phase", seen)
        self.assertFalse(seen["alive_at_pair_phase"])


if __name__ == "__main__":
    unittest.main()
