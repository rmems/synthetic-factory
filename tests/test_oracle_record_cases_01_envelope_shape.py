"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    PINNED_COMMIT,
    build,
    canon,
    families,
    mock,
    record,
    relabel_as_named_runtime,
    unittest,
)


class EnvelopeShapeCase01(unittest.TestCase):
    def test_every_family_builds_a_record_that_validates(self):
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                item = build(family)
                layers = record.classify(item)
                self.assertEqual(layers["envelope"], [])
                self.assertEqual(layers["status"], [])
                self.assertEqual(item["family"], family)
                self.assertEqual(item["schema"], record.SCHEMA_ID)


class EnvelopeShapeCase02(unittest.TestCase):
    def test_unauthenticated_top_level_siblings_are_rejected(self):
        item = build(families.MEMORY_FAMILY)
        item["ground_truth"] = {"authoritative_label": "forged"}
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("ground_truth" in f and "not allowed" in f for f in findings),
            findings,
        )
        clean = build(families.MEMORY_FAMILY)
        self.assertEqual(record.classify(clean)["envelope"], [])


class EnvelopeShapeCase03(unittest.TestCase):
    def test_unauthenticated_oracle_siblings_are_rejected(self):
        # The oracle block is execution provenance that no content hash
        # covers, so an injected sibling would be a free attestation claim.
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["external_attestation"] = "verified-by-vendor"
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("external_attestation" in f and "not allowed" in f for f in findings),
            findings,
        )


class EnvelopeShapeCase04(unittest.TestCase):
    def test_unauthenticated_oracle_stage_siblings_are_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["stages"][0]["attestation"] = "vendor-signed"
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("attestation" in f and "not allowed" in f for f in findings),
            findings,
        )


class EnvelopeShapeCase05(unittest.TestCase):
    def test_unauthenticated_measured_siblings_are_rejected_for_every_family(self):
        # result.measured is the authoritative measurement surface; an
        # injected sibling with a recomputed result_hash must not validate.
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                item = build(family)
                item["result"]["measured"]["external_attestation"] = "verified-on-hardware"
                item["result_hash"] = canon.digest(item["result"])
                findings = record.validate_record(item, check_declared_status=False)
                self.assertTrue(
                    any(
                        "external_attestation" in f and "not allowed" in f
                        for f in findings
                    ),
                    (family, findings),
                )


class EnvelopeShapeCase06(unittest.TestCase):
    def test_run_bound_validation_rejects_a_foreign_commit_without_resolving(self):
        # With the manifest's resolved commit supplied, a record stamped with
        # a different commit is rejected by string comparison; it must never
        # launch its own repository resolution, or a run full of distinct
        # forged commits could hold the bounded CLI in git for minutes.
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["commit"] = "b" * 40
        with mock.patch.object(
            record.oracles,
            "resolve_source_commit",
            side_effect=AssertionError("per-record resolution must not run"),
        ):
            layers = record.classify(
                item, check_declared_status=False, expected_commit=PINNED_COMMIT
            )
        self.assertTrue(
            any(
                "does not match the run manifest's resolved oracle commit" in f
                for f in layers["envelope"]
            ),
            layers,
        )


class EnvelopeShapeCase07(unittest.TestCase):
    def test_a_named_runtime_record_with_unresolved_dirty_state_is_unpublishable(self):
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        item["oracle"]["dirty"] = None
        publishable, reason = record.publishability(item)
        self.assertFalse(publishable)
        self.assertIn("dirty state is unresolved", reason)


class EnvelopeShapeCase08(unittest.TestCase):
    def test_unauthenticated_provenance_siblings_are_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["provenance"]["external_attestation"] = "verified-on-hardware"
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("external_attestation" in f and "not allowed" in f for f in findings),
            findings,
        )
        backstop = []
        record._provenance_findings(item, item["oracle"], backstop)
        self.assertTrue(
            any("provenance carries unauthenticated sibling keys" in f for f in backstop),
            backstop,
        )


class EnvelopeShapeCase09(unittest.TestCase):
    def test_unauthenticated_meta_siblings_are_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["meta"]["attestation"] = "vendor-signed"
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("attestation" in f and "not allowed" in f for f in findings),
            findings,
        )
        self.assertTrue(
            any(
                "meta carries unauthenticated sibling keys" in f
                for f in record._validate_generator_side(item)
            ),
        )


class EnvelopeShapeCase10(unittest.TestCase):
    def test_the_oracle_key_vocabulary_is_closed_without_the_schema_layer(self):
        # Belt and braces: the record validator itself refuses oracle and
        # stage siblings even when the JSON Schema layer is unavailable.
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["external_attestation"] = "verified-by-vendor"
        item["oracle"]["stages"][0]["attestation"] = "vendor-signed"
        findings = record._validate_oracle_side(item, require_named_runtime=False)
        self.assertTrue(
            any("oracle carries unauthenticated sibling keys" in f for f in findings),
            findings,
        )
        self.assertTrue(
            any(
                "oracle.stages[0] carries unauthenticated sibling keys" in f
                for f in findings
            ),
            findings,
        )

