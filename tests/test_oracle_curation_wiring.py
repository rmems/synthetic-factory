#!/usr/bin/env python3
"""End-to-end wiring for oracle-grounded records: kind, routes, registry, curation.

Generation and oracle validation already work; this module pins the
downstream integration that carries generated records to training-ready
curated data: payload-first classification, the validate_run shape route,
the sealed procedural registry row, and the preserving identity lane.
"""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import validate_run  # noqa: E402
from oracle_grounded import record as oracle_record  # noqa: E402
from oracle_grounded import source_policy as oracle_policy  # noqa: E402
from record_kind import classify_kind  # noqa: E402
import curate_identity as identity  # noqa: E402

FAMILY = "spike-encoder-equivalence-pairs"
SOURCE_PATH = f"oracle-grounded/{FAMILY}/accepted-r01.jsonl"


def _build(seed=7):
    """One deterministic accepted record from the reference oracle."""
    return oracle_record.build_record(FAMILY, 0, seed, round_number=1)


class OracleKindTests(unittest.TestCase):
    def test_generated_record_classifies_oracle(self):
        self.assertEqual(classify_kind(_build()), "oracle")

    def test_rejected_record_shares_the_oracle_kind(self):
        record = _build()
        record["candidate_prediction"] = {"not": "a prediction"}
        record["validation"] = oracle_record.assess(record)
        self.assertEqual(record["validation"]["status"], "rejected")
        self.assertEqual(classify_kind(record), "oracle")

    def test_route_accepts_clean_record(self):
        record = _build()
        errors, kind = validate_run.check_line(record, "accepted-r01.jsonl:1")
        self.assertEqual(kind, "oracle")
        self.assertEqual(errors, [])

    def test_route_catches_misfiled_verdict(self):
        record = _build()
        errors, kind = validate_run.check_line(record, "rejected-r01.jsonl:1")
        self.assertEqual(kind, "oracle")
        self.assertTrue(any("reserved for 'rejected' records" in e for e in errors), errors)


class OracleRegistryTests(unittest.TestCase):
    def test_committed_registry_carries_the_oracle_row(self):
        registry = identity.default_registry()
        row = registry.by_path_id.get("oracle-grounded")
        self.assertIsNotNone(row)
        self.assertEqual(sorted(row.record_kinds), ["oracle"])
        self.assertEqual(row.payload_factory, "oracle-grounded")
        self.assertEqual(row.source_type, "procedural")
        self.assertEqual(list(row.allowed_curation_lanes), ["curate_identity"])
        self.assertEqual(
            row.provenance_contract_by_kind.get("oracle"), "synthetic_shape_implies_designed"
        )
        self.assertIsNone(row.provider)
        self.assertIsNone(row.channel)

    def test_policy_seal_rejects_tampered_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tampered = Path(tmp) / "policy.json"
            raw = oracle_policy.POLICY_PATH.read_bytes().replace(b"training_candidate", b"research_only")
            tampered.write_bytes(raw)
            with self.assertRaises(oracle_policy.SourcePolicyError):
                oracle_policy.load_policy(tampered)

    def test_catalog_sha256_authenticates_the_committed_package(self):
        """The pin must match a recomputation, not merely be well-formed.

        The domain excludes source_policy.py: that module is the trust anchor
        carrying POLICY_SHA256, so hashing it into the catalog the anchor seals
        would make the digest a self-referential cycle with no stable value.
        """
        package = REPO / "pipelines/oracle_grounded"
        domain = sorted(
            (path for path in package.glob("*.py") if path.name != "source_policy.py"),
            key=lambda path: path.name,
        )
        digest = hashlib.sha256()
        for path in domain:
            digest.update(path.read_bytes())
        self.assertEqual(oracle_policy.POLICY["catalog_sha256"], digest.hexdigest())

    def test_programs_sha256_pins_the_pipeline_entry_points(self):
        digest = hashlib.sha256()
        for name in ("oracle_generate.py", "oracle_validate.py"):
            digest.update((REPO / "pipelines" / name).read_bytes())
        self.assertEqual(oracle_policy.POLICY["programs_sha256"], digest.hexdigest())

    def test_mutated_row_fails_registry_load(self):
        payload = json.loads(identity.FACTORY_REGISTRY_PATH.read_text(encoding="utf-8"))
        for row in payload["factories"]:
            if row.get("path_id") == "oracle-grounded":
                row["training_ready_policy"] = "never"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(identity.IdentityCurationError):
                identity.load_registry(path)


class OracleCurationTests(unittest.TestCase):
    def _curate(self, record, line=1):
        source = identity.SourceRecord(
            record=record, source_path=SOURCE_PATH, source_line=line
        )
        return identity.curate_record(source, registry=identity.default_registry())

    def test_accepted_record_retained_byte_identical_and_eligible(self):
        record = _build()
        result = self._curate(record)
        self.assertEqual(result.action, "retained")
        self.assertEqual(
            identity.canonical_json(result.record), identity.canonical_json(record)
        )
        authority = result.mapping.get("procedural_authority", {})
        self.assertTrue(authority.get("eligible_training_candidate"), authority)
        self.assertEqual(authority.get("ineligibility_reasons"), [])

    def test_rejected_record_retained_but_ineligible(self):
        record = _build()
        record["candidate_prediction"] = {"not": "a prediction"}
        record["validation"] = oracle_record.assess(record)
        self.assertEqual(record["validation"]["status"], "rejected")
        result = self._curate(record)
        self.assertEqual(result.action, "retained")
        authority = result.mapping.get("procedural_authority", {})
        self.assertFalse(authority.get("eligible_training_candidate"), authority)
        self.assertTrue(authority.get("ineligibility_reasons"), authority)

    def test_malformed_validation_block_excluded(self):
        record = _build()
        del record["validation"]
        result = self._curate(record)
        self.assertEqual(result.action, "exclude")


if __name__ == "__main__":
    unittest.main()
