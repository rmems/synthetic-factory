#!/usr/bin/env python3
"""Identifier-resolution tests for the read-only payload-kind audit.

Split out of test_payload_kind_audit.py: this concern is how a row's ``id`` is
derived — curate_identity's legacy aliases, their container-major precedence
(owner, then meta, then state), and the thalamic top-level-id fallback — not
what the record classifies as.
"""

import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from payload_kind_audit_fixtures import _episode, _thalamic  # noqa: E402
from payload_kind_audit_test_support import PayloadKindAuditCase  # noqa: E402

import payload_kind_audit  # noqa: E402


class PayloadKindIdentity(PayloadKindAuditCase):
    """Report the identifier the curation lane would recognize; never invent one."""

    def test_episode_identity_uses_every_supported_legacy_key(self):
        for key in payload_kind_audit.LEGACY_ID_KEYS:
            with self.subTest(key=key):
                record = _episode([])
                record[key] = f"{key}-value"
                audit = self._audit_corpus({"episodes.jsonl": [record]})
                self.assertEqual(audit["records"][0]["id"], f"{key}-value")

    def test_episode_identity_uses_the_first_present_supported_key(self):
        record = _episode([])
        for key in reversed(payload_kind_audit.LEGACY_ID_KEYS):
            record[key] = f"{key}-value"
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(
            audit["records"][0]["id"],
            f"{payload_kind_audit.LEGACY_ID_KEYS[0]}-value",
        )

    def test_thalamic_identity_prefers_the_top_level_id_over_state_episode_id(self):
        record = _thalamic("legacy-episode-id", {"summary": "no episode was executed"})
        record["id"] = "canonical-record-id"
        audit = self._audit_corpus({"batch-r02.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "canonical-record-id")

    def test_thalamic_identity_falls_back_to_state_episode_id_without_a_top_level_id(self):
        record = _thalamic("legacy-episode-id", {"summary": "no episode was executed"})
        self.assertNotIn("id", record)
        audit = self._audit_corpus({"batch-r02.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "legacy-episode-id")

    def test_episode_identity_finds_an_identifier_nested_under_meta(self):
        """curate_identity._legacy_ids reads owner, owner.meta and owner.state,
        so an audit that only reads the top level hides an identifier the
        curation lane recognizes (Codex #74)."""
        record = _episode([])
        record["meta"]["record_id"] = "meta-record-id"
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "meta-record-id")

    def test_episode_identity_finds_an_identifier_nested_under_state(self):
        record = _episode([])
        record["state"] = {"episode_id": "state-episode-id"}
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "state-episode-id")

    def test_episode_identity_prefers_a_top_level_alias_over_a_nested_one(self):
        record = _episode([])
        record["trajectory_id"] = "top-level-trajectory-id"
        record["meta"]["id"] = "meta-id"
        record["state"] = {"id": "state-id"}
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "top-level-trajectory-id")

    def test_episode_identity_prefers_a_meta_alias_over_a_state_alias(self):
        record = _episode([])
        record["meta"]["pair_id"] = "meta-pair-id"
        record["state"] = {"id": "state-id"}
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "meta-pair-id")

    def test_a_non_mapping_meta_never_breaks_the_identifier_search(self):
        record = _episode([])
        record["meta"] = "not-an-object"
        record["state"] = {"episode_id": "state-episode-id"}
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "state-episode-id")

    def test_null_id_does_not_shadow_a_later_record_id_alias(self):
        # Membership-only lookup used to return None when id:null was present
        # and hide a usable record_id (NULL-ALIAS-ID-SHADOW / PR #136).
        record = _episode([])
        record["id"] = None
        record["record_id"] = "record-1"
        audit = self._audit_corpus({"episodes.jsonl": [record]})
        self.assertEqual(audit["records"][0]["id"], "record-1")

    def test_first_legacy_id_skips_null_aliases(self):
        self.assertEqual(
            payload_kind_audit._first_legacy_id(
                {"id": None, "record_id": "record-1"}
            ),
            "record-1",
        )
        self.assertIsNone(payload_kind_audit._first_legacy_id({"id": None}))


if __name__ == "__main__":
    unittest.main()
