"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    canon,
    families,
    oracles,
    record,
    relabel_as_named_runtime,
    unittest,
)


class AuthorityCannotBeSelfDeclaredCase10(unittest.TestCase):
    def test_named_runtime_stage_requires_its_runtime_identity_and_executable(self):
        item = build(families.ENCODER_FAMILY)
        oracle = item["oracle"]
        oracle["implementation"] = "named-runtime"
        oracle["authority"] = "measured-runtime"
        oracle["runtime_bound"] = True
        oracle["availability"]["all_bound"] = True
        oracle["availability"]["unbound"] = []
        oracle["availability"]["runtimes"][0]["bound"] = True
        stage = oracle["stages"][0]
        stage["implementation"] = "named-runtime"
        stage["runtime_commit"] = "a" * 40
        item["provenance"]["claimed"] = "measured-runtime"
        item["meta"]["tags"][-1] = "named-runtime"
        item["validation"] = record.assess(item)
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("oracle_id" in f for f in findings), findings)
        self.assertTrue(any("executable" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase11(unittest.TestCase):
    def test_named_runtime_publication_does_not_claim_external_attestation(self):
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        publishable, reason = record.publishability(item, ())
        self.assertTrue(publishable)
        self.assertIn("does not provide external attestation", reason)
        # #171 changed nothing for a bound runtime: recorded exactly as before.
        self.assertEqual(
            reason,
            "measured through the named-runtime protocol with resolved stored "
            "provenance; the protocol does not provide external attestation",
        )


class AuthorityCannotBeSelfDeclaredCase12(unittest.TestCase):
    def test_a_stage_digest_that_does_not_match_the_oracle_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["stages"][0]["module_digest"] = canon.digest({"tampered": True})
        findings = record.validate_record(item)
        self.assertTrue(any("module_digest" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase13(unittest.TestCase):
    def test_runtime_bound_must_agree_with_the_availability_report(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["runtime_bound"] = True
        findings = record.validate_record(item)
        self.assertTrue(any("runtime_bound" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase14(unittest.TestCase):
    def test_each_stage_implementation_must_match_its_runtime_binding(self):
        item = build(families.CREDIT_FAMILY)
        availability = item["oracle"]["availability"]
        availability["runtimes"][0]["bound"] = True
        availability["unbound"] = ["plasticity-lab"]
        findings = record.validate_record(item)
        self.assertTrue(any("corresponding runtime binding" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase15(unittest.TestCase):
    def test_require_named_runtime_rejects_a_reference_record(self):
        item = build(families.ENCODER_FAMILY)
        self.assertEqual(record.validate_record(item), [])
        findings = record.validate_record(item, require_named_runtime=True)
        self.assertTrue(any("named-runtime" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclaredCase16(unittest.TestCase):
    def test_the_availability_report_names_the_missing_runtime(self):
        item = build(families.ENCODER_FAMILY)
        availability = item["oracle"]["availability"]
        self.assertEqual(availability["unbound"], ["axon-encoder"])
        self.assertFalse(availability["all_bound"])
        probe = oracles.probe_runtime("axon-encoder", environ={})
        self.assertEqual(probe["binding_env"], "SF_ORACLE_AXON_ENCODER_CMD")
        self.assertIn("axon-encoder", probe["note"])


class AuthorityCannotBeSelfDeclaredCase17(unittest.TestCase):
    def test_the_availability_report_carries_no_host_details(self):
        # This block is compared byte for byte by the golden fixture, so it must
        # describe the oracle binding and nothing about the machine.
        report = oracles.availability_report(("axon-encoder",), environ={})
        self.assertEqual(sorted(report), ["all_bound", "protocol", "runtimes", "unbound"])


class DeclaredStatusCase01(unittest.TestCase):
    def rejected_memory_record(self):
        for index in range(24):
            item = build(families.MEMORY_FAMILY, index)
            if item["validation"]["status"] == "rejected":
                return item
        self.skipTest("no rejected temporal-memory record in the first 24 proposals")
        return None
    def test_a_failing_record_relabelled_as_accepted_is_rejected(self):
        item = self.rejected_memory_record()
        item["validation"]["status"] = "accepted"
        item["validation"]["reasons"] = []
        findings = record.validate_record(item)
        self.assertTrue(any("recomputed status" in f for f in findings), findings)


class DeclaredStatusCase02(unittest.TestCase):
    def rejected_memory_record(self):
        for index in range(24):
            item = build(families.MEMORY_FAMILY, index)
            if item["validation"]["status"] == "rejected":
                return item
        self.skipTest("no rejected temporal-memory record in the first 24 proposals")
        return None
    def test_a_rewritten_rejection_reason_is_rejected(self):
        item = self.rejected_memory_record()
        item["validation"]["reasons"] = ["nothing to see here"]
        findings = record.validate_record(item)
        self.assertTrue(any("do not match the recomputed findings" in f for f in findings))


class DeclaredStatusCase03(unittest.TestCase):
    def test_a_rejected_record_with_no_reason_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["validation"]["status"] = "rejected"
        item["validation"]["reasons"] = []
        findings = record.validate_record(item)
        self.assertTrue(any("recomputed status" in f for f in findings), findings)


class DeclaredStatusCase04(unittest.TestCase):
    def test_an_unknown_status_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["validation"]["status"] = "probably fine"
        findings = record.validate_record(item)
        self.assertTrue(any("validation.status" in f for f in findings), findings)

