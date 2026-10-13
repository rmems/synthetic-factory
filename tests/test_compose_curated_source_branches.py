"""Fail-closed branches of native source-line decoding and deduplication."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated_source as source
from compose_contract import ComposeDecision, ComposeError
from compose_curated_test_support import episode
from exact_json import ExactJSONFloat

PATH = "agentic-coding-trajectory-factory/batch-r01.jsonl"
EPISODE_LINE = json.dumps(episode()).encode("utf-8")


def _context(**overrides) -> source.SourceLineContext:
    return source.SourceLineContext(PATH, 1, "0" * 64, **overrides)


class SourceLineExclusionTests(unittest.TestCase):
    def assert_excluded(self, physical_line: bytes, reason: str, **overrides) -> ComposeDecision:
        decision = source.compose_source_line(physical_line, _context(**overrides))

        self.assertEqual((decision.action, decision.reason_codes), ("excluded", (reason,)))
        self.assertEqual(decision.stages[0]["lane"], "source")
        return decision

    def test_invalid_utf8_is_excluded(self):
        self.assert_excluded(b"\xff{}", "compose.source_line_invalid_utf8")

    def test_invalid_json_is_excluded(self):
        self.assert_excluded(b"{", "compose.source_line_invalid_json")

    def test_non_finite_constant_is_excluded(self):
        self.assert_excluded(b'{"reward": NaN}', "compose.source_line_invalid_json")

    def test_curation_recursion_is_excluded_as_invalid_json(self):
        def exhaust(_record, _context):
            raise RecursionError("too deep")

        decision = self.assert_excluded(
            EPISODE_LINE, "compose.source_line_invalid_json", record_composer=exhaust
        )

        self.assertEqual(
            decision.stages[0]["detail"]["error"],
            "recursion depth exhausted during curation: too deep",
        )

    def test_supplied_exclusion_builder_is_used(self):
        built: list = []

        def excluded(reason, _detail):
            built.append(reason)
            return ComposeDecision("excluded", None, (reason,), ({"lane": "source"},), None, None)

        self.assert_excluded(
            b"{", "compose.source_line_invalid_json", excluded_source_line=excluded
        )
        self.assertEqual(built, ["compose.source_line_invalid_json"])


class NativeRecordParsingTests(unittest.TestCase):
    def composed_record(self, physical_line: bytes):
        composer = mock.Mock(
            return_value=ComposeDecision("excluded", None, ("stub",), (), None, None)
        )
        context = source.SourceLineContext(
            "hardware-parity-spike-trajectories/batch-r01.jsonl",
            1,
            "0" * 64,
            record_composer=composer,
        )

        source.compose_source_line(physical_line, context)

        return composer.call_args.args[0]

    def test_declared_native_record_keeps_exact_decimal_tokens(self):
        record = self.composed_record(b'{"record_kind": "hardware_parity", "lsb": 1.10}')

        self.assertIsInstance(record["lsb"], ExactJSONFloat)
        self.assertEqual(str(record["lsb"]), "1.10")

    def test_ordinary_record_uses_plain_floats(self):
        record = self.composed_record(b'{"goal": "g", "lsb": 1.10}')

        self.assertIs(type(record["lsb"]), float)


class SourceSemanticTests(unittest.TestCase):
    def test_repeated_source_record_is_excluded_after_the_first_retention(self):
        seen: dict = {}
        first = source.compose_source_line(EPISODE_LINE, _context(seen_source_semantics=seen))

        second = source.compose_source_line(
            EPISODE_LINE, source.SourceLineContext(PATH, 2, "0" * 64, seen_source_semantics=seen)
        )

        self.assertEqual(first.action, "retained")
        self.assertEqual(second.reason_codes, ("compose.source_record_semantic_duplicate",))
        self.assertEqual(second.stages[0]["detail"]["first_source_line"], 1)

    def test_excluded_source_record_is_not_indexed(self):
        seen: dict = {}

        source.compose_source_line(b'{"goal": "g"}', _context(seen_source_semantics=seen))

        self.assertEqual(seen, {})

    def test_non_callable_deduplicator_is_refused(self):
        context = _context(deduplicate_curated_record=42)

        with self.assertRaises(ComposeError) as caught:
            source.compose_source_line(EPISODE_LINE, context)

        self.assertEqual(str(caught.exception), "source-line deduplicator must be callable or None")

    def test_supplied_deduplicator_receives_the_line_coordinates(self):
        calls: list = []

        def deduplicate(decision, **coordinates):
            calls.append(coordinates)
            return decision

        decision = source.compose_source_line(
            EPISODE_LINE, _context(deduplicate_curated_record=deduplicate)
        )

        self.assertEqual(decision.action, "retained")
        self.assertEqual(
            calls, [{"source_path": PATH, "source_line": 1, "seen_curated_semantics": None}]
        )


class TransformContractTests(unittest.TestCase):
    def test_reviewed_trajectory_module_is_declared(self):
        reviewed = type("Reviewed", (), {"TRANSFORM_NAME": "gate", "TRANSFORM_VERSION": "2"})

        trajectory = source.transform_contract(reviewed)["preferences"]["trajectory"]

        self.assertEqual(
            trajectory, {"name": "gate", "version": "2", "implementation": "reviewed_module"}
        )

    def test_compatible_core_is_declared_without_a_reviewed_module(self):
        trajectory = source.transform_contract()["preferences"]["trajectory"]

        self.assertEqual(trajectory["implementation"], "compatible_core")


if __name__ == "__main__":
    unittest.main()
