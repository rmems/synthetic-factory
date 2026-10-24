#!/usr/bin/env python3
"""curate_gate must refuse duplicate content, self-declared kinds, and a future review.

Copies that differ only by id or surrounding whitespace share one content
hash, so integrate blocks them. A payload that names another kind, or
``source_kind`` ``human_verified``, is not evidence. A review dated in the
future does not promote. Honest records, including one whose id borrows
another mill's prefix while ``meta.factory`` matches its folder, still do.

Factory-label disagreement is owned by the separate factory-label gate.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import temp_root  # noqa: E402
from gate_fixture import GateFixture, _episode, _preference, _thalamic  # noqa: E402

_PIPELINES = _TESTS.parent / "pipelines"
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_gate_gates  # noqa: E402
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

    def _run(self, records=None, review_mut=None):
        fixture = GateFixture(self.root, thalamic_records=records)
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

    def _assert_exact_duplicate(self, records):
        integrate, promote, promoted, blockers = self._run(records)
        self.assertNotEqual(integrate, 0, blockers)
        self.assertIsNone(promote)
        self.assertFalse(promoted, blockers)
        self.assertTrue(any(item.startswith("EXACT_DUPLICATES:") for item in blockers), blockers)

    def test_byte_identical_duplicate_is_refused(self):
        self._assert_exact_duplicate(_with(lambda rows: rows.append(_thalamic("t-1"))))

    def test_duplicate_id_only_differs_is_refused(self):
        self._assert_exact_duplicate(_with(lambda rows: rows.append(_thalamic("t-2"))))

    def test_duplicate_trailing_space_is_refused(self):
        self._assert_exact_duplicate(_with(_trailing))

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

    def test_content_identity_ignores_id_sidecar_and_edge_whitespace(self):
        first = _thalamic("t-1")
        second = _thalamic("t-2")
        second["state"]["env"] = "curation gate fixture "
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

    def test_matching_kind_and_synthetic_source_kind_are_not_labels(self):
        record = _thalamic("t-1")
        record["meta"]["kind"] = "thalamic"
        record["source_kind"] = "synthetic"
        self.assertEqual(training_audit.declared_label_errors(record), [])


if __name__ == "__main__":
    unittest.main()
