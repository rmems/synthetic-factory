"""Tests for pipelines/nir_equivalence.py."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = (
    REPO
    / "tests"
    / "fixtures"
    / "parity-run"
    / "nir-cross-runtime-equivalence"
    / "batch-r01.jsonl"
)
sys.path.insert(0, str(PIPELINES))

import nir_equivalence as nir  # noqa: E402
import oracle_contract as contract  # noqa: E402

WHERE = "unit:1"


def _fixture_records():
    return [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _cli(args):
    return subprocess.run(
        [sys.executable, str(PIPELINES / "nir_equivalence.py"), *args],
        capture_output=True,
        text=True,
    )


def _linear_graph():
    return {
        "name": "unit",
        "dt_s": 0.001,
        "nodes": {
            "in": {"type": "Input", "shape": [2], "size": 2},
            "thr": {"type": "Threshold", "size": 2, "threshold": 0.5},
            "out": {"type": "Output", "size": 2},
        },
        "edges": [["in", "thr"], ["thr", "out"]],
    }


def _stimulus(steps=4):
    return {"name": "unit", "steps": steps, "channels": 2,
            "events": [[1.0, 0.0] for _ in range(steps)]}


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


class Comparison(unittest.TestCase):
    def test_convention_delta_lists_only_differences(self):
        scenario = nir.build_scenario(nir.GRAPH_SPECS[0], steps=4)
        entries = [
            nir.execute_runtime(runtime, scenario) for runtime in nir.IN_REPO_RUNTIMES
        ]
        delta = {item["convention"] for item in nir.convention_delta(entries)}
        self.assertEqual(delta, {"reset", "delay_unit", "cycle_break_order"})

    def test_attribution_only_names_conventions_the_graph_exercises(self):
        for spec in nir.GRAPH_SPECS:
            scenario = nir.build_scenario(spec, steps=10)
            entries = [
                nir.execute_runtime(runtime, scenario)
                for runtime in (*nir.IN_REPO_RUNTIMES, *nir.UPSTREAM_RUNTIMES)
            ]
            comparison = nir.compare_runtimes(scenario, entries)
            relevant = set(comparison["attribution"]["relevant_conventions"])
            types = {node["type"] for node in scenario["graph"]["nodes"].values()}
            with self.subTest(graph=spec["id"]):
                if "Delay" not in types:
                    self.assertNotIn("delay_unit", relevant)
                if not types & {"LIF", "IF"}:
                    self.assertNotIn("reset", relevant)

    def test_internal_state_divergence_does_not_flip_the_verdict(self):
        # Event outputs can agree while membrane state has already drifted.
        records = nir.generate_records(round_number=1, steps=10)
        drifted = [
            record
            for record in records
            if "DIVERGENCE_INTERNAL_STATE" in record["result"]["reason_codes"]
            and record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        self.assertTrue(drifted, "expected at least one match with state drift")

    def test_numeric_noise_within_tolerance_does_not_require_equal_digests(self):
        scenario = nir.build_scenarios(steps=4)[0]
        first = nir.execute_runtime(nir.REFERENCE_V1, scenario)
        second = copy.deepcopy(first)
        second["runtime"] = "within_tolerance"
        second["outputs"]["output_trace"][0][0] += nir.NUMERIC_TOL / 2
        second["output_digest"] = "sha256:" + "1" * 64
        pair = nir._compare_pair(first, second)
        self.assertTrue(pair["agree"], pair)

    def test_event_streams_are_compared_exactly(self):
        scenario = nir.build_scenarios(steps=4)[0]
        first = nir.execute_runtime(nir.REFERENCE_V1, scenario)
        second = copy.deepcopy(first)
        second["runtime"] = "different_events"
        if second["outputs"]["spike_events"]:
            second["outputs"]["spike_events"][0]["t_step"] += 1
        else:
            second["outputs"]["spike_events"].append({"t_step": 0, "channel": 0})
        second["outputs"]["spike_count"] = len(second["outputs"]["spike_events"])
        pair = nir._compare_pair(first, second)
        self.assertFalse(pair["agree"])
        self.assertIn("DIVERGENCE_EVENT_STREAM", pair["reason_codes"])

    def test_fewer_than_two_executed_runtimes_is_never_a_match(self):
        comparison = {
            "executed_runtimes": ["only_one"],
            "executed_count": 1,
            "parse_write_parity": {"per_runtime": {}, "agree": True},
            "structure_parity": {"digests": {}, "agree": True},
            "output_parity": {"comparable": False, "agree": None, "pairs": []},
            "unsupported": [],
            "unavailable": [],
        }
        verdict, codes = nir.verdict_for(comparison)
        self.assertEqual(verdict, contract.VERDICT_INCONCLUSIVE)
        self.assertIn("NO_EXECUTED_RUNTIME_PAIR", codes)

    def test_unsupported_construct_yields_the_unsupported_verdict(self):
        comparison = {
            "executed_runtimes": [],
            "executed_count": 0,
            "parse_write_parity": {"per_runtime": {}, "agree": True},
            "structure_parity": {"digests": {}, "agree": True},
            "output_parity": {"comparable": False, "agree": None, "pairs": []},
            "unsupported": [{"runtime": "a", "reason_code": "UNSUPPORTED_CONSTRUCT"}],
            "unavailable": [],
        }
        verdict, codes = nir.verdict_for(comparison)
        self.assertEqual(verdict, contract.VERDICT_UNSUPPORTED)
        self.assertIn("UNSUPPORTED_CONSTRUCT", codes)


class Generation(unittest.TestCase):
    def test_generated_records_validate(self):
        records = nir.generate_records(round_number=1, steps=6)
        self.assertEqual(nir.validate_records(records), [])

    def test_generation_is_deterministic(self):
        first = nir.generate_records(round_number=1, steps=6)
        second = nir.generate_records(round_number=1, steps=6)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_catalog_covers_feed_forward_recurrent_and_unsupported(self):
        classes = {spec["class"] for spec in nir.GRAPH_SPECS}
        self.assertIn("feed_forward", classes)
        self.assertIn("recurrent", classes)
        self.assertIn("delay_sensitive", classes)
        self.assertIn("boundary", classes)
        self.assertIn("unusual_parameters", classes)
        self.assertIn("unsupported", classes)

    def test_catalog_produces_every_verdict_kind(self):
        verdicts = {
            record["result"]["verdict"]
            for record in nir.generate_records(round_number=1, steps=10)
        }
        self.assertIn(contract.VERDICT_MATCH, verdicts)
        self.assertIn(contract.VERDICT_MISMATCH, verdicts)
        self.assertIn(contract.VERDICT_UNSUPPORTED, verdicts)

    def test_evidence_scope_is_stated_on_every_record(self):
        for record in nir.generate_records(round_number=1, steps=4):
            self.assertIn("in-repo", record["oracle"]["evidence_scope"])
            self.assertIn("nir-rs", record["oracle"]["evidence_scope"])

    def test_evidence_scope_matches_the_actual_executed_count(self):
        for record in nir.generate_records(round_number=1, steps=4):
            executed = record["result"]["comparison"]["executed_count"]
            scope = record["oracle"]["evidence_scope"]
            with self.subTest(record=record["id"], executed=executed):
                if executed >= 2:
                    self.assertIn("executed in-repo runtimes", scope)
                elif executed == 1:
                    self.assertIn("only one in-repo runtime executed", scope)
                else:
                    self.assertIn("no in-repo runtime executed", scope)


class Validation(unittest.TestCase):
    def setUp(self):
        self.records = nir.generate_records(round_number=1, steps=6)
        self.mismatch = next(
            record
            for record in self.records
            if record["result"]["verdict"] == contract.VERDICT_MISMATCH
        )

    def test_fixture_validates(self):
        self.assertEqual(nir.validate_records(_fixture_records()), [])

    def test_suppressed_divergence_is_caught(self):
        record = copy.deepcopy(self.mismatch)
        record["result"]["verdict"] = contract.VERDICT_MATCH
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("DIVERGENCE_SUPPRESSED" in error for error in errors))

    def test_fabricated_output_trace_is_caught_by_re_execution(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["outputs"]["output_trace"][0][0] += 1.0
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("COMPARISON_MISMATCH" in error for error in errors))

    def test_forged_output_digest_is_caught(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["output_digest"] = "sha256:" + "0" * 64
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_unavailable_runtime_may_not_carry_outputs(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_UNAVAILABLE
        )
        entry["outputs"] = {"output_trace": [[1.0]], "spike_events": [], "spike_count": 0}
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("UNAVAILABLE_RUNTIME_HAS_OUTPUT" in error for error in errors)
        )

    def test_unknown_runtime_status_is_caught(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"][0]["status"] = "probably_ran"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("RUNTIME_STATUS_UNKNOWN" in error for error in errors))

    def test_erased_unsupported_diagnostic_is_caught(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if item["result"]["verdict"] == contract.VERDICT_UNSUPPORTED
            )
        )
        record["result"]["comparison"]["unsupported"] = []
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_status_downgraded_to_hide_a_coverage_gap_is_caught(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if any(
                    entry["status"] == nir.STATUS_UNSUPPORTED
                    for entry in item["oracle"]["runtimes"]
                )
            )
        )
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_UNSUPPORTED
        )
        entry["status"] = nir.STATUS_UNAVAILABLE
        entry["reason_code"] = "RUNTIME_NOT_INSTALLED"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("UNSUPPORTED_NOT_DIAGNOSED" in error for error in errors))

    def test_tampered_graph_breaks_the_structure_digest(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["graph"]["edges"].append(["in", "out"])
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("STRUCTURE_DIGEST_MISMATCH" in error for error in errors))

    def test_tampered_stimulus_breaks_the_input_fixture(self):
        record = copy.deepcopy(self.records[0])
        record["scenario"]["stimulus"]["events"][0][0] = 9.0
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("INPUT_FIXTURE_MISMATCH" in error for error in errors))

    def test_edited_spike_count_is_caught(self):
        record = copy.deepcopy(self.mismatch)
        pair = record["result"]["comparison"]["output_parity"]["pairs"][0]
        pair["spike_count_b"] = pair["spike_count_a"]
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("COMPARISON_MISMATCH" in error for error in errors))

    def test_every_pair_and_state_metric_is_bound_to_reexecution(self):
        mutations = (
            lambda comparison: comparison["output_parity"]["pairs"][0].__setitem__(
                "max_abs_error", 99.0
            ),
            lambda comparison: comparison["output_parity"]["pairs"][0].__setitem__(
                "max_abs_state_error", 99.0
            ),
            lambda comparison: comparison["output_parity"]["pairs"][0].__setitem__(
                "shape_match", False
            ),
            lambda comparison: comparison["state_parity"].__setitem__("agree", False),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                record = copy.deepcopy(self.records[0])
                mutate(record["result"]["comparison"])
                errors = nir.validate_record(record, WHERE)
                self.assertTrue(
                    any("COMPARISON_MISMATCH" in error for error in errors), errors
                )

    def test_oracle_fixture_and_identical_flag_are_load_bearing(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["input_fixture"]["sha256"] = "sha256:" + "0" * 64
        record["oracle"]["identical_input_fixture"] = False
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("INPUT_FIXTURE_MISMATCH" in error for error in errors))

    def test_fabricated_summary_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["result"]["summary"] = "all runtimes agree"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("result.summary" in error for error in errors), errors)


class UnfalsifiableClaims(unittest.TestCase):
    """A runtime this validator cannot re-execute may never be marked executed."""

    def setUp(self):
        self.records = nir.generate_records(round_number=1, steps=6)

    def _claim_upstream_executed(self):
        """Dress the absent nir_rs up as having produced a real trace."""
        record = copy.deepcopy(self.records[0])
        real = next(
            entry
            for entry in record["oracle"]["runtimes"]
            if entry["status"] == nir.STATUS_EXECUTED
        )
        ghost = next(
            entry for entry in record["oracle"]["runtimes"] if entry["runtime"] == "nir_rs"
        )
        ghost.update(
            {
                "status": nir.STATUS_EXECUTED,
                "outputs": copy.deepcopy(real["outputs"]),
                "output_digest": real["output_digest"],
                "roundtrip": copy.deepcopy(real["roundtrip"]),
            }
        )
        ghost.pop("reason_code", None)
        ghost.pop("detail", None)
        record["result"]["comparison"] = nir.compare_runtimes(
            record["scenario"], record["oracle"]["runtimes"]
        )
        verdict, codes = nir.verdict_for(record["result"]["comparison"])
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        record["result"]["derived_from"] = [
            entry["output_digest"]
            for entry in record["oracle"]["runtimes"]
            if entry["status"] == nir.STATUS_EXECUTED
        ]
        return record

    def test_absent_upstream_runtime_cannot_be_claimed_as_executed(self):
        errors = nir.validate_record(self._claim_upstream_executed(), WHERE)
        self.assertTrue(
            any("re-execute" in error for error in errors), errors
        )

    def test_the_same_claim_is_caught_through_the_deep_layer(self):
        import check_records

        errors, _warnings, _kind, _id = check_records.check_record(
            self._claim_upstream_executed(), WHERE
        )
        self.assertTrue(any("re-execute" in error for error in errors))

    def test_unknown_runtime_class_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"][0]["runtime_class"] = "trust_me"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("runtime_class" in error for error in errors))

    def test_executed_entry_missing_output_fields_is_rejected(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        del entry["outputs"]["spike_count"]
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_runtime_inventory_cannot_drop_unavailable_oracles(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"] = [
            entry
            for entry in record["oracle"]["runtimes"]
            if entry["runtime"] in {"nir_reference_v1", "nir_reference_v1_altorder"}
        ]
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("complete ordered inventory" in error for error in errors))

    def test_duplicate_runtime_names_are_rejected(self):
        record = copy.deepcopy(self.records[0])
        record["oracle"]["runtimes"][1] = copy.deepcopy(
            record["oracle"]["runtimes"][0]
        )
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("complete ordered inventory" in error for error in errors))

    def test_absent_upstream_runtime_cannot_claim_unsupported(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item for item in record["oracle"]["runtimes"] if item["runtime"] == "nir_rs"
        )
        entry["status"] = nir.STATUS_UNSUPPORTED
        entry["reason_code"] = "UNSUPPORTED_CONSTRUCT"
        entry["unsupported_node"] = "invented"
        entry["unsupported_type"] = "Invented"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("unavailable runtime" in error for error in errors), errors)

    def test_runtime_declarations_are_bound_to_the_implementation(self):
        for key, replacement in (
            ("conventions", {"reset": "fabricated"}),
            ("supported_types", ["Input", "Output"]),
        ):
            with self.subTest(key=key):
                record = copy.deepcopy(self.records[0])
                record["oracle"]["runtimes"][0][key] = replacement
                errors = nir.validate_record(record, WHERE)
                self.assertTrue(any(key in error for error in errors), errors)


class ScrubbedDivergence(unittest.TestCase):
    """Divergence diagnostics must not be editable out of a record."""

    def setUp(self):
        self.records = nir.generate_records(round_number=1, steps=10)
        self.divergent = next(
            record
            for record in self.records
            if "DIVERGENCE_SPIKE_COUNT" in record["result"]["reason_codes"]
        )

    def test_scrubbing_spike_count_and_state_is_caught(self):
        record = copy.deepcopy(self.divergent)
        first, second = [
            entry
            for entry in record["oracle"]["runtimes"]
            if entry["status"] == nir.STATUS_EXECUTED
        ][:2]
        second["outputs"]["spike_count"] = first["outputs"]["spike_count"]
        second["outputs"]["final_membrane"] = copy.deepcopy(
            first["outputs"]["final_membrane"]
        )
        record["result"]["comparison"] = nir.compare_runtimes(
            record["scenario"], record["oracle"]["runtimes"]
        )
        verdict, codes = nir.verdict_for(record["result"]["comparison"])
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        # The scrub really does delete diagnostics...
        self.assertNotIn("DIVERGENCE_SPIKE_COUNT", codes)
        # ...and re-execution catches it.
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("do not match a re-execution" in error for error in errors), errors
        )

    def test_forged_roundtrip_block_is_caught(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["roundtrip"]["structure_digest"] = "sha256:" + "0" * 64
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(
            any("ROUNDTRIP_STRUCTURE_MISMATCH" in error for error in errors), errors
        )

    def test_forged_parse_failure_claim_is_caught(self):
        record = copy.deepcopy(self.records[0])
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_EXECUTED
        )
        entry["roundtrip"]["canonical_stable"] = False
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(errors)

    def test_unsupported_diagnostic_is_rederived_from_the_exception(self):
        record = copy.deepcopy(
            next(
                item
                for item in self.records
                if any(
                    entry["status"] == nir.STATUS_UNSUPPORTED
                    for entry in item["oracle"]["runtimes"]
                )
            )
        )
        entry = next(
            item
            for item in record["oracle"]["runtimes"]
            if item["status"] == nir.STATUS_UNSUPPORTED
        )
        entry["unsupported_node"] = "invented"
        errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("UNSUPPORTED_NOT_DIAGNOSED" in error for error in errors))


class MalformedRecordsDoNotCrash(unittest.TestCase):
    def setUp(self):
        self.record = nir.generate_records(round_number=1, steps=4)[0]

    def _assert_reports(self, mutate):
        record = copy.deepcopy(self.record)
        mutate(record)
        try:
            errors = nir.validate_record(record, WHERE)
        except Exception as exc:  # noqa: BLE001 - the point is that none escape
            self.fail(f"validation raised {type(exc).__name__}: {exc}")
        self.assertTrue(errors)

    def test_truthy_non_dict_oracle(self):
        self._assert_reports(lambda record: record.__setitem__("oracle", ["x"]))

    def test_executed_entry_with_empty_outputs(self):
        def mutate(record):
            entry = next(
                item
                for item in record["oracle"]["runtimes"]
                if item["status"] == nir.STATUS_EXECUTED
            )
            entry["outputs"] = {}

        self._assert_reports(mutate)

    def test_non_dict_runtime_entry(self):
        self._assert_reports(
            lambda record: record["oracle"]["runtimes"].append("not an object")
        )

    def test_missing_graph(self):
        self._assert_reports(lambda record: record["scenario"].pop("graph"))

    def test_nodes_array_is_reported_instead_of_crashing(self):
        self._assert_reports(
            lambda record: record["scenario"]["graph"].__setitem__("nodes", [])
        )


class TrainingViews(unittest.TestCase):
    def test_views_preserve_every_record(self):
        records = _fixture_records()
        views, errors = nir.build_training_views(records)
        self.assertEqual(errors, [])
        self.assertEqual(len(views), len(records))

    def test_divergent_records_are_flagged(self):
        views, _ = nir.build_training_views(_fixture_records())
        failed = [view for view in views if view["parity_failed"]]
        self.assertTrue(failed)
        for view in failed:
            self.assertTrue(view["reason_codes"])

    def test_view_carries_the_evidence_scope(self):
        views, _ = nir.build_training_views(_fixture_records())
        for view in views:
            self.assertIn("in-repo", view["evidence_scope"])

    def test_view_names_unavailable_runtimes_too(self):
        views, _ = nir.build_training_views(_fixture_records())
        self.assertTrue(
            any("nir_rs:unavailable" in target for target in views[0]["execution_targets"])
        )

    def test_prompt_does_not_invent_a_runtime_pair(self):
        record = next(
            item
            for item in _fixture_records()
            if item["result"]["comparison"]["executed_count"] < 2
        )
        prompt = nir.training_view(record)["prompt"]
        self.assertNotIn("more than one runtime", prompt)
        self.assertTrue("only one runtime" in prompt or "did not execute" in prompt)

    def test_filtering_out_divergences_is_rejected(self):
        records = _fixture_records()
        views = [
            nir.training_view(record)
            for record in records
            if record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("TRAINING_VIEW_HIDES_FAILURE" in error for error in errors))

    def test_completion_is_rederived_instead_of_copying_summary(self):
        record = copy.deepcopy(_fixture_records()[0])
        record["result"]["summary"] = "fabricated completion"
        self.assertNotEqual(
            nir.training_view(record)["completion"], "fabricated completion"
        )


class Cli(unittest.TestCase):
    def test_availability_reports_no_upstream_runtime(self):
        result = _cli(["availability"])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["nir_rs"]["available"])

    def test_generate_then_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            generated = _cli(["generate", tmp, "--round", "3", "--steps", "6"])
            self.assertEqual(generated.returncode, 0, generated.stderr)
            out = Path(json.loads(generated.stdout)["written"])
            self.assertEqual(out.name, "batch-r03.jsonl")
            validated = _cli(["validate", str(out)])
            self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_validate_rejects_a_suppressed_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            records = _fixture_records()
            for record in records:
                record["result"]["verdict"] = contract.VERDICT_MATCH
            path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            result = _cli(["validate", str(path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("DIVERGENCE_SUPPRESSED", result.stderr)

    def test_training_view_cli_emits_one_line_per_record(self):
        result = _cli(["training-view", str(FIXTURE)])
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), len(_fixture_records()))

    def test_training_view_cli_refuses_an_invalid_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            record = copy.deepcopy(_fixture_records()[0])
            record["result"]["summary"] = "fabricated completion"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = _cli(["training-view", str(path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("result.summary", result.stderr)


if __name__ == "__main__":
    unittest.main()
