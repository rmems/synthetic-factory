"""Graph semantics for pipelines/nir_equivalence.py.

Covers NIR serialization, topology rules, the reference interpreter, and the
in-repo runtime adapters.
"""

import json
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nir_equivalence_support import (  # noqa: E402
    linear_graph as _linear_graph,
    stimulus as _stimulus,
)

import nir_equivalence as nir  # noqa: E402

class Serialization(unittest.TestCase):
    def test_roundtrip_is_stable(self):
        report = nir.roundtrip(_linear_graph())
        self.assertTrue(report["parse_ok"])
        self.assertTrue(report["canonical_stable"])
        self.assertTrue(report["structure_stable"])
        self.assertIsNone(report["reason_code"])

    def test_structural_digest_ignores_key_order(self):
        graph = _linear_graph()
        reordered = json.loads(json.dumps(graph))
        reordered["nodes"]["thr"] = {
            "threshold": 0.5,
            "size": 2,
            "type": "Threshold",
        }
        self.assertEqual(nir.structural_digest(graph), nir.structural_digest(reordered))

    def test_structural_digest_notices_a_new_edge(self):
        graph = _linear_graph()
        changed = json.loads(json.dumps(graph))
        changed["edges"].append(["in", "out"])
        self.assertNotEqual(nir.structural_digest(graph), nir.structural_digest(changed))

    def test_structural_digest_notices_a_changed_node_type(self):
        graph = _linear_graph()
        changed = json.loads(json.dumps(graph))
        changed["nodes"]["thr"]["type"] = "LIF"
        self.assertNotEqual(nir.structural_digest(graph), nir.structural_digest(changed))

    def test_parse_rejects_a_non_graph(self):
        with self.assertRaises(nir.GraphError):
            nir.parse(json.dumps({"nodes": {}}))


class Topology(unittest.TestCase):
    def test_feed_forward_has_no_back_edges(self):
        order, recurrent = nir.evaluation_order(_linear_graph(), "insertion")
        self.assertEqual(order, ["in", "thr", "out"])
        self.assertEqual(recurrent, set())

    def test_cycle_produces_exactly_one_back_edge(self):
        graph = {
            "name": "cycle",
            "nodes": {
                "in": {"type": "Input", "shape": [1], "size": 1},
                "a": {"type": "Threshold", "size": 1, "threshold": 0.5},
                "b": {"type": "Threshold", "size": 1, "threshold": 0.5},
                "out": {"type": "Output", "size": 1},
            },
            "edges": [["in", "a"], ["a", "b"], ["b", "a"], ["b", "out"]],
        }
        _, recurrent = nir.evaluation_order(graph, "insertion")
        self.assertEqual(len(recurrent), 1)

    def test_cycle_break_order_changes_which_edge_is_cut(self):
        graph = {
            "name": "cycle",
            "nodes": {
                "in": {"type": "Input", "shape": [1], "size": 1},
                "a_node": {"type": "Threshold", "size": 1, "threshold": 0.5},
                "z_node": {"type": "Threshold", "size": 1, "threshold": 0.5},
                "out": {"type": "Output", "size": 1},
            },
            "edges": [
                ["in", "a_node"],
                ["a_node", "z_node"],
                ["z_node", "a_node"],
                ["z_node", "out"],
            ],
        }
        _, first = nir.evaluation_order(graph, "insertion")
        _, second = nir.evaluation_order(graph, "reverse_name")
        self.assertNotEqual(first, second)

    def test_unknown_cycle_break_order_rejected(self):
        with self.assertRaises(nir.GraphError):
            nir.evaluation_order(_linear_graph(), "random")

    def test_edge_to_unknown_node_rejected(self):
        graph = _linear_graph()
        graph["edges"].append(["thr", "nowhere"])
        with self.assertRaises(nir.GraphError):
            nir.evaluation_order(graph, "insertion")


class Interpreter(unittest.TestCase):
    def test_threshold_graph_passes_input_through(self):
        outputs = nir.REFERENCE_V1.execute(_linear_graph(), _stimulus())
        self.assertEqual(outputs["output_trace"], [[1.0, 0.0]] * 4)
        self.assertEqual(outputs["spike_count"], 4)

    def test_execution_is_deterministic(self):
        first = nir.REFERENCE_V1.execute(_linear_graph(), _stimulus())
        second = nir.REFERENCE_V1.execute(_linear_graph(), _stimulus())
        self.assertEqual(first["output_trace"], second["output_trace"])

    def test_unsupported_type_raises_a_diagnostic(self):
        graph = _linear_graph()
        graph["nodes"]["thr"]["type"] = "Conv2d"
        with self.assertRaises(nir.UnsupportedConstruct) as caught:
            nir.REFERENCE_V1.execute(graph, _stimulus())
        self.assertEqual(caught.exception.node_type, "Conv2d")
        self.assertEqual(caught.exception.node, "thr")

    def test_alt_runtime_declares_li_unsupported(self):
        self.assertIn("LI", nir.REFERENCE_V1.supported_types)
        self.assertNotIn("LI", nir.REFERENCE_ALT.supported_types)

    def test_node_without_a_declared_size_is_rejected(self):
        graph = _linear_graph()
        del graph["nodes"]["thr"]["size"]
        with self.assertRaises(nir.GraphError):
            nir.REFERENCE_V1.execute(graph, _stimulus())

    def test_graph_without_an_output_is_rejected(self):
        graph = _linear_graph()
        graph["nodes"]["out"]["type"] = "Threshold"
        graph["nodes"]["out"]["threshold"] = 0.5
        with self.assertRaises(nir.GraphError):
            nir.REFERENCE_V1.execute(graph, _stimulus())

    def test_non_positive_tau_is_rejected(self):
        graph = {
            "name": "bad-tau",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [1], "size": 1},
                "lif": {"type": "LIF", "size": 1, "tau": 0.0, "v_threshold": 1.0},
                "out": {"type": "Output", "size": 1},
            },
            "edges": [["in", "lif"], ["lif", "out"]],
        }
        with self.assertRaises(nir.GraphError):
            nir.REFERENCE_V1.execute(graph, {"name": "s", "steps": 1, "events": [[1.0]]})

    def test_delay_unit_convention_shifts_the_output(self):
        graph = {
            "name": "delay",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [1], "size": 1},
                "dly": {"type": "Delay", "size": 1, "delay": 2},
                "out": {"type": "Output", "size": 1},
            },
            "edges": [["in", "dly"], ["dly", "out"]],
        }
        stimulus = {"name": "s", "steps": 5, "events": [[1.0], [0.0], [0.0], [0.0], [0.0]]}
        first = nir.REFERENCE_V1.execute(graph, stimulus)["output_trace"]
        second = nir.REFERENCE_ALT.execute(graph, stimulus)["output_trace"]
        self.assertEqual(first, [[0.0], [0.0], [1.0], [0.0], [0.0]])
        self.assertEqual(second, [[0.0], [1.0], [0.0], [0.0], [0.0]])

    def test_reset_convention_changes_the_residue(self):
        graph = {
            "name": "reset",
            "dt_s": 0.001,
            "nodes": {
                "in": {"type": "Input", "shape": [1], "size": 1},
                "lif": {
                    "type": "LIF",
                    "size": 1,
                    "tau": 0.005,
                    "r": 1.0,
                    "v_leak": 0.0,
                    "v_threshold": 1.0,
                },
                "out": {"type": "Output", "size": 1},
            },
            "edges": [["in", "lif"], ["lif", "out"]],
        }
        # dt/tau = 0.2, so the drive lifts v to 2.0: subtracting the threshold
        # leaves 1.0 behind where resetting to zero leaves nothing.
        stimulus = {"name": "s", "steps": 3, "events": [[10.0], [0.0], [0.0]]}
        subtract = nir.REFERENCE_V1.execute(graph, stimulus)
        zero = nir.REFERENCE_ALT.execute(graph, stimulus)
        self.assertNotEqual(
            subtract["final_membrane"]["lif"]["v"], zero["final_membrane"]["lif"]["v"]
        )
        self.assertEqual(zero["final_membrane"]["lif"]["v"], [0.0])


class Runtimes(unittest.TestCase):
    def test_upstream_runtimes_are_unavailable_here(self):
        report = nir.availability_report()
        for name in ("nir_rs", "nir_python", "nirtorch_snntorch"):
            with self.subTest(runtime=name):
                self.assertFalse(report[name]["available"])
                self.assertTrue(report[name]["reason_code"])
                self.assertEqual(report[name]["runtime_class"], "upstream_runtime")

    def test_in_repo_runtimes_are_available(self):
        report = nir.availability_report()
        self.assertTrue(report["nir_reference_v1"]["available"])
        self.assertTrue(report["nir_reference_v1_altorder"]["available"])

    def test_unavailable_runtime_raises_rather_than_substituting(self):
        runtime = nir.UnavailableRuntime("ghost", module="definitely_not_installed_pkg")
        with self.assertRaises(nir.RuntimeUnavailable):
            runtime.execute(_linear_graph(), _stimulus())

    def test_unavailable_runtime_entry_carries_no_outputs(self):
        scenario = nir.build_scenario(nir.GRAPH_SPECS[0], steps=4)
        entry = nir.execute_runtime(nir.UPSTREAM_RUNTIMES[0], scenario)
        self.assertEqual(entry["status"], nir.STATUS_UNAVAILABLE)
        self.assertNotIn("outputs", entry)
        self.assertNotIn("output_digest", entry)
        self.assertTrue(entry["reason_code"])

    def test_roundtrip_evidence_names_the_runtime_adapter(self):
        scenario = nir.build_scenario(nir.GRAPH_SPECS[0], steps=4)
        for runtime in nir.IN_REPO_RUNTIMES:
            with self.subTest(runtime=runtime.name):
                entry = nir.execute_runtime(runtime, scenario)
                self.assertEqual(entry["roundtrip"]["runtime"], runtime.name)
                self.assertEqual(
                    entry["roundtrip"]["adapter"], f"{runtime.name}.nir_json"
                )



if __name__ == "__main__":
    unittest.main()
