#!/usr/bin/env python3
"""Emitted-field decimal-guard tests for the read-only payload-kind audit.

Split out of test_payload_kind_audit.py: this concern is the guard on values
the audit republishes verbatim. parse_float turns every JSON decimal into a
binary float, so a decimal in an emitted field — or nested anywhere inside a
container one holds — would be reported, and pinned by --expect, as a value
the corpus does not hold. Integers and strings round-trip exactly and pass.
"""

import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import _episode, _thalamic  # noqa: E402
from payload_kind_audit_test_support import PayloadKindAuditCase  # noqa: E402

# A decimal with more precision than a binary float carries: reporting it
# would round it, so the audit must fail closed instead.
_ROUNDS = 0.1234567890123456789012345


class PayloadKindDecimalGuard(PayloadKindAuditCase):
    """Reject any emitted decimal a binary float cannot carry back out unchanged."""

    def test_record_identifiers_that_a_float_would_round_are_rejected(self):
        self._assert_rejects_raw_payload(
            "episodes.jsonl",
            '{"id":0.1234567890123456789012345,"goal":"g","steps":[]}\n',
            "JSON decimal this audit cannot report exactly",
        )

    def test_thalamic_identifiers_that_a_float_would_round_are_rejected(self):
        record = _thalamic("act-r02-001", _episode([]))
        record["id"] = _ROUNDS
        self._assert_rejects_corpus(
            {"batch-r02.jsonl": [record]},
            "batch-r02.jsonl:1",
            "JSON decimal this audit cannot report exactly",
        )

    def test_emitted_gate_metadata_that_a_float_would_round_is_rejected(self):
        """Every field the audit republishes must survive the round trip, not
        just the identifier: --expect rounds a published decimal identically,
        so altered evidence would compare equal (Codex #74)."""
        for field, record in (
            ("supervisor_id", _thalamic("act-r02-001", _episode([]), supervisor=_ROUNDS)),
            ("gate_decision", _thalamic("act-r02-001", _episode([]), decision=_ROUNDS)),
        ):
            with self.subTest(field=field):
                self._assert_rejects_corpus(
                    {"batch-r02.jsonl": [record]},
                    "batch-r02.jsonl:1",
                    f"record {field} is a JSON decimal",
                )

    def test_a_decimal_domain_is_rejected_like_every_other_emitted_field(self):
        record = _thalamic("act-r02-001", _episode([]))
        record["state"]["domain"] = _ROUNDS
        self._assert_rejects_corpus(
            {"batch-r02.jsonl": [record]},
            "batch-r02.jsonl:1",
            "record domain is a JSON decimal",
        )

    def test_a_decimal_nested_in_a_list_valued_identifier_is_rejected(self):
        """A container-valued emitted field is republished verbatim, so a
        decimal inside it is altered corpus data that --expect would round
        identically and therefore accept (Codex #74)."""
        record = _episode([])
        record["id"] = [_ROUNDS]
        self._assert_rejects_corpus(
            {"episodes.jsonl": [record]},
            "episodes.jsonl:1",
            "record id[0] is a JSON decimal",
        )

    def test_a_decimal_nested_in_an_object_valued_domain_is_rejected(self):
        record = _thalamic("act-r02-001", _episode([]))
        record["state"]["domain"] = {"score": _ROUNDS}
        self._assert_rejects_corpus(
            {"batch-r02.jsonl": [record]},
            "batch-r02.jsonl:1",
            "record domain.score is a JSON decimal",
        )

    def test_string_gate_metadata_is_untouched_by_the_decimal_guard(self):
        record = _thalamic("act-r02-001", _episode([]), supervisor="gate-v1", decision="MODIFY")
        audit = self._audit_corpus({"batch-r02.jsonl": [record]})
        row = audit["records"][0]
        self.assertEqual(row["supervisor_id"], "gate-v1")
        self.assertEqual(row["gate_decision"], "MODIFY")

    def test_integer_record_identifiers_round_trip_and_are_kept(self):
        record = _episode([])
        record["id"] = 12345678901234567890
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], 12345678901234567890)

    def test_a_container_metadata_value_without_a_decimal_is_kept(self):
        """The recursive guard rejects decimals, not containers: an emitted
        list of strings still round-trips exactly and must survive."""
        record = _thalamic("act-r02-001", _episode([]))
        record["state"]["domain"] = ["software_engineering", "demo"]
        audit = self._audit_corpus({"batch-r02.jsonl": [record]})
        self.assertEqual(audit["records"][0]["domain"], ["software_engineering", "demo"])


if __name__ == "__main__":
    unittest.main()
