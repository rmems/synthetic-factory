"""Pin the refusal branches of the named curation-gate checks.

Each helper here was extracted from a larger gate function without changing
behaviour. These tests hold the messages, the order of checks, and the
pass-through results that the integrate/promote fixtures reach only on their
happy paths.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "pipelines") not in sys.path:
    sys.path.insert(0, str(REPO / "pipelines"))

import curate_gate_digest as digest
import curate_gate_evidence as evidence
import curate_gate_identity_gate as identity_gate
import curate_gate_manifests as manifests
import curate_gate_paths as paths
import curate_gate_reward as reward
import curate_rewards

GateError = manifests.GateError
RewardOntologyError = curate_rewards.RewardOntologyError
SOURCE_KEY = ("factory/batch-r01.jsonl", 3)


def _manifest_entries(text):
    return manifests._json_manifest_entries(Path("lane.json"), text)


class ManifestCandidateTests(unittest.TestCase):
    def test_object_manifest_uses_the_first_declared_list_key(self):
        text = json.dumps({"records": [{"b": 2}], "entries": [{"a": 1}], "items": "x"})
        self.assertEqual(_manifest_entries(text), [{"a": 1}])

    def test_object_without_a_declared_list_is_refused(self):
        text = json.dumps({"entries": "not-a-list"})
        with self.assertRaisesRegex(GateError, "manifest object needs one of decisions, manifest"):
            _manifest_entries(text)

    def test_scalar_manifest_is_refused(self):
        with self.assertRaisesRegex(GateError, "manifest must be a list or an object"):
            _manifest_entries("5")

    def test_non_object_entry_and_invalid_json_are_refused(self):
        with self.assertRaisesRegex(GateError, "every manifest entry must be an object"):
            _manifest_entries("[{}, 1]")
        with self.assertRaisesRegex(GateError, "lane.json: invalid JSON"):
            _manifest_entries("{bad")

    def test_explicit_format_hint_wins_over_the_suffix(self):
        self.assertTrue(manifests._is_jsonl_manifest(Path("m.jsonl"), None))
        self.assertFalse(manifests._is_jsonl_manifest(Path("m.json"), None))
        self.assertFalse(manifests._is_jsonl_manifest(Path("m.jsonl"), "json"))
        self.assertTrue(manifests._is_jsonl_manifest(Path("m.json"), "jsonl"))


def _view(retained=None, digests=None):
    return manifests.RetentionView(retained, digests)


class ManifestRetentionTests(unittest.TestCase):
    def test_content_change_replays_only_with_digest_hash_and_retention(self):
        normalized = {"output_hash": "a"}
        digests = {SOURCE_KEY: "b"}
        replay = manifests._replayable_source_digests
        self.assertIs(replay(normalized, SOURCE_KEY, _view(None, digests)), digests)
        self.assertIsNone(replay(normalized, SOURCE_KEY, _view(None, None)))
        self.assertIsNone(replay(normalized, SOURCE_KEY, _view(None, {})))
        self.assertIsNone(replay({}, SOURCE_KEY, _view(None, digests)))
        self.assertIsNone(replay(normalized, SOURCE_KEY, _view(set(), digests)))

    def test_entry_view_drops_or_recomputes_content_changed(self):
        entry = {"action": "retained", "output_hash": "a", "content_changed": True, "_private": 1}
        dropped = manifests._entry_view(entry, SOURCE_KEY, _view(set(), None))
        self.assertNotIn("content_changed", dropped)
        self.assertNotIn("_private", dropped)
        same = manifests._entry_view(entry, SOURCE_KEY, _view(None, {SOURCE_KEY: "a"}))
        self.assertIs(same["content_changed"], False)

    def test_identity_mapping_needs_a_retained_identity_entry(self):
        lane = {"transform": "curate_identity"}
        retains = manifests._retains_identity_mapping
        self.assertTrue(retains(lane, "retained", SOURCE_KEY, _view()))
        self.assertFalse(retains(lane, "excluded", SOURCE_KEY, _view()))
        self.assertFalse(retains({"transform": "other"}, "retained", SOURCE_KEY, _view()))
        self.assertFalse(retains(lane, "retained", SOURCE_KEY, _view(set())))


def _classify(lowered, normalized, view=None):
    fold = manifests._LaneManifestFold()
    row = manifests._NormalizedEntry(normalized, lowered, SOURCE_KEY)
    manifests._classify_entry(fold, row, view or manifests.RetentionView())
    return fold


class ManifestClassificationTests(unittest.TestCase):
    def test_refusals_are_bucketed_reviewed_and_counted(self):
        excluded = _classify("excluded", {"reason_codes": []})
        self.assertEqual(len(excluded.exclusions), 1)
        self.assertEqual(excluded.reason_counts, {"UNSPECIFIED": 1})
        quarantined = _classify("quarantine", {"reason_codes": ["R"]})
        self.assertEqual(len(quarantined.quarantines), 1)
        self.assertEqual(quarantined.reason_counts, {"R": 1})
        self.assertEqual(len(quarantined.review_candidates), 1)

    def test_retained_change_becomes_a_derived_review_candidate(self):
        changed = _classify("retained", {"reason_codes": [], "content_changed": True})
        self.assertEqual(changed.review_candidates[0]["review_action"], "changed")
        self.assertEqual(
            changed.review_candidates[0]["review_reason_codes"], [manifests.DERIVED_CHANGE_REASON]
        )
        unchanged = _classify("retained", {"reason_codes": [], "content_changed": False})
        self.assertEqual(unchanged.review_candidates, [])
        dropped = _classify("retained", {"content_changed": True}, manifests.RetentionView(set()))
        self.assertEqual(dropped.review_candidates, [])


POINTER_DOCUMENT = {"a/b": {"~": [10, 20]}, "list": [{"k": "v"}]}
GOOD_ID = {"owner_path": "/", "original_ids": [{"path": "/id", "value": "x"}]}
GOOD_PROVENANCE = {"owner_path": "/", "state_path": None, "original": {"o": 1}}


def _pointer_value(pointer):
    return identity_gate._mapping_value(POINTER_DOCUMENT, pointer, "L")


class IdentityPointerTests(unittest.TestCase):
    def test_pointer_resolution(self):
        self.assertIs(_pointer_value("/"), POINTER_DOCUMENT)
        self.assertEqual(_pointer_value("/a~1b/~0/1"), 20)
        self.assertEqual(_pointer_value("/list/0/k"), "v")

    def test_unresolvable_pointers_are_refused(self):
        with self.assertRaisesRegex(GateError, "L must be a JSON pointer"):
            _pointer_value("list")
        for pointer in ("/list/x", "/list/5", "/missing", "/list/0/k/deeper"):
            with (
                self.subTest(pointer=pointer),
                self.assertRaisesRegex(GateError, "L does not resolve"),
            ):
                _pointer_value(pointer)


def _claimed(id_mappings, provenance_mappings):
    entry = {"id_mappings": id_mappings, "provenance_mappings": provenance_mappings}
    return identity_gate._claimed_identity_source_evidence(entry, "E")


class ClaimedIdentityEvidenceTests(unittest.TestCase):
    def test_both_lists_must_be_non_empty_before_either_is_walked(self):
        with self.assertRaisesRegex(GateError, r"E\.id_mappings must be non-empty"):
            _claimed([], [5])
        with self.assertRaisesRegex(GateError, r"E\.provenance_mappings must be non-empty"):
            _claimed([5], None)

    def test_each_claimed_mapping_is_checked_in_order(self):
        cases = (
            ([GOOD_ID, 5], [GOOD_PROVENANCE], r"E\.id_mappings\[2\] must be an object"),
            ([{"original_ids": "x"}], [GOOD_PROVENANCE], r"\[1\]\.original_ids must be a list"),
            ([GOOD_ID], ["x"], r"E\.provenance_mappings\[1\] must be an object"),
            ([GOOD_ID], [{"original": 3}], r"provenance_mappings\[1\]\.original must be an"),
        )
        for id_mappings, provenance, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(GateError, message):
                _claimed(id_mappings, provenance)

    def test_claims_are_copied(self):
        claimed = _claimed([GOOD_ID], [GOOD_PROVENANCE])
        self.assertEqual(claimed["id_mappings"], [GOOD_ID])
        self.assertIsNot(claimed["id_mappings"][0]["original_ids"], GOOD_ID["original_ids"])
        self.assertEqual(claimed["provenance_mappings"], [GOOD_PROVENANCE])


def _provenance_paths(record, kind, owners):
    return identity_gate._identity_provenance_paths(record, kind, owners, "L")


class IdentityProvenancePathTests(unittest.TestCase):
    def test_records_without_state_claims_cover_only_the_root(self):
        record = {"state": {"other": 1}}
        self.assertEqual(_provenance_paths(record, "thalamic", []), [("/", None)])

    def test_state_claims_cover_every_owner_and_the_root_kind(self):
        chosen = {"state": {"sim_or_real": "sim"}}
        rejected = {"state": {"provenance": {}}}
        owners = [("/chosen", chosen), ("/rejected", rejected)]
        self.assertEqual(
            _provenance_paths({}, "preference", owners),
            [("/chosen", "/chosen/state"), ("/rejected", "/rejected/state"), ("/", None)],
        )
        self.assertEqual(
            _provenance_paths({}, "thalamic", owners[:1]), [("/chosen", "/chosen/state")]
        )

    def test_an_owner_without_a_state_object_is_refused(self):
        owners = [("/chosen", {"state": {"sim_or_real": "sim"}}), ("/rejected", {})]
        message = "L/rejected/state does not identify a source object"
        with self.assertRaisesRegex(GateError, message):
            _provenance_paths({}, "preference", owners)


class RewardOntologyGateHelperTests(unittest.TestCase):
    def test_annotation_errors_are_reported_not_raised(self):
        self.assertEqual(reward._annotation_error({}, 1), "unknown reward ontology version")
        self.assertEqual(reward._annotation_error("x", 1), "ontology document must be an object")

    def test_examples_list_missing_annotations_first_and_cap_at_five(self):
        missing = [f"m:{index}" for index in range(3)]
        invalid = [{"source": f"i:{index}", "error": "bad"} for index in range(4)]
        examples = reward._ontology_examples(missing, invalid)
        self.assertEqual(len(examples), 5)
        missing_example = {"source": "m:0", "error": "reward_training annotation missing"}
        self.assertEqual(examples[0], missing_example)
        self.assertEqual(examples[3], {"source": "i:0", "error": "bad"})


def _calibration_lookup(source_record, record_id):
    sidecar = {"source": {"record_id": record_id}}
    return reward._authenticated_calibration_lookup(source_record, sidecar)


class CalibrationLookupTests(unittest.TestCase):
    def test_lookup_prefers_the_authenticated_record_id(self):
        self.assertEqual(_calibration_lookup(None, "Side"), "Side")
        self.assertEqual(_calibration_lookup({"id": " Rec "}, "rec"), "Rec")
        self.assertEqual(_calibration_lookup({"id": "Rec"}, None), "Rec")
        self.assertIsNone(
            reward._authenticated_calibration_lookup(None, {"source": "not-a-mapping"})
        )

    def test_a_sidecar_naming_another_record_is_refused(self):
        message = "sidecar calibration source identity does not match the authenticated record"
        for record, record_id in (({"id": "a"}, "b"), ({"id": "a"}, 5), ({}, "a")):
            with (
                self.subTest(record=record, record_id=record_id),
                self.assertRaisesRegex(RewardOntologyError, message),
            ):
                _calibration_lookup(record, record_id)


def _assert_claims(comparability, annotation):
    derived = {"classification": {"comparability": comparability}, "payload": "P"}
    reward._assert_payload_claims(annotation, derived)


class PayloadClaimTests(unittest.TestCase):
    def test_matching_claims_pass(self):
        _assert_claims(curate_rewards.MAGNITUDE_COMPARABLE, {"magnitude": "P"})
        _assert_claims(curate_rewards.SIGN_ORDER_ONLY, {"order": "P"})
        _assert_claims("excluded", {})

    def test_mismatched_or_extra_claims_are_refused(self):
        cases = (
            (curate_rewards.MAGNITUDE_COMPARABLE, {"magnitude": "Q"}, "canonical magnitude"),
            (curate_rewards.MAGNITUDE_COMPARABLE, {"magnitude": "P", "order": "P"}, "canonical"),
            (curate_rewards.SIGN_ORDER_ONLY, {"order": "Q"}, "preference order does not match"),
            (curate_rewards.SIGN_ORDER_ONLY, {"order": "P", "magnitude": "P"}, "preference order"),
            ("excluded", {"order": "P"}, "excluded reward class must not carry"),
        )
        for comparability, annotation, message in cases:
            with (
                self.subTest(annotation=annotation),
                self.assertRaisesRegex(RewardOntologyError, message),
            ):
                _assert_claims(comparability, annotation)


class SourcePathTests(unittest.TestCase):
    def test_positive_line_numbers(self):
        for value, expected in ((1, True), (0, False), (True, False), ("1", False), (None, False)):
            with self.subTest(value=value):
                self.assertIs(paths.is_positive_line_number(value), expected)

    def test_logical_source_paths(self):
        logical = paths._logical_source_path
        self.assertEqual(logical("x/outputs/raw/run/f/b.jsonl", "L"), "f/b.jsonl")
        self.assertEqual(logical("./f//b.jsonl", "L"), "f/b.jsonl")
        for value, message in (
            ("outputs/raw/run", "does not identify a record below outputs/raw"),
            ("/abs/b.jsonl", "must be relative or identify a path below outputs/raw"),
            ("f/../b.jsonl", "is not a safe logical source path"),
            ("  ", "must be a non-empty source path"),
        ):
            with self.subTest(value=value), self.assertRaisesRegex(GateError, message):
                logical(value, "L")

    def test_trees_overlap(self):
        root = Path("/srv/a")
        self.assertTrue(paths._trees_overlap(root, root))
        self.assertTrue(paths._trees_overlap(root, root / "b"))
        self.assertTrue(paths._trees_overlap(root / "b", root))
        self.assertFalse(paths._trees_overlap(root, Path("/srv/c")))


class SnapshotAndSidecarTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="gate-refusals-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)

    def test_snapshot_refuses_links_directories_and_multiple_links(self):
        regular = self.root / "regular.txt"
        regular.write_bytes(b"hello\n")
        self.assertEqual(digest._read_regular_file_snapshot(regular, "thing")[2], 6)
        (self.root / "link.txt").symlink_to(regular)
        os.link(regular, self.root / "hard.txt")
        cases = (
            (self.root / "link.txt", "cannot open thing .* without following links"),
            (self.root, "thing is not a regular file"),
            (regular, "thing is multiply linked"),
        )
        for path, message in cases:
            with self.subTest(path=path.name), self.assertRaisesRegex(GateError, message):
                digest._read_regular_file_snapshot(path, "thing")

    def test_reward_sidecar_payloads_are_refused_line_by_line(self):
        load = evidence._load_reward_sidecars
        sidecar = Path("side.jsonl")
        cases = (
            (b"\n\n", "reward sidecar artifact is empty"),
            (b"\xff\n", "cannot decode reward sidecars"),
            (b"{x\n", "side.jsonl:1: invalid reward sidecar JSON"),
            (b"\n[]\n", "side.jsonl:2: expected a reward_source_sidecar document"),
            (b'{"document_type": "reward_source_sidecar"}\n', "side.jsonl:1: invalid reward"),
        )
        for payload, message in cases:
            with self.subTest(payload=payload), self.assertRaisesRegex(GateError, message):
                load(sidecar, payload=payload)


if __name__ == "__main__":
    unittest.main()
