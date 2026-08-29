#!/usr/bin/env python3
"""VSET release-manifest fail-closed tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import (  # noqa: E402
    MANIFEST,
    codes as _codes,
    load_record as _load,
    vset,
)

class ReleaseManifestTests(unittest.TestCase):
    def test_pilot_manifest_retains_actor_graph_and_pins(self):
        manifest = _load(MANIFEST)
        self.assertEqual(_codes(vset.validate_manifest(manifest)), [])
        pin = vset.registry_pin()
        self.assertEqual(manifest["factory_contract_version"], pin["schema_version"])
        self.assertEqual(manifest["factory_registry_sha256"], pin["sha256"])
        self.assertEqual(manifest["manifest_hash"], vset.manifest_body_hash(manifest))
        self.assertEqual(manifest["counts"]["invalid_or_impossible"], 1)
        statuses = {entry["oracle"]["status"] for entry in manifest["entries"]}
        self.assertEqual(statuses, {"validated", "invalid"})
        for entry in manifest["entries"]:
            for role in vset.MANIFEST_ROLES:
                self.assertIn(role, entry)
            self.assertIn("source_kind", entry)
            self.assertTrue(entry["environment"]["repo_snapshot_hash"].startswith("sha256:"))
            if entry["oracle"]["status"] == "validated":
                self.assertTrue(entry["oracle"]["result_hash"].startswith("sha256:"))

    def test_dropping_an_impossible_entry_fails_closed(self):
        manifest = _load(MANIFEST)
        kept = [
            entry
            for entry in manifest["entries"]
            if not vset._is_invalid_or_impossible(entry)
        ]
        manifest["entries"] = kept
        manifest["counts"]["records"] = 1
        manifest["counts"]["by_record_kind"] = {
            "issue_patch_v1": 1,
            "review_remediation_v1": 0,
            "failure_recovery_v1": 0,
        }
        manifest["counts"]["by_oracle_status"] = {
            "invalid": 0,
            "provisional": 0,
            "validated": 1,
        }
        manifest["counts"]["by_curation_decision"] = {
            "accept": 1,
            "exclude": 0,
            "measure": 0,
        }
        manifest["counts"]["invalid_or_impossible"] = 0
        # A release that forgets to report the field is the silent-drop case.
        del manifest["counts"]["invalid_or_impossible"]
        manifest["manifest_hash"] = vset.manifest_body_hash(manifest)
        self.assertIn("vset.payload_invalid", _codes(vset.validate_manifest(manifest)))

    def test_missing_manifest_actor_role_is_vset_not_identity(self):
        manifest = _load(MANIFEST)
        del manifest["entries"][0]["solver"]
        codes = _codes(vset.validate_manifest(manifest))
        self.assertIn("vset.missing_actor_role", codes)
        self.assertNotIn(vset.IDENTITY_UNRESOLVED_PROVENANCE, codes)

    def test_identity_reason_on_a_manifest_entry_fails_closed(self):
        manifest = _load(MANIFEST)
        manifest["entries"][0]["curation"]["reason_codes"] = [
            vset.IDENTITY_UNRESOLVED_PROVENANCE
        ]
        self.assertIn(
            "vset.identity_reason_collision", _codes(vset.validate_manifest(manifest))
        )

    def test_wrong_manifest_hash_fails_closed(self):
        manifest = _load(MANIFEST)
        manifest["manifest_hash"] = "sha256:" + ("ab" * 32)
        self.assertIn(
            "vset.release_contract_mismatch", _codes(vset.validate_manifest(manifest))
        )
