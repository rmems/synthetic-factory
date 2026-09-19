"""Native measurement admission checks reject internally inconsistent evidence."""
import copy
import importlib
import unittest
from pathlib import Path

from pipelines.oracle_grounded import schema_validation

ROOT = Path(__file__).resolve().parents[1]


def fixture(profile="axon-stream-v1"):
    encoder = profile == "axon-stream-v1"
    name, version, revision = (
        ("axon-encoder", "0.4.0", "102946f40dd55287a89aa363cd2d080a9d6195d8")
        if encoder else
        ("neuromod", "0.6.0", "184c80cbdad84c83042987e1b3ec6fed69578a87")
    )
    identity = dict(crate_name=name, crate_version=version, source_revision=revision,
                    lock_sha256="a" * 64, adapter_source_sha256="b" * 64,
                    adapter_revision="c" * 40, executable_sha256="d" * 64)
    measured = dict(profile=profile, identity=identity)
    if encoder:
        state = dict(spikes=[], reconstruction=[0.0, 0.0], spike_count=0, rmse=0.0,
                     spike_preview=[], spike_preview_truncated=False)
        measured.update(rate=copy.deepcopy(state), delta=state, winner="tie")
        params = dict(sample_ms=1.0, rate_hz=100.0, delta_threshold=0.1)
    else:
        state = dict(spikes=[], v_trace=[0.0, 0.0], spike_count=0)
        measured.update(before=copy.deepcopy(state), after=state, spike_count_delta=0)
        params = dict(dt_ms=1.0, threshold=1.0, decay=0.9, input_scale=1.0)
    return dict(
        family="spike-encoder-equivalence-pairs" if encoder else "neuron-dynamics-counterfactuals",
        scenario=dict(profile=profile, parameters=params, signal=[0.0, 0.0]),
        intervention=None if encoder else dict(parameter="threshold", factor=2.0),
        candidate_prediction=None, result=dict(measured=measured),
        oracle=dict(implementation="named-runtime", configuration=dict(profile=profile),
                    stages=[dict(requested_runtime=name, version=version, runtime_commit=revision)]),
    )


class NativeChecksTests(unittest.TestCase):
    def checks(self, record):
        spec = importlib.util.find_spec("pipelines.oracle_grounded.native_checks")
        self.assertIsNotNone(spec, "native admission checks are not implemented")
        if spec.name != "pipelines.oracle_grounded.native_checks":
            raise AssertionError("native checks resolved outside the allowlist")
        module = importlib.import_module("pipelines.oracle_grounded.native_checks")
        return module.checks(record)

    def test_silent_profiles_are_consistent(self):
        for profile in ("axon-stream-v1", "neuromod-lif-v1"):
            with self.subTest(profile=profile):
                self.assertEqual(self.checks(fixture(profile)), [])

    def test_rejects_changed_measurements(self):
        for key, value in (("spike_count", 1), ("rmse", 0.2),
                           ("reconstruction", [0.0]),
                           ("spikes", [dict(channel=7, t_ms=0.0, polarity=1)])):
            record = fixture()
            record["result"]["measured"]["rate"][key] = value
            with self.subTest(key=key):
                self.assertTrue(self.checks(record))

    def test_rejects_false_winner_and_neuron_count_delta(self):
        record = fixture()
        record["result"]["measured"]["winner"] = "rate"
        self.assertTrue(self.checks(record))
        record = fixture("neuromod-lif-v1")
        record["result"]["measured"]["spike_count_delta"] = 3
        self.assertTrue(self.checks(record))

    def test_rejects_wrong_runtime_identity(self):
        for key in ("crate_name", "crate_version", "source_revision"):
            record = fixture()
            record["result"]["measured"]["identity"][key] = "forged"
            with self.subTest(key=key):
                self.assertTrue(self.checks(record))
        record = fixture()
        record["oracle"]["stages"][0]["version"] = "9.0.0"
        self.assertTrue(self.checks(record))

    def test_rejects_reference_claim_and_wrong_family(self):
        record = fixture()
        record["oracle"]["implementation"] = "reference"
        self.assertTrue(self.checks(record))
        record = fixture()
        record["family"] = "neuron-dynamics-counterfactuals"
        self.assertTrue(self.checks(record))

    def test_schemas_reject_unknown_keys_and_nonfinite(self):
        for profile in ("axon-stream-v1", "neuromod-lif-v1"):
            path = ROOT / "schemas" / "oracle-grounded" / f"{profile}.schema.json"
            self.assertTrue(path.exists(), "native profile schema missing")
            record = fixture(profile)
            self.assertEqual(schema_validation._document_findings(record, path), [])
            record["scenario"]["parameters"]["undeclared"] = 1
            self.assertTrue(schema_validation._document_findings(record, path))
            record = fixture(profile)
            record["scenario"]["signal"][0] = float("nan")
            self.assertTrue(schema_validation._document_findings(record, path))

    def test_schema_rejects_unknown_identity_profile_and_wrong_family(self):
        for profile in ("axon-stream-v1", "neuromod-lif-v1"):
            path = ROOT / "schemas" / "oracle-grounded" / f"{profile}.schema.json"
            mutations = (
                lambda r: r["scenario"].update(profile="unknown-profile"),
                lambda r: r.update(family="wrong-family"),
                lambda r: r["result"]["measured"]["identity"].update(executable="run-me"),
                lambda r: r["scenario"].update(signal=[]),
                lambda r: r["scenario"].update(signal=[0.0] * 4097),
            )
            for mutate in mutations:
                record = fixture(profile)
                mutate(record)
                self.assertTrue(schema_validation._document_findings(record, path))

    def test_neuron_final_tick_is_in_window_and_ticks_are_discrete(self):
        record = fixture("neuromod-lif-v1")
        state = record["result"]["measured"]["before"]
        state.update(spikes=[2.0], spike_count=1)
        record["result"]["measured"]["spike_count_delta"] = -1
        self.assertEqual(self.checks(record), [])
        state["spikes"] = [0.5]
        self.assertTrue(self.checks(record))

    def test_reconstruction_is_derived_from_full_events(self):
        record = fixture()
        record["scenario"]["signal"] = [1.0, 0.0]
        rate = record["result"]["measured"]["rate"]
        rate.update(reconstruction=[1.0, 0.0], rmse=0.0)
        record["result"]["measured"]["delta"]["rmse"] = 2 ** -0.5
        record["result"]["measured"]["winner"] = "rate"
        self.assertTrue(self.checks(record))
        rate.update(spikes=[dict(channel=0, t_ms=0.0, polarity=True)], spike_count=1)
        rate["spike_preview"] = copy.deepcopy(rate["spikes"])
        self.assertEqual(self.checks(record), [])

    def test_canonical_six_decimal_rmse_is_accepted(self):
        record = fixture()
        record["scenario"]["signal"] = [1.0, 0.0]
        for side in ("rate", "delta"):
            record["result"]["measured"][side]["rmse"] = 0.707107
        self.assertEqual(self.checks(record), [])
        record["result"]["measured"]["rate"]["rmse"] = 0.7072
        self.assertTrue(self.checks(record))

    def test_winner_uses_full_events_when_rmse_rounds_equal(self):
        record = fixture()
        record["scenario"]["signal"] = [0.000001, 0.000001]
        record["scenario"]["parameters"]["delta_threshold"] = 0.000001
        measured = record["result"]["measured"]
        measured["rate"]["rmse"] = 0.000001
        measured["delta"].update(
            reconstruction=[0.000001, 0.0], rmse=0.000001, spike_count=2,
            spikes=[dict(channel=0, t_ms=0.0, polarity=True),
                    dict(channel=0, t_ms=1.0, polarity=False)])
        measured["delta"]["spike_preview"] = copy.deepcopy(measured["delta"]["spikes"])
        measured["winner"] = "delta"
        self.assertEqual(self.checks(record), [])
        measured["winner"] = "tie"
        self.assertTrue(self.checks(record))

    def test_preview_is_exact_bounded_prefix(self):
        record = fixture()
        record["result"]["measured"]["rate"]["spike_preview_truncated"] = True
        self.assertTrue(self.checks(record))
        record = fixture()
        record["result"]["measured"]["rate"]["spike_preview"] = [
            dict(channel=0, t_ms=0.0, polarity=True)]
        self.assertTrue(self.checks(record))

    def test_rate_probability_and_intervention_bounds(self):
        record = fixture()
        record["scenario"]["parameters"].update(rate_hz=1000.0, sample_ms=100.0)
        self.assertTrue(self.checks(record))
        record = fixture("neuromod-lif-v1")
        record["scenario"]["parameters"]["threshold"] = 99.0
        self.assertTrue(self.checks(record))

    def test_neuron_trace_and_event_time_are_bound_to_signal(self):
        for key, value in (("v_trace", [0.0]), ("spikes", [1000.0]),
                           ("spikes", [-1.0])):
            record = fixture("neuromod-lif-v1")
            record["result"]["measured"]["before"][key] = value
            self.assertTrue(self.checks(record))


if __name__ == "__main__":
    unittest.main()
