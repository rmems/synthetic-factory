"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    Path,
    build,
    families,
    json,
    mock,
    proposal_findings,
    record,
    result_findings,
    schema_validation,
    sim,
    tempfile,
    unittest,
)


class AuthoritativeRecordSemanticsCase09(unittest.TestCase):
    def test_unenforced_keywords_are_reported_from_nested_schema_positions(self):
        schema = {
            "type": "object",
            "properties": {
                "a": {"oneOf": [{"type": "string"}]},
                "b": {"type": "array", "items": {"maxLength": 3}},
            },
            "$defs": {"c": {"anyOf": [{"if": {}, "then": {}}]}},
        }
        errors = schema_validation._unsupported_keyword_errors(schema)
        self.assertEqual(
            errors,
            [
                "schema object at #/$defs/c/anyOf/0 uses unenforced keywords: if, then",
                "schema object at #/properties/a uses unenforced keywords: oneOf",
                "schema object at #/properties/b/items uses unenforced keywords: maxLength",
            ],
        )


class AuthoritativeRecordSemanticsCase10(unittest.TestCase):
    def test_validate_record_schemas_reports_unenforced_family_schema_keywords(self):
        item = build(families.ENCODER_FAMILY)
        family_path = (
            schema_validation.FAMILY_SCHEMA_DIR / f"{families.ENCODER_FAMILY}.schema.json"
        )
        doctored = json.loads(family_path.read_text(encoding="utf-8"))
        doctored["allOf"] = [{"required": ["nonexistent_key"]}]
        self.assertEqual(
            schema_validation.validate_record_schemas(item, families.ENCODER_FAMILY), []
        )
        with tempfile.TemporaryDirectory(prefix="oracle-doctored-schema-") as temp:
            out = Path(temp) / f"{families.ENCODER_FAMILY}.schema.json"
            out.write_text(json.dumps(doctored), encoding="utf-8")
            with mock.patch.object(schema_validation, "FAMILY_SCHEMA_DIR", Path(temp)):
                findings = schema_validation.validate_record_schemas(
                    item, families.ENCODER_FAMILY
                )
        self.assertTrue(
            any("unenforced keywords: allOf" in finding for finding in findings),
            findings,
        )


class AuthoritativeRecordSemanticsCase11(unittest.TestCase):
    def test_redundant_record_identity_labels_are_authenticated(self):
        item = build(families.ENCODER_FAMILY)
        item["generator"]["label"] = "another-family#99"
        findings = proposal_findings(item)
        self.assertTrue(any("generator.label" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["meta"]["round"] += 1
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("meta.round" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["meta"]["tags"][-1] = "named-runtime"
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("meta.tags" in f for f in findings), findings)


class AuthoritativeRecordSemanticsCase12(unittest.TestCase):
    def test_every_encoder_identity_and_summary_is_recomputed(self):
        item = build(families.ENCODER_FAMILY)
        item["result"]["measured"]["encoding_a"]["encoding"] = item["scenario"]["encoding_pair"][1]
        findings = result_findings(item)
        self.assertTrue(any("encoding_a.encoding" in f for f in findings), findings)

        scalar_fields = (
            "rmse",
            "mean_abs_error",
            "max_abs_error",
            "pearson_r",
            "information_retention",
            "mean_rate_hz",
            "energy_pJ",
            "retention_per_spike",
        )
        for field in scalar_fields:
            item = build(families.ENCODER_FAMILY)
            state = item["result"]["measured"]["encoding_a"]
            state[field] = 0.123456 if state[field] is None else state[field] + 0.123456
            findings = result_findings(item)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        for field in ("retention_margin", "energy_margin_pJ"):
            item = build(families.ENCODER_FAMILY)
            item["result"]["measured"][field] += 0.25
            findings = result_findings(item)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        item = build(families.ENCODER_FAMILY)
        state = item["result"]["measured"]["encoding_a"]
        state["representation_excerpt_truncated"] = not state["representation_excerpt_truncated"]
        findings = result_findings(item)
        self.assertTrue(any("representation_excerpt_truncated" in f for f in findings), findings)


class AuthoritativeRecordSemanticsCase13(unittest.TestCase):
    def test_every_neuron_spike_summary_is_recomputed(self):
        fields = (
            "spike_count",
            "first_spike_ms",
            "last_spike_ms",
            "mean_rate_hz",
            "mean_isi_ms",
            "cv_isi",
            "adaptation_index",
            "duration_ms",
            "v_trace_stride_ms",
        )
        for field in fields:
            item = build(families.NEURON_FAMILY)
            state = item["result"]["measured"]["before"]
            state[field] = 0.125 if state[field] is None else state[field] + 1
            findings = result_findings(item)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["before"]["v_trace"].pop()
        findings = result_findings(item)
        self.assertTrue(any("v_trace length" in f for f in findings), findings)


class AuthoritativeRecordSemanticsCase14(unittest.TestCase):
    def test_neuron_spikes_cannot_be_shifted_outside_the_run(self):
        item = build(families.NEURON_FAMILY)
        duration = item["result"]["measured"]["before"]["duration_ms"]
        for side in ("before", "after"):
            state = item["result"]["measured"][side]
            state["spike_times_ms"] = [
                time_ms + duration * 4 for time_ms in state["spike_times_ms"]
            ]
            if state["spike_times_ms"]:
                state["first_spike_ms"] = state["spike_times_ms"][0]
                state["last_spike_ms"] = state["spike_times_ms"][-1]
        item["result"]["measured"]["delta"] = sim.compare_neuron_states(
            item["result"]["measured"]["before"],
            item["result"]["measured"]["after"],
        )
        findings = result_findings(item)
        self.assertTrue(any("outside the simulated duration" in f for f in findings), findings)

