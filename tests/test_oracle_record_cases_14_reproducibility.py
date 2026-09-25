"""Focused cases split from test_oracle_grounded_record.py."""

from test_oracle_grounded_record import (
    build,
    canon,
    double_env,
    families,
    oracles,
    record,
    unittest,
)


def _bind_encoder_double(mode="ok"):
    return oracles.bind(
        runtime="axon-encoder",
        identity=oracles.OracleIdentity(
            oracle_id="encoder-ref",
            oracle_type="spike-encoder",
            description="reference",
        ),
        reference_fn=lambda request: ({"unused": True}, {}),
        environ=double_env(mode),
    )


class ReproducibilityCase01(unittest.TestCase):
    def test_every_family_reproduces_from_its_stored_scenario(self):
        for family in families.FAMILY_NAMES:
            for index in range(3):
                item = build(family, index)
                with self.subTest(family=family, index=index):
                    status, detail = record.reproduce(item, environ={})
                    self.assertEqual(status, "reproduced", detail)
                    self.assertEqual(detail, item["result_hash"])


class ReproducibilityCase02(unittest.TestCase):
    def test_the_same_seed_produces_the_same_record(self):
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                first = canon.dumps_record(build(family, 2))
                second = canon.dumps_record(build(family, 2))
                self.assertEqual(first, second)


class ReproducibilityCase03(unittest.TestCase):
    def test_a_different_index_produces_a_different_record(self):
        left = build(families.NEURON_FAMILY, 0)
        right = build(families.NEURON_FAMILY, 1)
        self.assertNotEqual(left["proposal_hash"], right["proposal_hash"])


class ReproducibilityCase04(unittest.TestCase):
    def test_a_tampered_measurement_does_not_reproduce(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["after"]["spike_count"] += 1
        item["result_hash"] = canon.digest(item["result"])
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "mismatch", detail)


class ReproducibilityCase05(unittest.TestCase):
    def test_reproduction_authenticates_reference_code_before_replaying(self):
        item = build(families.NEURON_FAMILY)
        forged = canon.digest({"forged": "implementation"})
        item["oracle"]["module_digest"] = forged
        item["oracle"]["stages"][0]["module_digest"] = forged
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "mismatch", detail)
        self.assertIn("module digest", detail)


class ReproducibilityCase06(unittest.TestCase):
    def test_reproduction_rejects_an_unresolved_source_commit_before_replaying(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["commit"] = "main"
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "invalid", detail)
        self.assertIn("source commit", detail)


class ReproducibilityCase07(unittest.TestCase):
    def test_reproduce_reports_unavailable_rather_than_guessing(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["implementation"] = "named-runtime"
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "unavailable")
        self.assertIn("named-runtime", detail)


class ReproducibilityCase08(unittest.TestCase):
    def test_malformed_stored_data_is_bounded_as_invalid(self):
        malformed = {"family": families.ENCODER_FAMILY, "scenario": []}
        status, detail = record.reproduce(malformed, environ={})
        self.assertEqual(status, "invalid")
        self.assertIn("cannot rebuild", detail)


class ExternalOracleProtocolCase01(unittest.TestCase):
    def test_an_unbound_runtime_falls_back_to_the_reference_adapter(self):
        reference = oracles.bind(
            runtime="axon-encoder",
            identity=oracles.OracleIdentity(
                oracle_id="encoder-ref",
                oracle_type="spike-encoder",
                description="reference",
            ),
            reference_fn=lambda request: ({"ok": True}, {}),
            environ={},
        )
        self.assertIsInstance(reference, oracles.ReferenceOracle)
        self.assertEqual(reference.implementation, "reference")


class ExternalOracleProtocolCase02(unittest.TestCase):
    def test_a_bound_runtime_is_used_and_attributed(self):
        adapter = _bind_encoder_double("ok")
        self.assertIsInstance(adapter, oracles.ExternalCommandOracle)
        self.assertEqual(adapter.implementation, "named-runtime")
        self.assertEqual(adapter.authority, "measured-runtime")
        run = adapter.run("spike-encoder-equivalence-pairs", {"configuration": {}, "data": {}})
        self.assertTrue(run.measured["protocol_double"])
        stage = run.stages[0]
        self.assertEqual(stage["implementation"], "named-runtime")
        self.assertEqual(stage["version"], "0.0.0-double")
        self.assertTrue(stage["runtime_commit"])


class ExternalOracleProtocolCase03(unittest.TestCase):
    def test_the_request_reaches_the_runtime_in_protocol_form(self):
        run = _bind_encoder_double("ok").run(
            "a-family", {"configuration": {"x": 1}, "data": {"y": 2}}
        )
        self.assertEqual(run.measured["echoed_family"], "a-family")
        self.assertEqual(run.measured["echoed_request_keys"], ["configuration", "data"])

