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


class CurationFailsClosedCase01(unittest.TestCase):
    def test_a_missing_result_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["result"] = {}
        findings = record.validate_record(item)
        self.assertTrue(any("$.result" in f and "required" in f for f in findings), findings)


class CurationFailsClosedCase02(unittest.TestCase):
    def test_an_empty_measurement_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"] = {}
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item)
        self.assertTrue(any("measured" in f for f in findings), findings)


class CurationFailsClosedCase03(unittest.TestCase):
    def test_a_misattributed_result_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["produced_by"] = "somebody-else"
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item)
        self.assertTrue(any("produced_by" in f for f in findings), findings)


class CurationFailsClosedCase04(unittest.TestCase):
    def test_an_unresolved_commit_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["commit"] = "unknown"
        findings = record.validate_record(item)
        self.assertTrue(any("commit" in f for f in findings), findings)


class CurationFailsClosedCase05(unittest.TestCase):
    def test_source_commit_requires_a_full_lowercase_object_id(self):
        for forged in ("main", "a" * 39, "a" * 41, "A" * 40, "0x" + "a" * 40):
            item = build(families.NEURON_FAMILY)
            item["oracle"]["commit"] = forged
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(commit=forged):
                self.assertTrue(any("oracle.commit" in f for f in findings), findings)
        self.assertTrue(oracles.is_source_commit("a" * 40))
        self.assertTrue(oracles.is_source_commit("b" * 64))


class CurationFailsClosedCase06(unittest.TestCase):
    def test_a_syntactically_valid_but_absent_source_commit_is_rejected(self):
        absent = "f" * 40
        self.assertTrue(oracles.is_source_commit(absent))
        self.assertIsNone(oracles.resolve_source_commit(absent))
        item = build(families.NEURON_FAMILY)
        item["oracle"]["commit"] = absent
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("does not resolve" in finding for finding in findings), findings)


class CurationFailsClosedCase07(unittest.TestCase):
    def test_generator_seed_must_reproduce_the_stored_proposal(self):
        item = build(families.ENCODER_FAMILY)
        item["generator"]["seed"] += 1
        item["oracle"]["seed"] = item["generator"]["seed"]
        item["proposal_hash"] = canon.digest(record.proposal_of(item))
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("generator.seed does not reproduce" in finding for finding in findings),
            findings,
        )


class CurationFailsClosedCase08(unittest.TestCase):
    def test_oracle_seed_must_match_the_generator_seed(self):
        # A record validated on its own (outside its original manifest) must
        # not be able to claim a different oracle.seed than the generator
        # seed that actually produced its scenario: nothing else re-derives
        # oracle.seed, so an unbound field is free provenance to forge.
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["seed"] += 1
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("oracle.seed does not match the generator seed" in finding for finding in findings),
            findings,
        )


class CurationFailsClosedCase09(unittest.TestCase):
    def test_a_custom_model_still_validates_deterministically(self):
        # build_record(..., model=...) is a supported provenance override:
        # validation must reconstruct the expected generator using the
        # retained model identity, not silently reject every custom model.
        item = build(families.ENCODER_FAMILY, model="custom-generator-x")
        self.assertEqual(item["generator"]["name"], "custom-generator-x")
        self.assertEqual(record.classify(item)["envelope"], [])


class CurationFailsClosedCase10(unittest.TestCase):
    def test_missing_module_digest_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["module_digest"] = "not-a-digest"
        findings = record.validate_record(item)
        self.assertTrue(any("module_digest" in f for f in findings), findings)


class CurationFailsClosedCase11(unittest.TestCase):
    def test_a_self_consistent_stale_reference_digest_is_rejected(self):
        item = build(families.NEURON_FAMILY)
        forged = canon.digest({"different": "reference implementation"})
        item["oracle"]["module_digest"] = forged
        item["oracle"]["stages"][0]["module_digest"] = forged
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("current reference implementation" in f for f in findings), findings)


class CurationFailsClosedCase12(unittest.TestCase):
    def test_named_runtime_records_still_bind_the_request_module_digest(self):
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        item["oracle"]["module_digest"] = canon.digest({"forged": "named-runtime digest"})
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("current reference implementation" in f for f in findings), findings)


class CurationFailsClosedCase13(unittest.TestCase):
    def test_a_missing_dirty_state_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        del item["oracle"]["dirty"]
        findings = record.validate_record(item)
        self.assertTrue(any("dirty" in f for f in findings), findings)


class CurationFailsClosedCase14(unittest.TestCase):
    def test_a_record_with_no_executed_stages_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["stages"] = []
        findings = record.validate_record(item)
        self.assertTrue(any("stages" in f for f in findings), findings)


class CurationFailsClosedCase15(unittest.TestCase):
    def test_provenance_never_claims_a_real_measurement(self):
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                self.assertEqual(build(family)["provenance"]["kind"], "simulated")


class CurationFailsClosedCase16(unittest.TestCase):
    def test_an_out_of_vocabulary_provenance_kind_is_rejected(self):
        item = build(families.NEURON_FAMILY)
        item["provenance"]["kind"] = "real"
        findings = record.validate_record(item)
        self.assertTrue(any("provenance.kind" in f for f in findings), findings)


class CurationFailsClosedCase17(unittest.TestCase):
    def test_unknown_provenance_is_not_allowed_on_a_new_record(self):
        item = build(families.NEURON_FAMILY)
        item["provenance"]["kind"] = "unknown"
        findings = record.validate_record(item)
        self.assertTrue(any("provenance.kind" in f for f in findings), findings)

