"""Malformed stage values remain bounded validation findings."""

from test_oracle_grounded_record import build, families, record, unittest


class MalformedStageTypes(unittest.TestCase):
    def test_unhashable_stage_implementation_is_a_finding(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["stages"][0]["implementation"] = []
        findings = record._validate_stage_consistency(
            item["oracle"], families.ENCODER_FAMILY
        )
        self.assertTrue(
            any("implementation must be a string" in finding for finding in findings)
        )

    def test_unhashable_requested_runtime_is_a_finding(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["requested_runtime"][0] = []
        findings = record.validate_record(item)
        self.assertTrue(any("requested_runtime" in finding for finding in findings))

    def test_zero_duration_encoder_is_a_finding_not_an_exception(self):
        item = build(families.ENCODER_FAMILY)
        item["scenario"]["sample_count"] = 0
        findings = families._encoder_checks(item)
        self.assertTrue(any("sample_count" in finding for finding in findings))

    def test_encoder_signal_length_mismatch_is_a_finding_not_an_exception(self):
        item = build(families.ENCODER_FAMILY)
        item["scenario"]["signal"].pop()
        findings = families._encoder_checks(item)
        self.assertTrue(any("signal length" in finding for finding in findings))
