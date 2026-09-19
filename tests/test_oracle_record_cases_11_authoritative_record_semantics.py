"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    canon,
    families,
    json,
    proposal_findings,
    record,
    result_findings,
    schema_validation,
    time,
    unittest,
)


class AuthoritativeRecordSemanticsCase02(unittest.TestCase):
    def test_provenance_claims_and_authorship_lists_are_authenticated(self):
        mutations = {
            "claimed": "some-other-authority",
            "oracle_grounded": False,
            "generator_authored": ["scenario"],
            "oracle_authored": ["result"],
        }
        for field, forged in mutations.items():
            item = build(families.ENCODER_FAMILY)
            item["provenance"][field] = forged
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)


class AuthoritativeRecordSemanticsCase03(unittest.TestCase):
    def test_units_must_be_nonempty_equal_and_family_exact(self):
        item = build(families.ENCODER_FAMILY)
        item["result"]["units"] = {}
        findings = result_findings(item)
        self.assertTrue(any("result.units" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["result"]["units"]["rmse"] = "forged-unit"
        findings = result_findings(item)
        self.assertTrue(any("result.units" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["result"]["units"]["rmse"] = "forged-unit"
        item["oracle"]["units"]["rmse"] = "forged-unit"
        findings = result_findings(item)
        self.assertTrue(any("family units contract" in f for f in findings), findings)


class AuthoritativeRecordSemanticsCase04(unittest.TestCase):
    @staticmethod
    def _drop_sample_count(item):
        del item["scenario"]["sample_count"]

    @staticmethod
    def _boolean_sample_count(item):
        item["scenario"]["sample_count"] = True

    @staticmethod
    def _duplicate_encoding_pair(item):
        item["scenario"]["encoding_pair"][1] = item["scenario"]["encoding_pair"][0]

    @staticmethod
    def _duplicate_node(item):
        item["scenario"]["nodes"][1] = item["scenario"]["nodes"][0]

    @staticmethod
    def _duplicate_firing_order(item):
        order = item["result"]["measured"]["before"]["firing_order"]
        order.append(order[0])

    def _assert_finding_mentions_all(self, findings, needles):
        self.assertTrue(
            any(all(needle in finding for needle in needles) for finding in findings),
            findings,
        )

    def _assert_proposal_gate_finding(self, family, mutate, *needles):
        item = build(family)
        mutate(item)
        self._assert_finding_mentions_all(proposal_findings(item), needles)

    def _assert_result_gate_finding(self, family, mutate, *needles):
        item = build(family)
        mutate(item)
        self._assert_finding_mentions_all(result_findings(item), needles)

    def test_stdlib_schema_gate_enforces_nested_required_types_and_uniqueness(self):
        self._assert_proposal_gate_finding(
            families.ENCODER_FAMILY, self._drop_sample_count, "sample_count", "required"
        )
        self._assert_proposal_gate_finding(
            families.ENCODER_FAMILY, self._boolean_sample_count, "sample_count", "type"
        )
        self._assert_proposal_gate_finding(
            families.ENCODER_FAMILY,
            self._duplicate_encoding_pair,
            "encoding_pair",
            "unique",
        )
        self._assert_proposal_gate_finding(
            families.MESH_FAMILY, self._duplicate_node, "nodes", "unique"
        )
        self._assert_result_gate_finding(
            families.MESH_FAMILY, self._duplicate_firing_order, "firing_order", "unique"
        )


class AuthoritativeRecordSemanticsCase05(unittest.TestCase):
    def test_unique_items_validation_is_linear_and_uses_json_equality(self):
        schema = {"type": "array", "uniqueItems": True}
        self.assertEqual(
            schema_validation._validate([1, True, "1"], schema, schema, "$"),
            [],
        )
        self.assertEqual(
            schema_validation._validate([1, 1.0], schema, schema, "$"),
            ["$ must contain unique items"],
        )
        self.assertEqual(
            schema_validation._validate([{"a": 1}, {"a": 1.0}], schema, schema, "$"),
            ["$ must contain unique items"],
        )
        values = list(range(8000))
        started = time.perf_counter()
        self.assertEqual(schema_validation._validate(values, schema, schema, "$"), [])
        unique_elapsed = time.perf_counter() - started
        values[-1] = 0
        started = time.perf_counter()
        self.assertEqual(
            schema_validation._validate(values, schema, schema, "$"),
            ["$ must contain unique items"],
        )
        duplicate_elapsed = time.perf_counter() - started
        self.assertLess(unique_elapsed, 1.0, unique_elapsed)
        self.assertLess(duplicate_elapsed, 1.0, duplicate_elapsed)


class AuthoritativeRecordSemanticsCase06(unittest.TestCase):
    def test_draft_integer_semantics_accept_integral_floats_only(self):
        schema = {"type": "integer"}
        for value in (0, -4, 1.0, -12.0):
            with self.subTest(accepted=value):
                self.assertEqual(schema_validation._validate(value, schema, schema, "$"), [])
        for value in (True, False, 1.5, float("nan"), float("inf"), float("-inf")):
            with self.subTest(rejected=value):
                self.assertTrue(
                    schema_validation._validate(value, schema, schema, "$"),
                    f"{value!r} was accepted as an integer",
                )

        item = build(families.MEMORY_FAMILY)
        measured = item["result"]["measured"]
        for trial in (measured["baseline"], *measured["probes"].values()):
            trial["output_spike_counts"] = {
                key: float(value) for key, value in trial["output_spike_counts"].items()
            }
        item["result_hash"] = canon.digest(item["result"])
        item["validation"] = record.assess(item)
        # Draft schema integer semantics accept these numeric values, while
        # exact execution replay still rejects a changed result representation.
        self.assertEqual(schema_validation.validate_record_schemas(item, item["family"]), [])
        layers = record.classify(item)
        self.assertTrue(any("reference replay mismatch" in error for error in layers["envelope"]))
        self.assertEqual(layers["status"], [])


class AuthoritativeRecordSemanticsCase07(unittest.TestCase):
    def test_every_shipped_schema_uses_only_enforced_keywords(self):
        paths = [schema_validation.BASE_SCHEMA_PATH]
        paths.extend(sorted(schema_validation.FAMILY_SCHEMA_DIR.glob("*.schema.json")))
        self.assertGreaterEqual(len(paths), 6)
        for path in paths:
            with self.subTest(schema=path.name):
                with path.open(encoding="utf-8") as handle:
                    schema = json.load(handle)
                self.assertEqual(schema_validation._unsupported_keyword_errors(schema), [])


class AuthoritativeRecordSemanticsCase08(unittest.TestCase):
    def test_a_schema_keyword_the_validator_ignores_is_a_finding_not_a_pass(self):
        # `_validate` skips `allOf`, so without the keyword audit this
        # violating instance would sail through the assertion unchecked.
        schema = {"type": "object", "allOf": [{"required": ["must_have"]}]}
        self.assertEqual(schema_validation._validate({}, schema, schema, "$"), [])
        self.assertEqual(
            schema_validation._unsupported_keyword_errors(schema),
            ["schema object at # uses unenforced keywords: allOf"],
        )

