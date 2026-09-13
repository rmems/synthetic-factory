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
import quality_gate_embedding  # noqa: E402


class EmbeddingEncoder(unittest.TestCase):
    def _assert_string_channel_distinct(self, records, markers):
        token_sets = [quality_gate.embedding_tokens(record) for record in records]
        self.assertNotEqual(token_sets[0], token_sets[1])
        for marker, tokens in zip(markers, token_sets):
            self.assertTrue(any(marker in token for token in tokens), marker)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", records)
            report = quality_gate.audit_run(root)
        self.assertEqual(report["duplicates"], [])

    def test_case_and_operator_channels_remain_semantically_distinct(self):
        cases = (
            (
                [
                    {"state": {"predicate": "queue_depth < hard_limit"}},
                    {"state": {"predicate": "queue_depth > hard_limit"}},
                ],
                ("str-op:<", "str-op:>"),
            ),
            (
                [
                    {"state": {"principal": "User"}},
                    {"state": {"principal": "user"}},
                ],
                ("str-case:User", "str-case:user"),
            ),
        )
        for records, markers in cases:
            with self.subTest(markers=markers):
                self._assert_string_channel_distinct(records, markers)

    def test_repeated_case_operator_units_keep_whole_sequence_order(self):
        """Repeated units can make an adjacent-bigram multiset ambiguous."""
        pairs = {
            "case and operator": ("a+A+", "A+a+"),
            "repeated word and operators": ("a-a/a", "a/a-a"),
            "same directed-trigram multiset": (
                "a+a-a+a/a+a",
                "a+a/a+a-a+a",
            ),
            "casefold-expanded chain": (
                "a/b-A+B",
                "A+b-a/B",
            ),
            "casefold-only repeated chain": (
                "a a A a",
                "a A a a",
            ),
            "boundary singleton with case variants": (
                "a b B b",
                "a B b b",
            ),
            "moved internal whitespace gap": (
                "a a a  a a",
                "a a  a a a",
            ),
        }
        for label, (left, right) in pairs.items():
            with self.subTest(case=label):
                first = {"id": "seq-1", "state": {"expr": left}}
                second = {"id": "seq-2", "state": {"expr": right}}
                first_tokens = quality_gate.embedding_tokens(first)
                second_tokens = quality_gate.embedding_tokens(second)

                self.assertNotEqual(first_tokens, second_tokens)
                for tokens in (first_tokens, second_tokens):
                    self.assertTrue(
                        any("str-unit-sequence:" in token for token in tokens)
                    )
                self.assertEqual(
                    {
                        token: count
                        for token, count in first_tokens.items()
                        if quality_gate._BIGRAM_SEP in token
                    },
                    {
                        token: count
                        for token, count in second_tokens.items()
                        if quality_gate._BIGRAM_SEP in token
                    },
                )
                self.assertEqual(self._audit_pair(first, second)["duplicates"], [])

    def test_string_sequence_features_do_not_enter_candidate_sketches(self):
        tokens = quality_gate.embedding_tokens(
            {"state": {"expr": "a-a/a"}}
        )
        sequence = next(
            token for token in tokens if "str-unit-sequence:" in token
        )

        self.assertEqual(
            list(quality_gate.candidate_sketch_features({sequence: 1.0})),
            [],
        )

    def test_one_terminal_singleton_does_not_need_a_sequence_digest(self):
        tokens = quality_gate.embedding_tokens(
            {"state": {"note": "saturated saturated saturated alpha"}}
        )

        self.assertFalse(
            any("str-unit-sequence:" in token for token in tokens)
        )

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
            steps = [
                {
                    "n": index,
                    "decision_basis": f"inspect subsystem {index} for the fault",
                    "tool_call": f"pytest tests/test_subsystem_{index}.py",
                    "observation": f"subsystem {index} reported a clean run",
                }
                for index in range(1, 26)
            ]
            if with_preamble:
                steps = [
                    {
                        "n": 1,
                        "decision_basis": "read brief",
                        "tool_call": "cat BRIEF.md",
                        "observation": "brief names module",
                    },
                    *(
                        {**step, "n": index}
                        for index, step in enumerate(steps, 2)
                    ),
                ]
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
        # Renumbering after the insertion must preserve all shared adjacency
        # edges, keeping the pair above the calibrated default threshold.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write(root / "batch.jsonl", [plain, padded])
            report = quality_gate.audit_run(root)

        self.assertEqual(len(report["duplicates"]), 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )
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
                self.assertTrue(
                    any(
                        "str-gap-layout:" in token
                        for token in quality_gate.embedding_tokens(first)
                    )
                )

                report = self._audit_pair(first, second)
                self.assertEqual(report["duplicates"], [])

    def test_gap_independent_lexical_channel_recalls_spacing_clone(self):
        words = [f"word{index:03d}" for index in range(100)]
        first = {"state": {"note": " ".join(words)}}
        second = {"state": {"note": "  ".join(words)}}
        first_tokens = quality_gate.embedding_tokens(first)
        second_tokens = quality_gate.embedding_tokens(second)

        self.assertNotEqual(first_tokens, second_tokens)
        self.assertEqual(
            {
                token: count
                for token, count in first_tokens.items()
                if not token.startswith(
                    quality_gate_embedding._NONCHAIN_STRING_MARK
                )
            },
            {
                token: count
                for token, count in second_tokens.items()
                if not token.startswith(
                    quality_gate_embedding._NONCHAIN_STRING_MARK
                )
            },
        )

        report = self._audit_pair(first, second)
        self.assertEqual(report["embedding"]["candidate_pairs"], 1)
        self.assertEqual(report["counts"]["embedding_duplicate_groups"], 1)
        self.assertGreater(
            report["duplicates"][0]["similarity"],
            quality_gate.DEFAULT_EMBEDDING_THRESHOLD,
        )

    def test_terminal_and_whitespace_only_gaps_remain_distinct(self):
        """The scanner must not discard a gap that has no following unit."""
        pairs = {
            "terminal space": ("customer", "customer "),
            "whitespace width": (" ", "  "),
            "whitespace kind": (" ", "\t"),
        }
        for label, (left, right) in pairs.items():
            with self.subTest(case=label):
                first = {"id": "g-1", "state": {"note": left}}
                second = {"id": "g-2", "state": {"note": right}}
                first_tokens = quality_gate.embedding_tokens(first)
                second_tokens = quality_gate.embedding_tokens(second)

                self.assertNotEqual(
                    quality_gate.record_hash(first), quality_gate.record_hash(second)
                )
                self.assertNotEqual(first_tokens, second_tokens)
                self.assertTrue(
                    any("str-terminal-gap:" in token for token in second_tokens)
                )
                self.assertEqual(self._audit_pair(first, second)["duplicates"], [])

    def test_terminal_gap_does_not_interrupt_word_bigrams(self):
        """A boundary feature must not enter the ordinary lexical chain."""
        plain = quality_gate.embedding_tokens(
            {"state": {"note": "alpha beta gamma"}}
        )
        trailing = quality_gate.embedding_tokens(
            {"state": {"note": "alpha beta gamma "}}
        )

        plain_bigrams = {
            token: count
            for token, count in plain.items()
            if quality_gate._BIGRAM_SEP in token
        }
        trailing_bigrams = {
            token: count
            for token, count in trailing.items()
            if quality_gate._BIGRAM_SEP in token
        }
        self.assertEqual(plain_bigrams, trailing_bigrams)
        self.assertTrue(any("str-terminal-gap:" in token for token in trailing))
        self.assertFalse(
            any(
                "str-terminal-gap:" in token
                for token in trailing_bigrams
            )
        )

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
