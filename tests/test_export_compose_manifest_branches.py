"""Pin the refusal branches of compose-manifest authentication at export.

``export_compose_auth`` hands every manifest row and reward sidecar to the two
entry points of ``export_compose_manifest``. Each case below differs from one
authenticated retained row in exactly one property, so the first failing check
decides the refusal; messages are asserted verbatim.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import compose_curated
import curate_rewards
import export_compose_manifest
from export_contract import CuratedFile, ExportError, ViewerRow
from refusal_case_support import RefusalCaseAssertions

_OUTPUT_PATH = "records/a.jsonl"
_SOURCE_PATH = "factory/batch-r01.jsonl"
_COORDINATE = (_OUTPUT_PATH, 1)


def _reward_pair() -> tuple[dict, dict]:
    """One reward-annotated record and its reversible sidecar."""

    return curate_rewards.curate_record(
        {"id": "r1", "reward": 1.0, "state": {}}, source_path=_SOURCE_PATH, source_line=1
    )


def _outputs(record_json: str) -> dict[str, CuratedFile]:
    row = ViewerRow(source_file=_OUTPUT_PATH, source_line=1, record_json=record_json)
    return {_OUTPUT_PATH: CuratedFile(source_file=_OUTPUT_PATH, payload=b"", rows=(row,))}


def _entry(record_json: str, **overrides) -> dict:
    entry = {
        "compose_name": compose_curated.COMPOSE_NAME,
        "compose_version": compose_curated.COMPOSE_VERSION,
        "lane_order": list(compose_curated.LANE_ORDER),
        "action": compose_curated.ACTION_RETAINED,
        "source_path": _SOURCE_PATH,
        "source_line": 1,
        "output_path": _OUTPUT_PATH,
        "output_line": 1,
        "output_id": "r1",
        "output_sha256": hashlib.sha256(record_json.encode("utf-8")).hexdigest(),
        "reward_sidecar_id": None,
    }
    entry.update(overrides)
    return entry


def _authenticate(entries: list, record_json: str, sidecars: dict | None = None):
    return export_compose_manifest._authenticate_compose_manifest(
        entries, _outputs(record_json), sidecars or {}
    )


def _authenticate_plain(case: tuple):
    entries, record_json = case
    return _authenticate(entries, record_json)


_PLAIN = '{"id":"r1"}'


def _plain_refusals() -> tuple:
    invalid = "compose manifest entry 1 has an invalid output coordinate"
    unresolved = "compose manifest coordinate does not resolve: "
    return (
        ("entry is not an object", [["r1"]], _PLAIN, "compose manifest entry 1 must be an object"),
        (
            "coordinate repeated",
            [_entry(_PLAIN), _entry(_PLAIN)],
            _PLAIN,
            f"duplicate compose manifest coordinate {_COORDINATE}",
        ),
        ("output path is not a string", [_entry(_PLAIN, output_path=7)], _PLAIN, invalid),
        ("output line is a boolean", [_entry(_PLAIN, output_line=True)], _PLAIN, invalid),
        (
            "output path is not exported",
            [_entry(_PLAIN, output_path="records/b.jsonl")],
            _PLAIN,
            unresolved + "('records/b.jsonl', 1)",
        ),
        (
            "output line past the file",
            [_entry(_PLAIN, output_line=2)],
            _PLAIN,
            unresolved + f"('{_OUTPUT_PATH}', 2)",
        ),
        (
            "exported row is not an object",
            [_entry("[1]")],
            "[1]",
            f"compose manifest output id mismatch: {_COORDINATE}",
        ),
        (
            "exported id is not a string",
            [_entry('{"id":5}')],
            '{"id":5}',
            f"compose manifest output id mismatch: {_COORDINATE}",
        ),
        (
            "sidecar id names no sidecar",
            [_entry(_PLAIN, reward_sidecar_id="sha256:absent")],
            _PLAIN,
            "compose manifest references missing reward sidecar sha256:absent",
        ),
    )


class ComposeManifestRowRefusals(RefusalCaseAssertions, unittest.TestCase):
    def test_rows_that_do_not_bind_to_exported_bytes_are_refused(self):
        rows = (
            (label, (entries, record_json), message)
            for label, entries, record_json, message in _plain_refusals()
        )
        self.assert_each_refuses(ExportError, _authenticate_plain, rows)

    def test_retained_and_excluded_rows_authenticate(self):
        excluded = _entry(_PLAIN, action="excluded")
        for field_name in ("output_path", "output_line", "output_id", "output_sha256"):
            excluded[field_name] = None
        coordinates, sidecars = _authenticate([_entry(_PLAIN), excluded], _PLAIN)
        self.assertEqual(coordinates, {_COORDINATE})
        self.assertEqual(sidecars, set())


class ComposeManifestSidecarRefusals(unittest.TestCase):
    def setUp(self):
        self.curated, self.sidecar = _reward_pair()
        self.sidecars = export_compose_manifest._validated_sidecars_by_id([self.sidecar])

    def _refusal(self, entry: dict, record_json: str) -> str:
        with self.assertRaises(ExportError) as caught:
            _authenticate([entry], record_json, self.sidecars)
        return str(caught.exception)

    def test_duplicate_sidecar_ids_are_refused(self):
        with self.assertRaises(ExportError) as caught:
            export_compose_manifest._validated_sidecars_by_id([self.sidecar, self.sidecar])
        self.assertEqual(
            str(caught.exception), f"duplicate reward sidecar id {self.sidecar['sidecar_id']}"
        )

    def test_annotation_without_a_manifested_sidecar_is_refused(self):
        record_json = json.dumps(self.curated)
        self.assertEqual(
            self._refusal(_entry(record_json), record_json),
            f"compose output {_COORDINATE} has an unmanifested reward annotation",
        )

    def test_sidecar_that_does_not_restore_the_row_is_refused(self):
        tampered = copy.deepcopy(self.curated)
        tampered["state"] = {"changed": True}
        record_json = json.dumps(tampered)
        entry = _entry(record_json, reward_sidecar_id=self.sidecar["sidecar_id"])
        self.assertEqual(
            self._refusal(entry, record_json),
            f"compose output {_COORDINATE} does not authenticate its reward sidecar: "
            "restored source record hash mismatch",
        )

    def test_sidecar_that_restores_the_row_is_referenced(self):
        record_json = json.dumps(self.curated)
        entry = _entry(record_json, reward_sidecar_id=self.sidecar["sidecar_id"])
        coordinates, referenced = _authenticate([entry], record_json, self.sidecars)
        self.assertEqual(coordinates, {_COORDINATE})
        self.assertEqual(referenced, {self.sidecar["sidecar_id"]})


if __name__ == "__main__":
    unittest.main()
