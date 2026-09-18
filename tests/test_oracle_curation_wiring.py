#!/usr/bin/env python3
"""End-to-end wiring for oracle-grounded records: kind, routes, registry, curation.

Generation and oracle validation already work; this module pins the
downstream integration that carries generated records to training-ready
curated data: payload-first classification, the validate_run shape route,
the sealed procedural registry row, and the preserving identity lane.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import validate_run  # noqa: E402
from oracle_grounded import canon as oracle_canon  # noqa: E402
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
        digest = oracle_policy.catalog_digest(REPO / "pipelines/oracle_grounded")
        self.assertEqual(oracle_policy.POLICY["catalog_sha256"], digest)

    def test_the_package_pin_is_framed_against_boundary_redistribution(self):
        """A byte moved across a module boundary must change the catalog pin.

        Length framing is what stops an attacker from shifting bytes between
        adjacent files while preserving the concatenated digest (CWE-354).
        """
        left = ("a.py", b"x = 1\n")
        right = ("b.py", b"y = 2\n")
        self.assertNotEqual(
            oracle_policy.framed_digest([left, right]),
            oracle_policy.framed_digest([("a.py", b"x = 1\ny = 2\n"), ("b.py", b"")]),
        )

    def test_programs_sha256_pins_the_pipeline_entry_points(self):
        digest = oracle_policy.programs_digest(
            REPO / "pipelines", ("oracle_generate.py", "oracle_validate.py")
        )
        self.assertEqual(oracle_policy.POLICY["programs_sha256"], digest)

    def test_admission_recomputes_the_sealed_digests(self):
        """Admission rehashes the installed bytes, not just the registry strings.

        Repeating a digest in the registry row proves nothing about the files
        on disk, so ``row_findings`` recomputes both domains and refuses a
        package that differs from the reviewed catalog.
        """
        from oracle_grounded import admission

        row = identity.default_registry().by_path_id["oracle-grounded"]
        self.assertEqual(admission.row_findings(row), [])

        with mock.patch.object(
            oracle_policy, "catalog_digest", return_value="0" * 64
        ):
            findings = admission.row_findings(row)
        self.assertEqual([code for code, _ in findings], ["ORACLE_ROUTE_UNAUTHORIZED"])
        self.assertIn("catalog digest", findings[0][1])

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
        # A genuine family-invariant failure (envelope still valid) is honest
        # evidence: retained for context, ineligible as a training candidate.
        filtered = _build()
        filtered["result"]["measured"]["encoding_b"] = dict(
            filtered["result"]["measured"]["encoding_a"]
        )
        filtered["result_hash"] = oracle_canon.digest(filtered["result"])
        filtered["validation"] = oracle_record.assess(filtered)
        self.assertEqual(filtered["validation"]["status"], "rejected")
        self.assertEqual(
            filtered["validation"]["checks"],
            {"envelope": True, "family_invariants": False},
        )
        result = self._curate(filtered)
        self.assertEqual(result.action, "retained")
        authority = result.mapping.get("procedural_authority", {})
        self.assertFalse(authority.get("eligible_training_candidate"), authority)
        self.assertTrue(authority.get("ineligibility_reasons"), authority)

    def test_tampered_envelope_is_excluded_not_trusted(self):
        # A record whose measured result was edited while keeping its stored
        # accepted verdict must be refused, not admitted on the stale stamp.
        record = _build()
        record["result"]["measured"]["injected"] = 1.0
        self.assertEqual(record["validation"]["status"], "accepted")
        result = self._curate(record)
        self.assertEqual(result.action, "exclude")
        self.assertIn("identity.oracle_invalid", result.mapping.get("reason_codes", []))

    def test_forged_generator_is_excluded(self):
        record = _build()
        record["generator"]["name"] = "unreviewed-hosted-model"
        record["validation"] = oracle_record.assess(record)
        self.assertEqual(record["validation"]["status"], "rejected")
        result = self._curate(record)
        self.assertEqual(result.action, "exclude")
        self.assertIn("ORACLE_GENERATOR_MISMATCH", str(result.mapping.get("details")))

    def test_contradictory_payload_factory_is_excluded(self):
        record = _build()
        record["meta"] = {"factory": "some-other-factory"}
        record["validation"] = oracle_record.assess(record)
        result = self._curate(record)
        self.assertEqual(result.action, "exclude")
        self.assertIn("ORACLE_FAMILY_MISMATCH", str(result.mapping.get("details")))

    def test_malformed_validation_block_excluded(self):
        record = _build()
        del record["validation"]
        result = self._curate(record)
        self.assertEqual(result.action, "exclude")


if __name__ == "__main__":
    unittest.main()
