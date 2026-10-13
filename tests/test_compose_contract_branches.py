"""Fail-closed branches of preserved native output and published coordinates."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for _path in (TESTS, TESTS.parent / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_contract as contract
from compose_contract import ComposeDecision, ComposeError

NATIVE = {"record_kind": "hardware_parity", "id": "hp-1"}
NATIVE_TEXT = '{"record_kind": "hardware_parity", "id": "hp-1"}'


def _retained(record, stages=()) -> ComposeDecision:
    return ComposeDecision("retained", record, (), tuple(stages), None, None)


def _identity_stage(**source) -> dict:
    return {"lane": "identity", "detail": {"source": source}}


def _native_source(original=NATIVE_TEXT, digest=None) -> dict:
    return {
        "original": original,
        "sha256": contract.sha256_hex(NATIVE_TEXT.encode("utf-8")) if digest is None else digest,
        "path": "hardware-parity-spike-trajectories/batch-r01.jsonl",
        "line": 1,
    }


class ContractCase(unittest.TestCase):
    def assert_refused(self, message: str, call, *args) -> None:
        with self.assertRaises(ComposeError) as caught:
            call(*args)

        self.assertEqual(str(caught.exception), message)


class NativeFrameTests(ContractCase):
    def test_unknown_native_terminator_is_refused(self):
        self.assert_refused(
            "invalid captured native source terminator",
            contract.emitted_record_line,
            _retained(NATIVE),
            NATIVE_TEXT,
            "\r",
        )

    def test_native_frames_keep_their_captured_terminator(self):
        frame = contract.emitted_record_line(_retained(NATIVE), NATIVE_TEXT, "\r\n")
        canonical = contract.emitted_record_line(_retained({"goal": "g"}), '{"goal":"g"}', "\r\n")

        self.assertEqual(
            contract.emitted_records_text([frame, canonical]), NATIVE_TEXT + '\r\n{"goal":"g"}\n'
        )

    def test_source_terminators_follow_each_physical_line(self):
        self.assertEqual(contract.source_terminators(b"a\r\nb\nc"), ("\r\n", "\n", ""))


class PreservedSourceTextTests(ContractCase):
    def test_native_output_without_identity_evidence_is_refused(self):
        self.assert_refused(
            "preserved native output has no identity evidence",
            contract.retained_json_line,
            _retained(NATIVE, ({"lane": "bridge"},)),
        )

    def test_native_output_without_source_text_is_refused(self):
        stage = _identity_stage(**_native_source(original=None))

        self.assert_refused(
            "preserved native output has no exact source text",
            contract.retained_json_line,
            _retained(NATIVE, (stage,)),
        )

    def test_native_source_text_with_a_foreign_digest_is_refused(self):
        stage = _identity_stage(**_native_source(digest="0" * 64))

        self.assert_refused(
            "preserved native source text does not match its line digest",
            contract.retained_json_line,
            _retained(NATIVE, (stage,)),
        )

    def test_native_source_text_for_another_record_is_unauthenticated(self):
        stage = _identity_stage(**_native_source())
        other = {"record_kind": "hardware_parity", "id": "hp-2"}

        with self.assertRaises(ComposeError) as caught:
            contract.retained_json_line(_retained(other, (stage,)))

        self.assertRegex(
            str(caught.exception), r"^preserved native source text is unauthenticated: "
        )

    def test_authenticated_native_source_text_is_reused_verbatim(self):
        stage = _identity_stage(**_native_source())

        self.assertEqual(contract.retained_json_line(_retained(NATIVE, (stage,))), NATIVE_TEXT)


class PublishedCoordinateTests(ContractCase):
    def test_nested_factory_identity_is_refused(self):
        self.assert_refused(
            "invalid factory identity for published source coordinate: 'a/b'",
            contract.published_source_coordinate,
            "batch-r01.jsonl",
            "a/b",
        )

    def test_parent_factory_identity_is_refused(self):
        self.assert_refused(
            "invalid factory identity for published source coordinate: '..'",
            contract.published_source_coordinate,
            "batch-r01.jsonl",
            "..",
        )

    def test_factory_qualified_member_keeps_its_coordinate(self):
        self.assertEqual(
            contract.published_source_coordinate("f/batch-r01.jsonl", "f"), "f/batch-r01.jsonl"
        )

    def test_colliding_published_coordinates_are_refused(self):
        members = ("batch-r01.jsonl", "f/batch-r01.jsonl")
        payloads = {member: b"{}\n" for member in members}
        identities = {member: ("f", True) for member in members}

        self.assert_refused(
            "published source coordinate collision: 'f/batch-r01.jsonl' and another source "
            "member both map to 'f/batch-r01.jsonl'",
            contract.published_source_snapshot,
            members,
            payloads,
            identities,
        )

    def test_factory_root_uses_its_own_calibration_file(self):
        root = Path("/runs/failure-as-fuel-preference-cascade")

        self.assertEqual(contract.default_units_migration_path(root), root / "units-migration.json")


if __name__ == "__main__":
    unittest.main()
