#!/usr/bin/env python3
"""curate_gate must refuse duplicate content, self-declared kinds, and a future review.

Copies that differ only by id share one content hash, so integrate blocks
them. Meaningful edge whitespace in content is kept, which revises #535.
A payload that names another kind, or ``source_kind`` ``human_verified``
under any listed respelling, is not evidence. A review dated in the future
does not promote. Honest records, including one whose id borrows another
mill's prefix while ``meta.factory`` matches its folder, still do.

Factory-label disagreement is owned by the separate factory-label gate.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import temp_root  # noqa: E402
from gate_fixture import GateFixture, _bridge, _episode, _preference, _thalamic  # noqa: E402

_PIPELINES = _TESTS.parent / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_gate_gates  # noqa: E402
import curate_gate_review  # noqa: E402
import training_audit  # noqa: E402

_RIGHTS_PASS = mock.patch.object(
    curate_gate_gates,
    "evaluate_rights",
    return_value=({"passed": True, "enforced": False}, []),
)


def _base():
    return [_thalamic("t-1"), _preference(), _episode()]


def _with(mutate):
    records = _base()
    mutate(records)
    return records


def _trailing(records):
    twin = _thalamic("t-2")
    twin["state"]["env"] = "curation gate fixture "
    records.append(twin)


def _labels(records):
    records[0]["meta"]["kind"] = "preference"
    records[0]["source_kind"] = "human_verified"


def _manifest_blockers(fixture):
    try:
        manifest = fixture.manifest()
    except (OSError, ValueError):
        return []
    blockers = list(manifest.get("blockers") or [])
    audit = (manifest.get("gates") or {}).get("training_audit") or {}
    blockers.extend(audit.get("blockers") or [])
    return blockers


def _written_review(fixture, review_mut):
    review = fixture.accepted_review()
    if review_mut is None:
        return review
    document = json.loads(review.read_text())
    review_mut(document)
    review.write_text(json.dumps(document))
    return review


def _promotion(report):
    if not isinstance(report, dict):
        return False, []
    return bool(report.get("promoted")), list(report.get("blockers") or [])


class ForgedRecordTests(unittest.TestCase):
    def setUp(self):
        self.root = temp_root(self)
        self.enterContext(_RIGHTS_PASS)

    def _run(self, records=None, review_mut=None, bridge_records=None):
        kwargs = {}
        if records is not None:
            kwargs["thalamic_records"] = records
        if bridge_records is not None:
            kwargs["bridge_records"] = bridge_records
        fixture = GateFixture(self.root, **kwargs)
        integrate_code = fixture.integrate()
        blockers = _manifest_blockers(fixture)
        if integrate_code != 0:
            return integrate_code, None, False, blockers
        review = _written_review(fixture, review_mut)
        promote_code, report, _stderr = fixture.promote_report(review)
        promoted, extra = _promotion(report)
        return integrate_code, promote_code, promoted, blockers + extra

    def test_honest_records_promote(self):
        integrate_code, promote_code, promoted, blockers = self._run()
        self.assertEqual((integrate_code, promote_code, promoted), (0, 0, True), blockers)

    def test_borrowed_id_prefix_with_matching_factory_promotes(self):
        def _leftover(records):
            records[0]["id"] = "dbc-r3714-buildkit-cache-mount-id-leftover"
            records[0]["meta"]["factory"] = "thalamic-mini"

        integrate_code, promote_code, promoted, blockers = self._run(_with(_leftover))
        self.assertEqual((integrate_code, promote_code, promoted), (0, 0, True), blockers)

    def _assert_blocked_duplicates(self, integrate, promote, promoted, blockers):
        self.assertNotEqual(integrate, 0, blockers)
        self.assertIsNone(promote)
        self.assertFalse(promoted, blockers)
        self.assertTrue(any(item.startswith("EXACT_DUPLICATES:") for item in blockers), blockers)

    def _assert_exact_duplicate(self, records):
        self._assert_blocked_duplicates(*self._run(records))

    def _assert_exact_duplicate_bridges(self, bridges):
        self._assert_blocked_duplicates(*self._run(bridge_records=bridges))

    def test_byte_identical_duplicate_is_refused(self):
        self._assert_exact_duplicate(_with(lambda rows: rows.append(_thalamic("t-1"))))

    def test_duplicate_id_only_differs_is_refused(self):
        self._assert_exact_duplicate(_with(lambda rows: rows.append(_thalamic("t-2"))))

    def test_meaningful_trailing_whitespace_is_kept_apart(self):
        integrate, promote, promoted, blockers = self._run(_with(_trailing))
        self.assertEqual((integrate, promote, promoted), (0, 0, True), blockers)

    def test_self_declared_kind_preference_human_verified_is_refused(self):
        labeled = _thalamic("t-1")
        labeled["meta"]["kind"] = "preference"
        labeled["source_kind"] = "human_verified"
        errors = training_audit.declared_label_errors(labeled)
        self.assertIn("DECLARED_KIND_MISMATCH:preference!=thalamic", errors)
        self.assertIn("DECLARED_SOURCE_KIND:human_verified", errors)

        integrate, promote, promoted, blockers = self._run(_with(_labels))
        self.assertNotEqual(integrate, 0, blockers)
        self.assertIsNone(promote)
        self.assertFalse(promoted, blockers)
        self.assertTrue(
            any("record shape/invariant errors" in item for item in blockers),
            blockers,
        )

    def test_review_dated_2099_is_refused(self):
        integrate_code, promote_code, promoted, blockers = self._run(
            None,
            lambda document: document.update(reviewed_at="2099-01-01T00:00:00Z"),
        )
        self.assertEqual(integrate_code, 0, blockers)
        self.assertEqual(promote_code, 1, blockers)
        self.assertFalse(promoted, blockers)
        self.assertIn("REVIEW_REVIEWED_AT_FUTURE", blockers)

    def test_near_future_review_is_refused_through_promote(self):
        soon = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=30)
        stamp = soon.strftime("%Y-%m-%dT%H:%M:%SZ")
        integrate_code, promote_code, promoted, blockers = self._run(
            None,
            lambda document, value=stamp: document.update(reviewed_at=value),
        )
        self.assertEqual(integrate_code, 0, blockers)
        self.assertEqual(promote_code, 1, blockers)
        self.assertFalse(promoted, blockers)
        self.assertIn("REVIEW_REVIEWED_AT_FUTURE", blockers)

    def test_nul_trailing_review_date_is_invalid_through_promote(self):
        forged = "2026-08-23T00:00:00Z\x00not a date: 2099-12-31T00:00:00Z"
        integrate_code, promote_code, promoted, blockers = self._run(
            None,
            lambda document: document.update(reviewed_at=forged),
        )
        self.assertEqual(integrate_code, 0, blockers)
        self.assertEqual(promote_code, 1, blockers)
        self.assertFalse(promoted, blockers)
        self.assertIn("REVIEW_REVIEWED_AT_INVALID", blockers)

    def test_lowercase_z_review_date_promotes(self):
        integrate_code, promote_code, promoted, blockers = self._run(
            None,
            lambda document: document.update(reviewed_at="2026-08-23T00:00:00z"),
        )
        self.assertEqual((integrate_code, promote_code, promoted), (0, 0, True), blockers)

    def test_content_identity_ignores_id_and_sidecar(self):
        first = _thalamic("t-1")
        second = _thalamic("t-2")
        first["reward_training"] = {"source_sidecar_id": "sha256:aaa"}
        second["reward_training"] = {"source_sidecar_id": "sha256:bbb"}
        self.assertEqual(
            training_audit.content_identity_blob(first),
            training_audit.content_identity_blob(second),
        )
        changed = _thalamic("t-3")
        changed["state"]["env"] = "other fixture"
        self.assertNotEqual(
            training_audit.content_identity_blob(first),
            training_audit.content_identity_blob(changed),
        )
        nested = _thalamic("t-4")
        nested["note"] = {"id": "step-a"}
        other_nested = _thalamic("t-4")
        other_nested["note"] = {"id": "step-b"}
        self.assertNotEqual(
            training_audit.content_identity_blob(nested),
            training_audit.content_identity_blob(other_nested),
        )
        chosen = {"id": "left", "chosen": {"id": "c1", "text": "a"}, "rejected": {"id": "r1"}}
        other_chosen = {"id": "right", "chosen": {"id": "c2", "text": "a"}, "rejected": {"id": "r2"}}
        self.assertEqual(
            training_audit.content_identity_blob(chosen),
            training_audit.content_identity_blob(other_chosen),
        )

    def test_content_identity_keeps_meaningful_edge_whitespace(self):
        flush = {"id": "a", "body": "return cache[key]"}
        indented = {"id": "b", "body": "    return cache[key]"}
        self.assertNotEqual(
            training_audit.content_identity_blob(flush),
            training_audit.content_identity_blob(indented),
        )
        bare = {"id": "a", "body": "print(1)"}
        newline = {"id": "b", "body": "print(1)\n"}
        self.assertNotEqual(
            training_audit.content_identity_blob(bare),
            training_audit.content_identity_blob(newline),
        )

    def test_bridge_trajectory_id_is_stamped_out_of_identity(self):
        first = _bridge("b-1")
        second = copy.deepcopy(first)
        second["id"] = "b-2"
        second["language_view"]["trajectory"]["id"] = "other-trajectory"
        self.assertEqual(
            training_audit.content_identity_blob(first),
            training_audit.content_identity_blob(second),
        )
        self._assert_exact_duplicate_bridges([first, second])

    def test_review_date_edges_and_list_element_ids(self):
        self.assertIsNone(curate_gate_review._reviewed_at_blocker({}))
        self.assertIsNone(curate_gate_review._reviewed_at_blocker({"reviewed_at": ""}))
        self.assertIsNone(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": "2026-08-23T00:00:00z"})
        )
        self.assertEqual(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": "2026-08-23T00:00:00"}),
            "REVIEW_REVIEWED_AT_INVALID",
        )
        self.assertEqual(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": "   "}),
            "REVIEW_REVIEWED_AT_INVALID",
        )
        self.assertEqual(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": 12}),
            "REVIEW_REVIEWED_AT_INVALID",
        )
        self.assertEqual(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": "yesterday"}),
            "REVIEW_REVIEWED_AT_INVALID",
        )
        self.assertEqual(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": "2016-12-31T23:59:60Z"}),
            "REVIEW_REVIEWED_AT_INVALID",
        )
        self.assertEqual(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": "0001-01-01T00:00:00+01:00"}),
            "REVIEW_REVIEWED_AT_INVALID",
        )
        self.assertEqual(
            curate_gate_review._reviewed_at_blocker({"reviewed_at": "9999-12-31T23:59:59-01:00"}),
            "REVIEW_REVIEWED_AT_INVALID",
        )
        rows = {"id": "a", "chosen": [{"id": "arm-1", "text": "x"}]}
        other = {"id": "a", "chosen": [{"id": "arm-2", "text": "x"}]}
        self.assertNotEqual(
            training_audit.content_identity_blob(rows),
            training_audit.content_identity_blob(other),
        )
        self.assertEqual(training_audit.declared_label_errors(["nope"]), [])

    def test_matching_kind_and_synthetic_source_kind_are_not_labels(self):
        record = _thalamic("t-1")
        record["meta"]["kind"] = "thalamic"
        record["source_kind"] = "synthetic"
        self.assertEqual(training_audit.declared_label_errors(record), [])

    def test_each_kind_claim_path_is_read(self):
        for path in (("record_kind",), ("meta", "kind"), ("meta", "record_kind")):
            with self.subTest(path=path):
                record = _thalamic("t-1")
                _assign(record, path, "Preference")
                errors = training_audit.declared_label_errors(record)
                self.assertIn("DECLARED_KIND_MISMATCH:preference!=thalamic", errors)

    def test_each_source_kind_claim_path_is_read(self):
        paths = (
            ("source_kind",),
            ("meta", "source_kind"),
            ("provenance", "source_kind"),
            ("meta", "provenance", "source_kind"),
        )
        for path in paths:
            with self.subTest(path=path):
                record = _thalamic("t-1")
                _assign(record, path, "human_verified")
                errors = training_audit.declared_label_errors(record)
                self.assertIn("DECLARED_SOURCE_KIND:human_verified", errors)

    def test_respelled_human_verified_claims_are_refused(self):
        samples = (
            "HUMAN_VERIFIED",
            "Human_Verified",
            "human-verified",
            "human verified",
            " human_verified ",
            "human_\u200bverified",
        )
        for claim in samples:
            with self.subTest(claim=repr(claim)):
                record = _thalamic("t-1")
                record["source_kind"] = claim
                errors = training_audit.declared_label_errors(record)
                self.assertIn("DECLARED_SOURCE_KIND:human_verified", errors)

    def test_non_string_claim_at_source_kind_is_refused(self):
        record = _thalamic("t-1")
        record["source_kind"] = ["human_verified"]
        errors = training_audit.declared_label_errors(record)
        self.assertIn("DECLARED_SOURCE_KIND:non-string", errors)
        record = _thalamic("t-2")
        record["meta"]["kind"] = ["preference"]
        errors = training_audit.declared_label_errors(record)
        self.assertIn("DECLARED_KIND_MISMATCH:non-string!=thalamic", errors)


def _assign(record, path, value):
    current = record
    for key in path[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    current[path[-1]] = value


if __name__ == "__main__":
    unittest.main()
