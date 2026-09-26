"""Generator descriptions and analog traces cannot invent oracle measurements."""

import copy
import unittest

from hardware_parity_support import WHERE
import hardware_parity as hp
import nir_equivalence as nir
from nir_equivalence_support import linear_graph, stimulus


class GeneratorMeasurements(unittest.TestCase):
    def test_generator_owned_sections_refuse_nested_oracle_fields(self):
        for module in (hp, nir):
            original = module.generate_records()[0]
            for section in ("scenario", "intervention", "candidate_prediction", "generator"):
                for field in ("spikes", "result", "oracle", "measurement"):
                    with self.subTest(family=module.__name__, section=section, field=field):
                        record = copy.deepcopy(original)
                        record[section] = record[section] or {}
                        record[section]["extra"] = [{field: {"claimed": True}}]
                        errors = module.validate_record(record, WHERE)
                        self.assertTrue(any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in e for e in errors), errors)


class SpikeObservations(unittest.TestCase):
    def test_long_li_trace_remains_nonspiking_after_display_rounding(self):
        scenario = next(s for s in nir.build_scenarios(steps=200) if s["id"] == "nir-partial-coverage-li")
        run = nir.IN_REPO_RUNTIMES[0].execute(scenario["graph"], scenario["stimulus"])
        self.assertEqual(max(row[0] for row in run["output_trace"]), 1.0)
        self.assertEqual(run["spike_events"], [])
        self.assertEqual(run["spike_count"], 0)

    def test_delay_preserves_actual_threshold_spike_events(self):
        graph = linear_graph()
        graph["nodes"]["delay"] = {"type": "Delay", "size": 2, "delay": 1}
        graph["edges"] = [["in", "thr"], ["thr", "delay"], ["delay", "out"]]
        run = nir.IN_REPO_RUNTIMES[0].execute(graph, stimulus())
        expected = [{"t_step": step, "channel": 0} for step in range(1, 4)]
        self.assertEqual(run["spike_events"], expected)

    def test_affine_analog_outputs_are_not_spike_events(self):
        graph = linear_graph()
        graph["nodes"]["thr"] = {"type": "Affine", "size": 2, "weight": [[2, 0], [0, 2]]}
        run = nir.IN_REPO_RUNTIMES[0].execute(graph, stimulus())
        self.assertEqual(run["output_trace"], [[2.0, 0.0]] * 4)
        self.assertEqual(run["spike_events"], [])

    def test_transparent_feedback_keeps_real_spike_events(self):
        graph = linear_graph()
        graph["nodes"]["delay"] = {"type": "Delay", "size": 2, "delay": 1}
        graph["edges"] = [["in", "thr"], ["thr", "delay"], ["delay", "delay"], ["delay", "out"]]
        run = nir.IN_REPO_RUNTIMES[0].execute(graph, stimulus())
        self.assertEqual(run["output_trace"], [[0.0, 0.0], [1.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
        self.assertEqual(run["spike_events"], [{"t_step": step, "channel": 0} for step in range(1, 4)])
