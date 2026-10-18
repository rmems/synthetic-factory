"""Pin the fail-closed checks on identity-manifest source and provenance evidence.

``curate_identity_evidence`` recovers each manifest entry's embedded source
snapshot and validates its provenance originals. Every refusal is an
``IdentityTreeError`` whose message names the manifest location; the cases
below differ from one valid snapshot in exactly one field.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import curate_identity_evidence as evidence
import curate_identity_json as identity_json
from refusal_case_support import RefusalCaseAssertions

IdentityTreeError = evidence.IdentityTreeError
_WHERE = "IDENTITY-MANIFEST.json[0].source"
_LINE = '{"id": "r1"}'
_CANONICAL = identity_json.canonical_json({"id": "r1"})


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _deps(resolve_provenance=None) -> evidence.ManifestDependencies:
    return evidence.ManifestDependencies(
        resolve_provenance=resolve_provenance or (lambda owner, state: None),
        check_dependencies=lambda: None,
        strict_json_loads=identity_json.strict_json_loads,
        is_json_whitespace=identity_json._is_json_whitespace,
        canonical_json=identity_json.canonical_json,
        sha256_bytes=lambda payload: hashlib.sha256(payload).hexdigest(),
    )


def _source(**changes) -> dict:
    source = {
        "path": "factory/batch-r01.jsonl",
        "line": 1,
        "sha256": _sha256(_LINE),
        "hash_basis": "source-json-line-sha256",
        "original": _LINE,
    }
    source.update(changes)
    return source


_DUPLICATE_KEYS = '{"a":1,"a":2}'
_SNAPSHOT = "must be a hash-verifiable JSONL snapshot"
_SOURCE_REFUSALS = (
    (
        "parent traversal",
        _source(path="../x.jsonl"),
        (
            f"{_WHERE}.path is invalid: source_path must be normalized, relative, "
            "and contain no '.' or '..'"
        ),
    ),
    ("line is zero", _source(line=0), f"{_WHERE}.line must be positive"),
    ("digest is not text", _source(sha256=5), f"{_WHERE}.sha256 must be a SHA-256"),
    ("digest is uppercase", _source(sha256="A" * 64), f"{_WHERE}.sha256 must be a SHA-256"),
    ("unknown hash basis", _source(hash_basis="other"), f"{_WHERE}.hash_basis is invalid"),
    ("hash basis is not text", _source(hash_basis=3), f"{_WHERE}.hash_basis is invalid"),
    ("snapshot missing", _source(original=None), f"{_WHERE}.original {_SNAPSHOT}"),
    ("snapshot empty", _source(original=""), f"{_WHERE}.original {_SNAPSHOT}"),
    ("snapshot is whitespace", _source(original="  "), f"{_WHERE}.original {_SNAPSHOT}"),
    (
        "snapshot holds two lines",
        _source(original="{}\n{}"),
        f"{_WHERE}.original must contain exactly one JSONL record",
    ),
    (
        "snapshot differs from digest",
        _source(original='{"id": "r2"}'),
        f"{_WHERE}.original does not match source.sha256",
    ),
    (
        "snapshot is not strict JSON",
        _source(original=_DUPLICATE_KEYS, sha256=_sha256(_DUPLICATE_KEYS)),
        f"{_WHERE}.original is not strict JSON: duplicate JSON object key 'a'",
    ),
    (
        "snapshot is not canonical under the canonical basis",
        _source(hash_basis="canonical-json-sha256"),
        f"{_WHERE}.original does not match canonical-json-sha256 basis",
    ),
)


def _recover_source(source_meta: dict):
    return evidence.hash_verified_manifest_source(source_meta, 0, _deps())


class HashVerifiedManifestSource(RefusalCaseAssertions, unittest.TestCase):
    def test_line_basis_keeps_the_physical_bytes(self):
        source = _recover_source(_source())
        self.assertEqual(source.record, {"id": "r1"})
        self.assertEqual(source.source_path, "factory/batch-r01.jsonl")
        self.assertEqual(source.source_sha256, _sha256(_LINE))
        self.assertEqual(source.source_json, _LINE)

    def test_canonical_basis_drops_digest_and_bytes(self):
        canonical = _source(
            original=_CANONICAL, sha256=_sha256(_CANONICAL), hash_basis="canonical-json-sha256"
        )
        source = _recover_source(canonical)
        self.assertEqual(source.record, {"id": "r1"})
        self.assertIsNone(source.source_sha256)
        self.assertIsNone(source.source_json)

    def test_inconsistent_snapshots_are_refused(self):
        self.assert_each_refuses(IdentityTreeError, _recover_source, _SOURCE_REFUSALS)


def _presence(snapshot):
    return evidence.validate_presence_snapshot(snapshot, "s")


_EXACT_PRESENCE = "s must contain exactly boolean present and value"
_PRESENCE_REFUSALS = (
    ("not an object", ["present"], _EXACT_PRESENCE),
    ("extra key", {"present": True, "value": 1, "x": 0}, _EXACT_PRESENCE),
    ("present is not boolean", {"present": 1, "value": 1}, "s.present must be a boolean"),
    ("absent carries a value", {"present": False, "value": 0}, "s.value must be null when absent"),
)


class PresenceSnapshots(RefusalCaseAssertions, unittest.TestCase):
    def test_presence_snapshot_shape_is_exact(self):
        self.assert_each_refuses(IdentityTreeError, _presence, _PRESENCE_REFUSALS)

    def test_valid_presence_snapshots(self):
        self.assertEqual(_presence({"present": True, "value": 0}), (True, 0))
        self.assertEqual(_presence({"present": False, "value": None}), (False, None))


def _present(value) -> dict:
    return {"present": True, "value": value}


_ABSENT = {"present": False, "value": None}
_STATE_ORIGINAL = {
    "sim_or_real": _present("sim"),
    "state_provenance": _present({"kind": "designed"}),
    "owner_provenance": _ABSENT,
}
_STATE_MAPPING = {"state_path": "/state", "basis": "state", "original": _STATE_ORIGINAL}
_CANONICAL_PROVENANCE = {"kind": "designed", "claimed": "sim"}
_UNRESOLVED = "p.original does not resolve to its canonical provenance"


def _validate_original(mapping: dict):
    return evidence.validate_provenance_original(mapping, {}, "p", _deps())


def _validate_state_resolving_to(resolved: tuple):
    deps = _deps(lambda owner, state: resolved)
    return evidence.validate_provenance_original(_STATE_MAPPING, _CANONICAL_PROVENANCE, "p", deps)


_SNAPSHOT_REFUSALS = (
    (
        "owner snapshot holds more than owner provenance",
        {"state_path": None, "original": {"owner_provenance": _ABSENT, "x": 1}},
        "p.original must contain exactly owner_provenance",
    ),
    (
        "state snapshot is incomplete",
        {"state_path": "/state", "original": {"sim_or_real": _ABSENT}},
        "p.original must contain the complete state provenance snapshot",
    ),
)
_RESOLUTION_REFUSALS = (
    ("kind differs", ("measured", "sim", "state"), _UNRESOLVED),
    ("basis differs", ("designed", "sim", "owner"), _UNRESOLVED),
    ("claim differs", ("designed", "real", "state"), _UNRESOLVED),
)


class ProvenanceOriginals(RefusalCaseAssertions, unittest.TestCase):
    def test_snapshot_shapes_are_exact(self):
        self.assert_each_refuses(IdentityTreeError, _validate_original, _SNAPSHOT_REFUSALS)

    def test_state_snapshot_replays_present_values_through_the_resolver(self):
        calls = []

        def resolve(owner, state):
            calls.append((owner, state))
            return "designed", "sim", "state"

        evidence.validate_provenance_original(
            _STATE_MAPPING, _CANONICAL_PROVENANCE, "p", _deps(resolve)
        )
        self.assertEqual(calls, [({}, {"sim_or_real": "sim", "provenance": {"kind": "designed"}})])

    def test_resolution_that_differs_from_the_canonical_provenance_is_refused(self):
        self.assert_each_refuses(
            IdentityTreeError, _validate_state_resolving_to, _RESOLUTION_REFUSALS
        )


def _owned(kind: str, claimed: str) -> dict:
    return {"provenance": {"kind": kind, "claimed": claimed}}


_OWNERS = {
    "chosen": _owned("designed", "a"),
    "rejected": _owned("designed", "a"),
    "measured": _owned("measured", "b"),
    "other": _owned("designed", "c"),
    "bare": {},
}


def _aggregate(owner_paths: list):
    return evidence.aggregate_owner_provenance(_OWNERS, owner_paths)


_AGGREGATE_REFUSALS = (
    ("only the root owner", ["/"], "aggregate provenance mapping has no nested owners"),
    ("owner lacks provenance", ["/bare"], "provenance mapping owner /bare lacks provenance"),
)


class AggregateOwnerProvenance(RefusalCaseAssertions, unittest.TestCase):
    def test_aggregates_by_kind_and_claim(self):
        cases = (
            (
                "one kind, one claim",
                ["/", "/chosen", "/rejected"],
                {"kind": "designed", "claimed": "a"},
            ),
            ("kinds differ", ["/chosen", "/measured"], {"kind": "unknown", "claimed": ["a", "b"]}),
            ("claims differ", ["/chosen", "/other"], {"kind": "designed", "claimed": ["a", "c"]}),
        )
        for label, owner_paths, expected in cases:
            with self.subTest(label):
                self.assertEqual(_aggregate(owner_paths), expected)

    def test_aggregate_without_nested_provenance_is_refused(self):
        self.assert_each_refuses(IdentityTreeError, _aggregate, _AGGREGATE_REFUSALS)


_REPLAY = "IDENTITY-MANIFEST.json[3] hash-verified source replay"
_NO_MAPPINGS = f"{_REPLAY} did not produce provenance mappings"
_BAD_TARGET = f"{_REPLAY} produced an invalid provenance target"


def _expected_by_target(expected_mapping: dict):
    return evidence.expected_provenance_by_target(expected_mapping, 3)


def _plan(*mappings) -> dict:
    return {"provenance_mappings": list(mappings)}


_PLAN_REFUSALS = (
    ("mappings are not a list", {"provenance_mappings": {}}, _NO_MAPPINGS),
    ("mappings are empty", _plan(), _NO_MAPPINGS),
    ("mapping is not an object", _plan(["/"]), f"{_REPLAY} produced an invalid provenance mapping"),
    ("owner path is not text", _plan({"owner_path": 1}), _BAD_TARGET),
    ("state path is not text", _plan({"owner_path": "/", "state_path": 2}), _BAD_TARGET),
    (
        "target repeats",
        _plan({"owner_path": "/"}, {"owner_path": "/"}),
        f"{_REPLAY} repeated a provenance target",
    ),
)


class ExpectedProvenanceByTarget(RefusalCaseAssertions, unittest.TestCase):
    def test_replayed_plan_is_indexed_by_target(self):
        root = {"owner_path": "/", "state_path": None}
        state = {"owner_path": "/", "state_path": "/state"}
        self.assertEqual(
            _expected_by_target(_plan(root, state)), {("/", None): root, ("/", "/state"): state}
        )

    def test_malformed_replayed_plans_are_refused(self):
        self.assert_each_refuses(IdentityTreeError, _expected_by_target, _PLAN_REFUSALS)


if __name__ == "__main__":
    unittest.main()
