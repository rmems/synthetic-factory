#!/usr/bin/env python3
"""Lexical encoder behavior tests for the quality gate."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from gate_fixtures import write  # noqa: E402
import quality_gate  # noqa: E402


class EmbeddingEncoder(unittest.TestCase):
    def test_string_operators_remain_semantically_distinct(self):
        records = [
            {"state": {"predicate": "queue_depth < hard_limit"}},
            {"state": {"predicate": "queue_depth > hard_limit"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        self.assertTrue(any("str-op:<" in token for token in token_sets[0]))
        self.assertTrue(any("str-op:>" in token for token in token_sets[1]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_null_and_empty_values_have_typed_sentinels(self):
        records = [
            {"state": {"value": None}},
            {"state": {"value": ""}},
            {"state": {"value": []}},
            {"state": {"value": {}}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertEqual(len({frozenset(tokens) for tokens in token_sets}), 4)
        for marker, tokens in zip(
            ("null", "str-empty", "list-empty", "dict-empty"), token_sets
        ):
            self.assertTrue(any(marker in token for token in tokens), marker)

    def test_case_sensitive_identifiers_remain_distinct(self):
        records = [
            {"state": {"principal": "User"}},
            {"state": {"principal": "user"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        self.assertTrue(any("str-case:User" in token for token in token_sets[0]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_repeated_sequence_order_is_position_qualified(self):
        """A repeated element makes bigram multisets coincide, so those lists
        carry an explicit positional feature. The feature is asserted by its
        effect, not by its spelling: absolute ``/i:<index>`` path qualification
        was replaced because it made every later leaf depend on its index."""
        records = [
            {"state": {"sequence": ["alpha", "beta", "alpha", "gamma", "alpha"]}},
            {"state": {"sequence": ["alpha", "gamma", "alpha", "beta", "alpha"]}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        self.assertTrue(
            any(token.startswith(quality_gate._ORDER_MARK) for token in token_sets[0]),
            "a list repeating an element must carry positional features",
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_reordering_distinct_elements_is_still_not_a_duplicate(self):
        """Directed adjacency features distinguish every list ordering.

        Distinct elements previously relied on leaf-word bigrams, which do not
        cover short or non-textual elements reliably. The order marker now
        carries adjacent element digests without tying later leaves to absolute
        positions.
        """
        records = [
            {"state": {"sequence": ["alpha", "beta"]}},
            {"state": {"sequence": ["beta", "alpha"]}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        for tokens in token_sets:
            self.assertTrue(
                any(token.startswith(quality_gate._ORDER_MARK) for token in tokens)
            )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_one_inserted_step_does_not_rewrite_every_later_step(self):
        """Absolute ``/i:<index>`` qualification shifted every later leaf, so a
        25-step trajectory and the same trajectory with one extra leading step
        scored ~0.21 -- far below any usable threshold -- despite 25 identical
        steps in identical order. Similarity must track the content that
        actually differs."""

        def trajectory(with_preamble):
            steps = []
            if with_preamble:
                steps.append(
                    {
                        "n": 0,
                        "decision_basis": "read the brief before touching the repo",
                        "tool_call": "cat BRIEF.md",
                        "observation": "the brief names the failing module",
                    }
                )
            for index in range(1, 26):
                steps.append(
                    {
                        "n": index,
                        "decision_basis": f"inspect subsystem {index} for the fault",
                        "tool_call": f"pytest tests/test_subsystem_{index}.py",
                        "observation": f"subsystem {index} reported a clean run",
                    }
                )
            return {
                "id": f"traj-{int(with_preamble)}",
                "goal": "find the failing subsystem and repair it",
                "steps": steps,
                "outcome": "the failing subsystem was repaired",
                "reward": {"success": True},
            }

        plain, padded = trajectory(False), trajectory(True)
        self.assertNotEqual(
            quality_gate.record_hash(quality_gate.exact_identity_view(plain)),
            quality_gate.record_hash(quality_gate.exact_identity_view(padded)),
        )

        shared = trajectory(False)["steps"][0]
        for record in (plain, padded):
            tokens = quality_gate.embedding_tokens(record)
            self.assertTrue(
                any("subsystem" in token for token in tokens),
                "step content must still be encoded",
            )
        # The 25 shared steps must produce the same leaf features in both, so
        # the pair is a near-duplicate at any threshold at or below its real
        # content overlap rather than only below ~0.21.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [plain, padded])
            report = quality_gate.audit_run(root, threshold=0.90)

        self.assertEqual(len(report["duplicates"]), 1)
        self.assertIn(shared["tool_call"].split()[0], "pytest")

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

    def test_numeric_features_preserve_sign_and_type(self):
        records = [
            {"executed_action": {"setpoint": -5}},
            {"executed_action": {"setpoint": 5}},
            {"executed_action": {"setpoint": "5"}},
        ]
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertEqual(len({frozenset(tokens) for tokens in token_sets}), 3)
        self.assertTrue(any("int:-5" in token for token in token_sets[0]))
        self.assertTrue(any("int:5" in token for token in token_sets[1]))
        self.assertTrue(any("str-case:5" in token for token in token_sets[2]))
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

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
        self.assertTrue(any("str-char:冷" in token for token in token_sets[0]))
        self.assertTrue(any("str-char:港" in token for token in token_sets[1]))
        self.assertTrue(
            any(
                "str-char:冷" in token and "str-char:却" in token
                for token in token_sets[0]
            )
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["duplicates"], [])

    def test_unsegmented_scripts_use_grapheme_fallback(self):
        samples = {
            "japanese": "クレーンの温度を下げる",
            "thai": "ระบบควบคุมลดอุณหภูมิน้ำหล่อเย็น",
        }
        for language, note in samples.items():
            with self.subTest(language=language):
                tokens = quality_gate.embedding_tokens({"state": {"note": note}})
                character_tokens = [
                    token
                    for token in tokens
                    if "str-char:" in token and quality_gate._BIGRAM_SEP not in token
                ]
                self.assertGreaterEqual(len(character_tokens), 4)

    def test_unsegmented_minimal_edit_is_an_embedding_duplicate(self):
        common = (
            "港口起重机正在执行集装箱装卸作业控制系统持续监测吊具位置载荷风速"
            "制动器温度液压压力电机电流和安全联锁状态操作员依据标准程序确认所有"
            "传感器读数稳定并记录每个控制周期的执行结果"
        )
        records = [
            {"state": {"note": common * 2 + "随后降低冷却水设定值保持设备稳定运行"}},
            {"state": {"note": common * 2 + "随后提高冷却水设定值保持设备稳定运行"}},
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)

        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertEqual(len(report["duplicates"]), 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )

    def _audit_pair(self, first, second):
        """Audit two one-record-per-line records and return the report."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [first, second])
            return quality_gate.audit_run(root)

    def test_unsegmented_reordering_is_not_an_embedding_duplicate(self):
        """A grapheme bag plus adjacent bigrams is not injective over
        sequences: 甲乙甲丙甲 and 甲丙甲乙甲 share both, so the encoder scored
        them at cosine 1.0 and the blocking gate excluded one even though
        their exact hashes differ (Codex #98, quality_gate.py:461)."""
        first = {"id": "u-1", "state": {"note": "甲乙甲丙甲"}}
        second = {"id": "u-2", "state": {"note": "甲丙甲乙甲"}}

        self.assertNotEqual(
            quality_gate.record_hash(first), quality_gate.record_hash(second)
        )
        self.assertNotEqual(
            quality_gate.embedding_tokens(first), quality_gate.embedding_tokens(second)
        )

        report = self._audit_pair(first, second)
        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 0)

    def test_whitespace_boundaries_survive_in_code_strings(self):
        """Whitespace is semantic in agentic coding and shell content. These
        pairs have different exact hashes but used to produce identical token
        counters and cosine 1.0 (Codex #98, quality_gate.py:395)."""
        pairs = {
            "shell path": (
                "curl https://safe /admin",
                "curl https://safe/admin",
            ),
            "python indentation": (
                "if x:\n    return 1",
                "if x:\nreturn 1",
            ),
        }
        for label, (left, right) in pairs.items():
            with self.subTest(case=label):
                first = {"id": "w-1", "state": {"cmd": left}}
                second = {"id": "w-2", "state": {"cmd": right}}

                self.assertNotEqual(
                    quality_gate.record_hash(first), quality_gate.record_hash(second)
                )
                self.assertNotEqual(
                    quality_gate.embedding_tokens(first),
                    quality_gate.embedding_tokens(second),
                )

                report = self._audit_pair(first, second)
                self.assertEqual(report["duplicates"], [])

    def test_word_order_survives_the_whitespace_encoding(self):
        """The gap rides on the following unit instead of becoming a token of
        its own, so adjacent-word bigrams still relate word to word. A
        standalone whitespace token would make these two identical."""
        first = {"id": "o-1", "state": {"note": "alpha beta gamma delta"}}
        second = {"id": "o-2", "state": {"note": "alpha gamma beta delta"}}

        self.assertNotEqual(
            quality_gate.embedding_tokens(first), quality_gate.embedding_tokens(second)
        )
        self.assertEqual(self._audit_pair(first, second)["duplicates"], [])


if __name__ == "__main__":
    unittest.main()
