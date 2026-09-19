"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    double_env,
    families,
    mock,
    oracles,
    record,
    unittest,
)


class ExternalOracleProtocolCase09(unittest.TestCase):
    def test_bound_record_declares_runtime(self):
        item = build(families.ENCODER_FAMILY, environ=double_env("ok"))
        self.assertEqual(item["oracle"]["implementation"], "named-runtime")
        self.assertEqual(item["oracle"]["id"], "axon-encoder")
        self.assertTrue(item["oracle"]["runtime_bound"])
        self.assertEqual(item["oracle"]["availability"]["unbound"], [])
        self.assertEqual(item["result"]["produced_by"], "axon-encoder")
        # Only a bound runtime can clear the publication bar at all; this
        # particular record still cannot, because the double answers in a shape
        # the family does not recognise.
        self.assertTrue(record.publishability(item, ())[0])
        self.assertEqual(item["validation"]["status"], "rejected")
        self.assertFalse(item["validation"]["publishable"])


class ExternalOracleProtocolCase10(unittest.TestCase):
    def test_a_named_runtime_stage_requires_a_resolved_hex_commit(self):
        item = build(families.ENCODER_FAMILY, environ=double_env("ok"))
        item["oracle"]["stages"][0]["runtime_commit"] = "unknown"
        findings = record.validate_record(item)
        self.assertTrue(any("runtime_commit" in f for f in findings), findings)


class ExternalOracleProtocolCase11(unittest.TestCase):
    def test_a_runtime_answering_in_the_wrong_shape_is_rejected_not_crashed(self):
        item = build(families.ENCODER_FAMILY, environ=double_env("ok"))
        self.assertEqual(item["validation"]["status"], "rejected")
        self.assertTrue(
            any("family schema" in r for r in item["validation"]["reasons"]),
            item["validation"]["reasons"],
        )
        self.assertIsNone(item["validation"]["candidate_prediction_correct"])


class ExternalOracleProtocolCase12(unittest.TestCase):
    def test_a_half_bound_chain_is_labelled_mixed(self):
        adapter = families.spec_for(families.CREDIT_FAMILY).oracle(
            double_env("ok", runtimes=("limbic-critic",))
        )
        self.assertEqual(adapter.implementation, "mixed")
        self.assertEqual(adapter.authority, "mixed-reference-and-runtime")
        self.assertEqual(adapter.oracle_id, "limbic-critic+plasticity-ref")


class ExternalOracleProtocolCase13(unittest.TestCase):
    def test_a_chain_stage_that_cannot_consume_its_input_fails_closed(self):
        # The double answers stage one in a shape the plasticity stage cannot
        # use. That must surface as an OracleError, not a traceback.
        environ = double_env("ok", runtimes=("limbic-critic",))
        with self.assertRaises(oracles.OracleError):
            build(families.CREDIT_FAMILY, environ=environ)


class ExternalOracleProtocolCase14(unittest.TestCase):
    def test_a_failing_bound_oracle_drops_the_record(self):
        environ = double_env("fail")
        with self.assertRaises(oracles.OracleError):
            build(families.ENCODER_FAMILY, environ=environ)


class ExternalOracleProtocolCase15(unittest.TestCase):
    def test_the_environment_key_is_derived_mechanically(self):
        self.assertEqual(oracles.env_key("axon-encoder"), "SF_ORACLE_AXON_ENCODER_CMD")
        self.assertEqual(oracles.env_key("plasticity-lab"), "SF_ORACLE_PLASTICITY_LAB_CMD")


class ExternalOracleProtocolCase16(unittest.TestCase):
    def test_a_runtime_on_path_without_a_binding_is_not_claimed(self):
        with mock.patch.object(oracles.shutil, "which", return_value="/runtime/python3"):
            probe = oracles.probe_runtime("python3", environ={})
        self.assertTrue(probe["on_path"])
        self.assertFalse(probe["bound"])
        self.assertIn("no sf-oracle/1 binding", probe["note"])
