"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    REPO,
    build,
    canon,
    families,
    generators,
    json,
    record,
    unittest,
)


class EnvelopeShapeCase11(unittest.TestCase):
    def test_the_envelope_carries_every_declared_key(self):
        item = build(families.ENCODER_FAMILY)
        for key in record.ENVELOPE_KEYS:
            self.assertIn(key, item)
        for key in record.ORACLE_KEYS:
            self.assertIn(key, item["oracle"])


class EnvelopeShapeCase12(unittest.TestCase):
    def test_the_schema_file_and_the_code_agree_on_the_required_keys(self):
        schema = json.loads((REPO / "schemas" / "oracle-grounded-v1.schema.json").read_text())
        self.assertEqual(sorted(schema["required"]), sorted(record.ENVELOPE_KEYS))
        oracle_required = schema["$defs"]["oracle"]["required"]
        self.assertEqual(sorted(oracle_required), sorted(record.ORACLE_KEYS))
        self.assertEqual(schema["properties"]["schema"]["const"], record.SCHEMA_ID)
        self.assertEqual(
            sorted(schema["properties"]["family"]["enum"]), sorted(families.FAMILY_NAMES)
        )


class EnvelopeShapeCase13(unittest.TestCase):
    def test_every_family_has_a_published_schema_file(self):
        for family in families.FAMILY_NAMES:
            path = REPO / "schemas" / "oracle-grounded" / f"{family}.schema.json"
            with self.subTest(family=family):
                self.assertTrue(path.is_file(), f"missing schema: {path}")
                json.loads(path.read_text())


class EnvelopeShapeCase14(unittest.TestCase):
    def test_an_unknown_family_is_refused(self):
        with self.assertRaises(KeyError):
            families.spec_for("not-a-family")
        with self.assertRaises(KeyError):
            build("not-a-family")


class GeneratorNeverMeasuresCase01(unittest.TestCase):
    def test_the_generator_block_declares_itself_non_authoritative(self):
        item = build(families.MESH_FAMILY)
        self.assertIs(item["generator"]["authoritative"], False)


class GeneratorNeverMeasuresCase02(unittest.TestCase):
    def test_a_generator_claiming_authority_is_rejected(self):
        item = build(families.MESH_FAMILY)
        item["generator"]["authoritative"] = True
        self.assertTrue(any("authoritative" in finding for finding in record.validate_record(item)))


class GeneratorNeverMeasuresCase03(unittest.TestCase):
    def test_a_measurement_key_in_a_generator_section_is_rejected(self):
        for section in ("scenario", "candidate_prediction"):
            item = build(families.NEURON_FAMILY)
            item[section]["measured"] = {"spike_count": 99}
            with self.subTest(section=section):
                findings = record.validate_record(item)
                self.assertTrue(any("oracle-reserved keys" in f for f in findings), findings)


class GeneratorNeverMeasuresCase04(unittest.TestCase):
    def test_a_nested_measurement_key_is_found(self):
        item = build(families.NEURON_FAMILY)
        item["scenario"]["stimulus"]["parameters"]["ground_truth"] = 1
        findings = record.validate_record(item)
        self.assertTrue(any("oracle-reserved keys" in f for f in findings), findings)


class GeneratorNeverMeasuresCase05(unittest.TestCase):
    def test_reserved_key_scanning_is_bounded_against_adversarial_payloads(self):
        # A schema-open scenario section can legally carry large extra arrays,
        # so the reserved-key scan must not turn one reserved key per element
        # into a multi-megabyte list of paths before the record is rejected.
        payload = {"scenario": {"junk": [{"measured": index} for index in range(10_000)]}}
        hits = record._reserved_key_hits(payload)
        self.assertEqual(len(hits), record.MAX_RESERVED_KEY_HITS)

        item = build(families.MESH_FAMILY)
        item["scenario"]["junk"] = [{"measured": index} for index in range(10_000)]
        findings = record.validate_record(item, check_declared_status=False)
        reserved = [f for f in findings if "oracle-reserved keys" in f]
        self.assertTrue(reserved, findings)
        self.assertLess(len(reserved[0]), 4_000, len(reserved[0]))
        self.assertIn("scan capped", reserved[0])


class GeneratorNeverMeasuresCase06(unittest.TestCase):
    def test_build_refuses_a_generator_that_authors_a_measurement(self):
        original = generators.propose_mesh_scenario

        def poisoned(rng, *args, **kwargs):
            scenario = original(rng, *args, **kwargs)
            scenario["measured"] = {"propagation_delay_ms": 0.0}
            return scenario

        generators.propose_mesh_scenario = poisoned
        try:
            with self.assertRaises(record.GenerationError):
                build(families.MESH_FAMILY)
        finally:
            generators.propose_mesh_scenario = original


class GeneratorNeverMeasuresCase07(unittest.TestCase):
    def test_a_candidate_prediction_cannot_pose_as_ground_truth(self):
        item = build(families.ENCODER_FAMILY)
        item["candidate_prediction"]["kind"] = "ground_truth"
        findings = record.validate_record(item)
        self.assertTrue(any("non_authoritative_guess" in f for f in findings), findings)


class GeneratorNeverMeasuresCase08(unittest.TestCase):
    def test_the_candidate_prediction_is_scored_but_not_believed(self):
        item = build(families.ENCODER_FAMILY)
        self.assertIn(item["validation"]["candidate_prediction_correct"], (True, False, None))
        self.assertNotIn("candidate_prediction", item["result"]["measured"])


class HashesCoverWhatTheyClaimCase01(unittest.TestCase):
    def test_the_proposal_hash_covers_exactly_the_generator_sections(self):
        item = build(families.ENCODER_FAMILY)
        self.assertEqual(item["proposal_hash"], canon.digest(record.proposal_of(item)))
        self.assertEqual(sorted(record.proposal_of(item)), sorted(record.GENERATOR_SECTIONS))


class HashesCoverWhatTheyClaimCase02(unittest.TestCase):
    def test_editing_a_scenario_after_the_fact_is_detected(self):
        item = build(families.ENCODER_FAMILY)
        item["scenario"]["sample_count"] += 1
        findings = record.validate_record(item)
        self.assertTrue(any("proposal_hash" in f for f in findings), findings)


class HashesCoverWhatTheyClaimCase03(unittest.TestCase):
    def test_editing_the_oracle_block_does_not_disturb_the_proposal_hash(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["description"] = "annotated later"
        self.assertNotIn(
            "proposal_hash",
            " ".join(record.classify(item)["envelope"]),
        )


class HashesCoverWhatTheyClaimCase04(unittest.TestCase):
    def test_the_result_hash_covers_the_result(self):
        item = build(families.MESH_FAMILY)
        self.assertEqual(item["result_hash"], canon.digest(item["result"]))
        item["result"]["measured"]["before"]["sink_reached"] = not item["result"]["measured"][
            "before"
        ]["sink_reached"]
        findings = record.validate_record(item)
        self.assertTrue(any("result_hash" in f for f in findings), findings)


class HashesCoverWhatTheyClaimCase05(unittest.TestCase):
    def test_hashes_survive_a_json_round_trip(self):
        item = build(families.CREDIT_FAMILY)
        reloaded = json.loads(canon.dumps_record(item))
        self.assertEqual(reloaded["proposal_hash"], canon.digest(record.proposal_of(reloaded)))
        self.assertEqual(reloaded["result_hash"], canon.digest(reloaded["result"]))
        self.assertEqual(record.validate_record(reloaded), [])

