#!/usr/bin/env python3
"""Record-kind classification tests for the read-only payload-kind audit.

One concern per module: identifier resolution lives in
test_payload_kind_audit_identity.py, fail-closed corpus parsing in
test_payload_kind_audit_parsing.py, the emitted-field decimal guard in
test_payload_kind_audit_decimal_guard.py, Markdown rendering in
test_payload_kind_audit_markdown.py, and the CLI (--json/--expect) in
test_payload_kind_audit_cli.py. The published #74 finding itself is pinned in
test_payload_kind_audit_published.py (committed evidence) and
test_payload_kind_audit_fidelity.py (raw-corpus re-derivation).
"""

import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import _episode, _step, _thalamic  # noqa: E402
from payload_kind_audit_test_support import PayloadKindAuditCase  # noqa: E402


class PayloadKindClassification(PayloadKindAuditCase):
    """The auditor measures the mix; it never guesses at an unknown shape."""

    def test_a_mixed_corpus_reports_both_kinds_and_where_they_live(self):
        audit = self._audit_corpus(
            {
                "batch-r02.jsonl": [
                    _thalamic("act-r02-001", _episode([_step(1, thought="t")])),
                    _thalamic(
                        "act-r02-002",
                        _episode([_step(1, thought="t"), _step(2, thought="t")]),
                        supervisor="gate-v2",
                        decision="REJECT",
                    ),
                ],
                # Legacy payload filename: it does not match batch-r*.jsonl and is
                # exactly what a batch-only glob drops.
                "episodes.jsonl": [
                    _episode([_step(1, decision_basis="b"), _step(2, decision_basis="b")])
                ],
            }
        )

        self.assertEqual(audit["summary"]["files"], 2)
        self.assertEqual(audit["summary"]["records"], 3)
        self.assertEqual(audit["summary"]["kinds"], {"episode": 1, "thalamic": 2})
        self.assertEqual(
            audit["summary"]["meta_factory_stamps"],
            {"agentic-coding-trajectory-factory": 3},
        )
        self.assertEqual(audit["summary"]["thalamic_records_wrapping_a_coding_episode"], 2)
        self.assertEqual(audit["summary"]["coding_episodes_reachable_at_top_level"], 1)
        self.assertEqual(audit["summary"]["coding_episodes_including_wrapped"], 3)
        self.assertEqual(audit["summary"]["coding_steps"], {"native": 2, "wrapped": 3, "total": 5})
        self.assertEqual(
            audit["summary"]["coding_steps_by_reasoning_field"],
            {"decision_basis": 2, "reflection": 0, "thought": 3},
        )

        by_source = {(row["source_file"], row["source_line"]): row for row in audit["records"]}
        self.assertEqual(by_source[("batch-r02.jsonl", 1)]["id"], "act-r02-001")
        self.assertEqual(by_source[("batch-r02.jsonl", 2)]["gate_decision"], "REJECT")
        self.assertEqual(by_source[("batch-r02.jsonl", 2)]["supervisor_id"], "gate-v2")
        # An episode record in this lane carries no top-level id, and the audit
        # reports that rather than inventing one.
        self.assertIsNone(by_source[("episodes.jsonl", 1)]["id"])
        self.assertFalse(by_source[("episodes.jsonl", 1)]["wraps_coding_episode"])

        files = {entry["path"]: entry for entry in audit["files"]}
        self.assertEqual(files["episodes.jsonl"]["kinds"], {"episode": 1})
        self.assertEqual(files["batch-r02.jsonl"]["kinds"], {"thalamic": 2})

    def test_a_gate_record_without_a_wrapped_episode_is_reported_as_such(self):
        audit = self._audit_corpus(
            {"batch-r02.jsonl": [_thalamic("act-r02-001", {"summary": "no episode was executed"})]}
        )
        row = audit["records"][0]
        self.assertEqual(row["kind"], "thalamic")
        self.assertFalse(row["wraps_coding_episode"])
        self.assertEqual(row["coding_steps"], 0)
        self.assertEqual(audit["summary"]["thalamic_records_wrapping_a_coding_episode"], 0)
        self.assertEqual(audit["summary"]["coding_episodes_including_wrapped"], 0)

    def test_steps_without_a_goal_are_not_counted_as_a_wrapped_episode(self):
        audit = self._audit_corpus(
            {"batch-r02.jsonl": [_thalamic("act-r02-001", {"steps": [_step(1)]})]}
        )
        self.assertFalse(audit["records"][0]["wraps_coding_episode"])
        self.assertEqual(audit["records"][0]["coding_steps"], 0)
        self.assertEqual(
            audit["summary"]["coding_steps"],
            {"native": 0, "wrapped": 0, "total": 0},
        )

    def test_malformed_gate_metadata_containers_fail_closed(self):
        for field in ("state", "safety_decision"):
            with self.subTest(field=field):
                record = _thalamic("act-r02-001", {"summary": "no episode"})
                record[field] = "not-an-object"
                self._assert_rejects_corpus(
                    {"batch-r02.jsonl": [record]},
                    f"batch-r02.jsonl:1.{field} must be a JSON object",
                )

    def test_malformed_episode_step_containers_fail_closed(self):
        malformed = (
            _episode("not-a-list"),
            _episode([_step(1), "not-an-object"]),
        )
        for record in malformed:
            with self.subTest(steps=record["steps"]):
                self._assert_rejects_corpus(
                    {"episodes.jsonl": [record]}, "episodes.jsonl:1.steps"
                )

    def test_other_valid_curation_kinds_are_rejected_not_misreported_as_episodes(self):
        preference = {
            "id": "pair-1",
            "chosen": _episode([_step(1)]),
            "rejected": _episode([_step(1)]),
        }
        bridge = {
            "language_view": {"trajectory": _thalamic("bridge-1", _episode([_step(1)]))},
            "spike_events": [],
        }
        for record, kind in ((preference, "preference"), (bridge, "bridge_pair")):
            with self.subTest(kind=kind):
                self._assert_rejects_corpus(
                    {"batch-r01.jsonl": [record]}, f"payload kind '{kind}'"
                )

    def test_a_record_the_lane_cannot_classify_fails_loudly_with_its_coordinate(self):
        self._assert_rejects_corpus({"batch-r02.jsonl": [{"who": "knows"}]}, "batch-r02.jsonl:1")


if __name__ == "__main__":
    unittest.main()
