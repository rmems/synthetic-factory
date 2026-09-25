"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    accepted_reference,
    build,
    canon,
    copy,
    families,
    oracles,
    record,
    relabel_as_named_runtime,
    relabel_plasticity_stage_as_named,
    result_findings,
    unittest,
)


class CurationFailsClosedCase18(unittest.TestCase):
    def test_protocol_execution_cannot_self_attest_hil_or_designed_provenance(self):
        for item in (
            build(families.NEURON_FAMILY),
            relabel_as_named_runtime(build(families.ENCODER_FAMILY)),
        ):
            for forged in ("hil", "designed"):
                candidate = copy.deepcopy(item)
                candidate["provenance"]["kind"] = forged
                findings = record.validate_record(candidate, check_declared_status=False)
                with self.subTest(implementation=item["oracle"]["implementation"], kind=forged):
                    self.assertTrue(
                        any("does not attest physical hardware" in f for f in findings),
                        findings,
                    )


class AuthorityCannotBeSelfDeclaredCase01(unittest.TestCase):
    def test_reference_records_at_the_current_digest_are_publishable(self):
        # #171: a deterministic in-repo simulator is an authoritative oracle
        # when its measurement is reproducible, so an accepted reference record
        # is publishable and a rejected one never is.
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                item = build(family)
                self.assertEqual(item["oracle"]["implementation"], "reference")
                self.assertEqual(item["oracle"]["authority"], "reference-simulator")
                self.assertEqual(item["provenance"]["kind"], "simulated")
                self.assertEqual(item["oracle"]["module_digest"], oracles.module_digest())
                accepted = item["validation"]["status"] == "accepted"
                self.assertIs(item["validation"]["publishable"], accepted)
                reason = item["validation"]["publishable_reason"]
                if accepted:
                    self.assertEqual(reason, record.PUBLISHABLE_REASONS["reference"])
                    self.assertIn("not a runtime attestation", reason)
                else:
                    self.assertEqual(reason, "record failed validation")


class AuthorityCannotBeSelfDeclaredCase02(unittest.TestCase):
    def test_a_reference_record_with_an_unreproducible_digest_is_not_publishable(self):
        item = accepted_reference(families.ENCODER_FAMILY)
        item["oracle"]["module_digest"] = canon.digest({"different": "reference implementation"})
        publishable, reason = record.publishability(item, ())
        self.assertFalse(publishable)
        self.assertIn("cannot be reproduced here", reason)
        # Stored, such a record is refused on the digest before its own
        # validation block is even consulted.
        findings = record.validate_record(item)
        self.assertTrue(any("current reference implementation" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase03(unittest.TestCase):
    def test_a_reference_record_is_publishable_only_as_simulated_provenance(self):
        item = accepted_reference(families.NEURON_FAMILY)
        for kind in ("designed", "hil", "unknown"):
            forged = copy.deepcopy(item)
            forged["provenance"]["kind"] = kind
            with self.subTest(kind=kind):
                publishable, reason = record.publishability(forged, ())
                self.assertFalse(publishable)
                self.assertIn("'simulated'", reason)


class AuthorityCannotBeSelfDeclaredCase04(unittest.TestCase):
    def test_an_unknown_implementation_is_never_publishable(self):
        item = accepted_reference(families.ENCODER_FAMILY)
        for forged in ("hardware", ["reference"]):
            candidate = copy.deepcopy(item)
            candidate["oracle"]["implementation"] = forged
            with self.subTest(implementation=forged):
                publishable, reason = record.publishability(candidate, ())
                self.assertFalse(publishable)
                self.assertIn("unknown oracle.implementation", reason)


class AuthorityCannotBeSelfDeclaredCase05(unittest.TestCase):
    def test_a_mixed_chain_is_publishable_at_the_current_digest(self):
        item = relabel_plasticity_stage_as_named(accepted_reference(families.CREDIT_FAMILY))
        self.assertEqual(item["oracle"]["implementation"], "mixed")
        publishable, reason = record.publishability(item, ())
        self.assertTrue(publishable)
        self.assertEqual(reason, record.PUBLISHABLE_REASONS["mixed"])


class AuthorityCannotBeSelfDeclaredCase06(unittest.TestCase):
    def test_a_declared_publishability_that_disagrees_with_the_recomputed_one_is_rejected(self):
        item = accepted_reference(families.ENCODER_FAMILY)
        self.assertTrue(item["validation"]["publishable"])
        denied = copy.deepcopy(item)
        denied["validation"]["publishable"] = False
        findings = record.validate_record(denied)
        self.assertTrue(any("recomputed value is True" in f for f in findings), findings)
        # Nor may a simulator run dress its reason up as a runtime measurement.
        relabelled = copy.deepcopy(item)
        relabelled["validation"]["publishable_reason"] = "measured by axon-encoder"
        findings = record.validate_record(relabelled)
        self.assertTrue(any("publishable_reason" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase07(unittest.TestCase):
    def test_a_rejected_named_runtime_record_cannot_claim_publishability(self):
        item = next(
            relabel_as_named_runtime(build(families.MEMORY_FAMILY, index))
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["validation"]["status"] == "rejected"
        )
        self.assertEqual(item["validation"]["status"], "rejected")
        self.assertFalse(item["validation"]["publishable"])
        item["validation"]["publishable"] = True
        findings = record.validate_record(item)
        self.assertTrue(any("recomputed value" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase08(unittest.TestCase):
    def test_relabelling_a_reference_run_as_a_named_runtime_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["implementation"] = "named-runtime"
        item["oracle"]["authority"] = "measured-runtime"
        findings = record.validate_record(item)
        self.assertTrue(
            any("not every stage was run by a named runtime" in f for f in findings), findings
        )


class AuthorityCannotBeSelfDeclaredCase09(unittest.TestCase):
    def test_coordinated_oracle_identity_and_version_rewrites_are_rejected(self):
        item = build(families.ENCODER_FAMILY)
        oracle = item["oracle"]
        oracle["id"] = "forged-reference-oracle"
        oracle["version"] = "999.0.0-forged"
        oracle["stages"][0]["oracle_id"] = "different-forged-stage-id"
        oracle["stages"][0]["version"] = "888.0.0-forged"
        item["result"]["produced_by"] = oracle["id"]
        findings = result_findings(item)
        self.assertTrue(any("canonical reference adapter" in f for f in findings), findings)
        self.assertTrue(any("oracle.id" in f for f in findings), findings)
        self.assertTrue(any("oracle.version" in f for f in findings), findings)

