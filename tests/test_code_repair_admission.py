"""Admission authority must come from reviewed bytes, never caller claims."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.test_curate_identity import identity as ci
from code_repair import source_policy as policy
from record_kind import classify_kind


class ProceduralRegistryTests(unittest.TestCase):
    def test_trusted_catalog_snapshots_isolate_mutable_source_and_metadata(self):
        from code_repair import admission
        try:
            first = admission.load_trusted_catalog()
        except TypeError as exc:
            self.fail(f"trusted catalog must support immutable hidden cases: {exc}")
        second = admission.load_trusted_catalog()
        first.meta["upstream"]["repository"] = "unreviewed/project"
        first.meta["split_policy"]["weights"]["train"] = 0
        first.programs[0].upstream["repository"] = "unreviewed/project"
        first.programs[0].upstream["line_span"][0] = -1
        with self.assertRaises(TypeError):
            first.programs[0].cases[0]["want"] = "forged"
        fresh = admission.load_trusted_catalog()
        self.assertEqual(fresh, second)
        self.assertEqual(fresh.meta["upstream"]["repository"], "TheAlgorithms/Python")
        self.assertEqual(fresh.programs[0].upstream["repository"], "TheAlgorithms/Python")
        self.assertGreater(fresh.meta["split_policy"]["weights"]["train"], 0)

    def load_changed(self, change):
        value = json.loads(ci.FACTORY_REGISTRY_PATH.read_text())
        change(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(value))
            return ci.load_registry(path)

    def test_default_registry_admits_local_generator_without_hosted_provider(self):
        row = ci.load_registry().by_path_id.get("python-function-repair-factory")
        self.assertIsNotNone(row, "reviewed procedural route must be visible to default callers")
        self.assertIsNone(row.provider)
        self.assertIsNone(row.channel)
        self.assertEqual(row.intended_use, "training_candidate")
        self.assertEqual(row.project_training_policy, "allowed")

    def test_unreviewed_generator_or_license_cannot_grant_training_permission(self):
        for key, bad in (("generator", "invented"), ("source_license_evidence", {}),
                         ("procedural_policy_sha256", "0" * 64),
                         ("identity_authoritative", 1)):
            with self.subTest(key=key), self.assertRaises(ci.IdentityCurationError):
                self.load_changed(lambda value, key=key, bad=bad:
                                  value["factories"][-1].update({key: bad}))

    def test_old_schema_refuses_procedural_fields_on_hosted_row(self):
        for version in ("factory-registry-v0.1", "factory-registry-v0.2"):
            def change(value, version=version):
                value["schema_version"] = version
                value["factories"] = [value["factories"][0]]
                value["factories"][0]["generation_method"] = "deterministic_execution"
            with self.subTest(version=version), self.assertRaises(ci.IdentityCurationError):
                self.load_changed(change)

    def test_hosted_rows_keep_blocked_policy(self):
        rows = ci.load_registry().by_path_id.values()
        for row in rows:
            if row.path_id != "python-function-repair-factory":
                self.assertEqual((row.intended_use, row.project_training_policy),
                                 ("research_only", "blocked"))

    def test_self_consistent_changed_policy_is_not_an_authority(self):
        value = json.loads(policy.POLICY_PATH.read_text())
        value["generator"] = "unreviewed-generator"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps(value))
            with self.assertRaises(policy.SourcePolicyError):
                policy.load_policy(path)
        with self.assertRaises(TypeError):
            policy.POLICY["source_license_evidence"]["license"] = "unknown"

    def test_malformed_family_claim_cannot_escape_to_episode_shape(self):
        self.assertEqual(classify_kind({"family": "python-function-repair", "goal": "x",
                                        "steps": [], "result": []}), "code_repair")

    def test_supplied_source_json_remains_the_identity_snapshot_without_a_digest(self):
        record = {"family": "python-function-repair"}
        raw = '{"family": "python-function-repair"}  '
        # Exclusion still carries its exact source snapshot for later replay.
        result = ci.curate_record(ci.SourceRecord(
            record, "unknown-factory/candidates.jsonl", 1, source_json=raw,
        ))
        self.assertEqual(result.mapping["source"]["original"], raw)
        self.assertEqual(result.mapping["source"]["hash_basis"], "source-json-line-sha256")


if __name__ == "__main__":
    unittest.main()
