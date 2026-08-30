#!/usr/bin/env python3
"""Focused raster-contract regression tests for Bridge curation."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    from tests.test_curate_bridge import (
        bridge,
        curate_bridge,
        decide,
        event,
        gate_snn_fixture,
    )
except ModuleNotFoundError:
    from test_curate_bridge import (  # type: ignore[no-redef]
        bridge,
        curate_bridge,
        decide,
        event,
        gate_snn_fixture,
    )

import spike_probe  # noqa: E402
from exact_json import parse_finite_json_float  # noqa: E402


class RasterArithmeticReviewFollowUps(unittest.TestCase):
    """Spike-arithmetic holes the PR #94 review found in the shared validator.

    Every downstream consumer — the curator, the publish gate, the training
    audit and the distillation probe — reads ``raster_status``, so a budget
    the validator cannot evaluate has to surface as a reason code rather than
    as an exception or as a silently accepted record.
    """

    def test_unrepresentable_spike_count_is_a_budget_defect_not_an_overflow(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 10**400
        record["raster"]["energy_uJ"] = 1.0

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])

    def test_unrepresentable_energy_evidence_stays_json_serializable(self):
        record = gate_snn_fixture()
        record["raster"]["spikes"] = 10**400
        record["raster"]["energy_pJ"] = 1.0
        record["raster"]["energy_uJ"] = 1.0

        decision = decide(record)

        self.assertEqual(decision.action, "quarantine")
        json.dumps(decision.manifest, allow_nan=False)

    def test_gate_compute_totals_survive_an_unrepresentable_spike_sum(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": 4,
                    "mean_rate_hz": 10.0,
                    "window_s": 0.05,
                    "spikes": 10**400,
                }
            ],
            "total_energy_uJ": 1.0,
        }

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        json.dumps(status["evidence"], allow_nan=False)

    def test_a_malformed_declared_gate_compute_carrier_is_not_skipped(self):
        record = gate_snn_fixture()
        record["gate_compute"] = "bad"
        record["language_view"]["trajectory"]["gate_compute"] = {
            "per_check": [{"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}]
        }

        self.assertEqual(curate_bridge._gate_compute_sidecar(record), ("gate_compute", "bad"))
        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_SPIKE_BUDGET, status["reason_codes"])

    def test_gate_compute_budget_operands_must_be_physically_positive(self):
        for check in (
            {"neurons": -2, "mean_rate_hz": -3.0, "window_s": 1.0, "spikes": 6},
            {"neurons": 0, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 0},
            {"neurons": 4, "mean_rate_hz": 10.0, "window_s": -0.05, "spikes": -2},
        ):
            with self.subTest(check=check):
                record = gate_snn_fixture()
                record["gate_compute"] = {"per_check": [check]}

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )

    def test_a_well_formed_gate_compute_budget_still_passes(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {
            "per_check": [{"neurons": 4, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 2}],
            "total_energy_pJ": 2 * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE,
        }

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertTrue(status["evidence"]["gate_compute_spike_budget_valid"])

    def test_large_integer_raster_energy_does_not_hide_one_pj_mismatch(self):
        record = gate_snn_fixture()
        spikes = 2**53
        expected_energy = spikes * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE
        record["raster"].update(
            {
                "neurons": spikes,
                "mean_rate_hz": 25,
                "window_ms": 40,
                "window_s": 0.04,
                "spikes": spikes,
                "energy_pJ": expected_energy,
            }
        )
        record["raster"].pop("energy_uJ", None)

        exact = curate_bridge.raster_status(record)
        self.assertTrue(exact["raster_valid"], exact["reason_codes"])
        self.assertEqual(
            exact["evidence"]["raster_expected_energy_pJ"],
            expected_energy,
        )
        self.assertEqual(float(expected_energy), float(expected_energy + 1))

        record["raster"]["energy_pJ"] = expected_energy + 1
        mismatch = curate_bridge.raster_status(record)
        self.assertFalse(mismatch["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, mismatch["reason_codes"])

    def test_large_integer_gate_total_does_not_hide_one_pj_mismatch(self):
        record = gate_snn_fixture()
        spikes = 2**53
        expected_energy = spikes * curate_bridge.RASTER_ENERGY_PJ_PER_SPIKE
        record["gate_compute"] = {
            "per_check": [
                {
                    "neurons": spikes,
                    "mean_rate_hz": 1,
                    "window_s": 1,
                    "spikes": spikes,
                }
            ],
            "total_energy_pJ": expected_energy,
        }

        exact = curate_bridge.raster_status(record)
        self.assertTrue(exact["raster_valid"], exact["reason_codes"])

        record["gate_compute"]["total_energy_pJ"] = expected_energy + 1
        mismatch = curate_bridge.raster_status(record)
        self.assertFalse(mismatch["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, mismatch["reason_codes"])

    def test_decimal_pj_token_does_not_hide_one_pj_mismatch(self):
        record = gate_snn_fixture()
        spikes = 10**16
        record["raster"].update(
            {
                "neurons": spikes,
                "mean_rate_hz": 25,
                "window_ms": 40,
                "window_s": 0.04,
                "spikes": spikes,
                "energy_pJ": parse_finite_json_float("230000000000000001.0"),
            }
        )
        record["raster"].pop("energy_uJ", None)

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_large_exact_uj_token_matches_integer_spike_energy(self):
        record = gate_snn_fixture()
        spikes = 2**52
        record["raster"].update(
            {
                "neurons": spikes,
                "mean_rate_hz": 25,
                "window_ms": 40,
                "window_s": 0.04,
                "spikes": spikes,
                "energy_uJ": parse_finite_json_float("103582791429.521408"),
            }
        )
        record["raster"].pop("energy_pJ", None)

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])

    def test_derived_alias_beyond_exact_bound_fails_closed(self):
        record = gate_snn_fixture()
        record["raster"].pop("window_s", None)
        record["raster"]["window_ms"] = parse_finite_json_float("1e-4096")

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_RASTER_WINDOW, status["reason_codes"])

    def test_conflicting_eligibility_time_aliases_are_rejected(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"]["tau_e_ms"] = 1

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertIn(curate_bridge.REASON_THIRD_FACTOR_INVALID, status["reason_codes"])

    def test_agreeing_eligibility_time_aliases_stay_valid(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["third_factor"]["tau_e_ms"] = 2000

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"], status["reason_codes"])
        self.assertEqual(status["evidence"]["raster_third_factor_tau_e_s"], 2.0)


class MaterializedLaneRequiresRasters(unittest.TestCase):
    """``--out-dir`` publishes a *gate-compatible* tree, so it must gate.

    The publication, audit and probe contracts all reject a Bridge record with
    no raster sidecar; materializing one into the tree this module advertises
    as gate-compatible would hand a downstream distillation run a record every
    other layer refuses.
    """

    def source_tree(self, root, records):
        source_root = Path(root) / "raw"
        batch = source_root / "neuromorphic-event-language-bridge" / "batch-r02.jsonl"
        batch.parent.mkdir(parents=True)
        batch.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )
        return source_root, batch

    def test_materialized_tree_quarantines_a_raster_less_record(self):
        with tempfile.TemporaryDirectory() as td:
            records = [bridge([event(1.0, "a"), event(2.0, "b")], "no-raster")]
            source_root, batch = self.source_tree(td, records)
            out_dir = Path(td) / "lane"

            decisions = curate_bridge.materialize_paths(
                [batch], source_root=source_root, output_dir=out_dir
            )

            self.assertEqual([d.action for d in decisions], ["quarantine"])
            self.assertIn(
                curate_bridge.REASON_RASTER_MISSING, decisions[0].manifest["reason_codes"]
            )
            self.assertFalse(
                (out_dir / "neuromorphic-event-language-bridge" / "batch-r02.jsonl").exists()
            )

    def test_materialized_tree_keeps_a_raster_backed_record(self):
        with tempfile.TemporaryDirectory() as td:
            source_root, batch = self.source_tree(td, [gate_snn_fixture()])
            out_dir = Path(td) / "lane"

            decisions = curate_bridge.materialize_paths(
                [batch], source_root=source_root, output_dir=out_dir
            )

            self.assertEqual([d.action for d in decisions], ["retain"])
            self.assertTrue(
                (out_dir / "neuromorphic-event-language-bridge" / "batch-r02.jsonl").exists()
            )

    def test_the_pure_decision_api_still_defaults_to_lenient(self):
        with tempfile.TemporaryDirectory() as td:
            records = [bridge([event(1.0, "a"), event(2.0, "b")], "no-raster")]
            _source_root, batch = self.source_tree(td, records)

            self.assertEqual([d.action for d in curate_bridge.curate_jsonl(batch)], ["retain"])
            self.assertEqual(
                [d.action for d in curate_bridge.curate_jsonl(batch, require_raster=True)],
                ["quarantine"],
            )


def zero_spike_record():
    """The reference record retuned to a legitimately zero-spike raster.

    ``round(1 * 1.0 * 0.02)`` is 0, so the budget, the 23 pJ/spike energy and
    both declared totals are all exactly zero -- the case where an
    absolute-tolerance comparison alone would accept a negative energy.
    """

    record = gate_snn_fixture()
    record["raster"].update(
        {
            "neurons": 1,
            "mean_rate_hz": 1.0,
            "window_ms": 20,
            "window_s": 0.02,
            "spikes": 0,
            "energy_pJ": 0,
            "energy_uJ": 0,
            "excerpt": [{"t_us": 5000, "neuron_id": 0}],
        }
    )
    return record


def declared_null_case(carrier):
    record = gate_snn_fixture()
    if carrier == "raster":
        record["meta"] = {"raster": copy.deepcopy(record["raster"])}
        record["raster"] = None
        return record, curate_bridge.raster_sidecar, curate_bridge.REASON_RASTER_EXCERPT
    if carrier == "gate_snn":
        record["meta"] = {"gate_snn": copy.deepcopy(record["gate_snn"])}
        record["gate_snn"] = None
        return record, curate_bridge.gate_snn_sidecar, curate_bridge.REASON_GATE_SNN_INVALID
    record["gate_compute"] = None
    record["language_view"]["trajectory"]["gate_compute"] = {
        "per_check": [{"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}]
    }
    return record, curate_bridge._gate_compute_sidecar, curate_bridge.REASON_RASTER_SPIKE_BUDGET


class DeclaredNullCarriersAndEnergyBounds(unittest.TestCase):
    """PR #94 review follow-ups on the shared sidecar/energy contract.

    Two holes the earlier carrier-precedence and overflow fixes left open:
    an explicit ``null`` sidecar was read as an absence rather than as a
    declaration, and the energy tolerance accepted small negative values
    whenever the expected energy was zero.
    """

    def test_a_declared_null_carrier_never_falls_through(self):
        for carrier in ("raster", "gate_snn", "gate_compute"):
            with self.subTest(carrier=carrier):
                record, resolver, reason = declared_null_case(carrier)
                location, value = resolver(record)

                self.assertEqual(location, carrier)
                self.assertIsNone(value)
                status = curate_bridge.raster_status(record)
                self.assertFalse(status["raster_valid"])
                self.assertIn(reason, status["reason_codes"])

    def test_a_declared_non_array_per_check_container_fails_validation(self):
        for per_check in ("bad", 7, {"neurons": 2}, None):
            with self.subTest(per_check=per_check):
                record = gate_snn_fixture()
                record["gate_compute"] = {"per_check": per_check}

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )

    def test_malformed_lower_raster_carrier_is_not_masked(self):
        record = gate_snn_fixture()
        record["meta"] = {"raster": "bad"}

        status = curate_bridge.raster_status(record)

        self.assertFalse(status["raster_valid"])
        self.assertEqual(status["raster_location"], "raster")
        self.assertIn(curate_bridge.REASON_RASTER_EXCERPT, status["reason_codes"])
        self.assertEqual(
            status["evidence"]["raster_invalid_carrier_locations"],
            ["meta.raster"],
        )

    def test_malformed_lower_gate_snn_carriers_are_not_masked(self):
        locations = (
            "meta.gate_snn",
            "language_view.trajectory.gate_snn",
            "language_view.trajectory.safety_decision.gate_snn",
        )
        for location in locations:
            with self.subTest(location=location):
                record = gate_snn_fixture()
                target = record
                for key in location.split(".")[:-1]:
                    target = target.setdefault(key, {})
                target["gate_snn"] = "bad"

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertFalse(status["gate_snn_valid"])
                self.assertIn(curate_bridge.REASON_GATE_SNN_INVALID, status["reason_codes"])
                self.assertEqual(
                    status["evidence"]["gate_snn_invalid_carrier_locations"],
                    [location],
                )

    def test_malformed_lower_gate_compute_carriers_are_not_masked(self):
        locations = (
            "language_view.trajectory.gate_compute",
            "language_view.trajectory.safety_decision.gate_compute",
        )
        for location in locations:
            with self.subTest(location=location):
                record = gate_snn_fixture()
                record["gate_compute"] = {
                    "per_check": [
                        {"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}
                    ]
                }
                target = record
                for key in location.split(".")[:-1]:
                    target = target.setdefault(key, {})
                target["gate_compute"] = "bad"

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(
                    curate_bridge.REASON_RASTER_SPIKE_BUDGET,
                    status["reason_codes"],
                )
                self.assertEqual(
                    status["evidence"]["gate_compute_invalid_carrier_locations"],
                    [location],
                )

    def test_valid_redundant_sidecars_remain_supported(self):
        record = gate_snn_fixture()
        record["meta"] = {
            "raster": copy.deepcopy(record["raster"]),
            "gate_snn": copy.deepcopy(record["gate_snn"]),
        }
        record["gate_compute"] = {
            "per_check": [{"neurons": 2, "mean_rate_hz": 10.0, "window_s": 0.05, "spikes": 1}]
        }
        record["language_view"]["trajectory"]["gate_compute"] = copy.deepcopy(
            record["gate_compute"]
        )

        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

    def test_an_absent_per_check_block_stays_optional(self):
        record = gate_snn_fixture()
        record["gate_compute"] = {}

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"])

    def test_negative_declared_raster_energy_is_rejected_inside_tolerance(self):
        for key, value in (("energy_pJ", -5e-7), ("energy_uJ", -5e-10)):
            with self.subTest(key=key):
                record = zero_spike_record()
                record["raster"][key] = value

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_negative_declared_gate_compute_totals_are_rejected(self):
        for key, value in (("total_energy_pJ", -5e-7), ("total_energy_uJ", -5e-10)):
            with self.subTest(key=key):
                record = gate_snn_fixture()
                record["gate_compute"] = {
                    "per_check": [
                        {
                            "neurons": 1,
                            "mean_rate_hz": 1.0,
                            "window_s": 0.02,
                            "spikes": 0,
                        }
                    ],
                    key: value,
                }

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(curate_bridge.REASON_RASTER_ENERGY, status["reason_codes"])

    def test_zero_energy_on_a_zero_spike_raster_still_validates(self):
        record = zero_spike_record()

        status = curate_bridge.raster_status(record)

        self.assertTrue(status["raster_valid"])


class RasterContractSecondReviewRound(unittest.TestCase):
    """PR #94 follow-up review: crashes and gaps the first round left open."""

    def test_an_oversized_declared_number_is_a_defect_not_an_overflow(self):
        """``math.isfinite(10**400)`` raises rather than returning False.

        Every numeric raster/gate guard runs through ``_is_finite_number``, so
        a staged record declaring an unbounded JSON integer crashed the
        publish gate, the training audit and strict probing instead of
        reporting an invalid contract.
        """
        self.assertFalse(curate_bridge._is_finite_number(10**400))
        self.assertFalse(curate_bridge._is_finite_number(-(10**400)))

        for field, reason in (
            ("window_ms", curate_bridge.REASON_RASTER_WINDOW),
            ("window_s", curate_bridge.REASON_RASTER_WINDOW),
            ("energy_pJ", curate_bridge.REASON_RASTER_ENERGY),
            ("energy_uJ", curate_bridge.REASON_RASTER_ENERGY),
            ("mean_rate_hz", curate_bridge.REASON_RASTER_SPIKE_BUDGET),
        ):
            with self.subTest(field=field):
                record = gate_snn_fixture()
                record["raster"][field] = 10**400

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(reason, status["reason_codes"])
                json.dumps(status["evidence"], allow_nan=False)

    def test_a_routing_entry_without_a_weight_is_invalid(self):
        """prompts/03-neuromorphic-event-language-bridge.md specifies
        ``{from, to, weight}``: without a synaptic weight a distillation
        consumer cannot reconstruct the declared connection, so a missing
        weight is as invalid as a non-numeric one."""
        for entry in (
            {"from": "pop_a", "to": "pop_b"},
            {"from": "pop_a", "to": "pop_b", "weight": None},
            {"from": "pop_a", "to": "pop_b", "weight": "0.5"},
        ):
            with self.subTest(entry=entry):
                record = gate_snn_fixture()
                record["raster"]["routing"]["table"] = [entry]

                status = curate_bridge.raster_status(record)

                self.assertFalse(status["raster_valid"])
                self.assertIn(curate_bridge.REASON_RASTER_ROUTING, status["reason_codes"])
                self.assertEqual(status["routing_table_entries"], 0)

        record = gate_snn_fixture()
        self.assertTrue(curate_bridge.raster_status(record)["raster_valid"])

    def test_materialized_trees_require_a_loadable_routing_table(self):
        """``materialize_paths`` advertises a gate-compatible tree, but a
        raster with no routing entry is exactly what the strict probe rejects
        as BRIDGE_RASTER_ROUTING_MISSING, so publishing one produced a corpus
        distillation cannot load."""
        for table in ([], None):
            with self.subTest(table=table):
                record = gate_snn_fixture()
                if table is None:
                    record["raster"]["routing"].pop("table", None)
                else:
                    record["raster"]["routing"]["table"] = table
                raw = json.dumps(record, ensure_ascii=False).encode("utf-8")
                digest = hashlib.sha256(raw).hexdigest()

                published = curate_bridge.curate_record(
                    record,
                    source_path="bridge/batch-r02.jsonl",
                    source_line=1,
                    source_hash=digest,
                    require_raster=True,
                    require_routing_table=True,
                )
                self.assertEqual(published.action, "quarantine")
                self.assertIn(
                    curate_bridge.REASON_RASTER_ROUTING,
                    published.manifest["reason_codes"],
                )

                # The pure decision API is unchanged: the table stays optional
                # there, and the publish gate keeps its own routing message.
                lenient = curate_bridge.curate_record(
                    record,
                    source_path="bridge/batch-r02.jsonl",
                    source_line=1,
                    source_hash=digest,
                    require_raster=True,
                )
                self.assertEqual(lenient.action, "retain")

    def test_materialize_paths_refuses_a_tableless_raster(self):
        record = gate_snn_fixture()
        record["raster"]["routing"]["table"] = []
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "src"
            (root / "bridge").mkdir(parents=True)
            source = root / "bridge" / "batch-r02.jsonl"
            source.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

            decisions = curate_bridge.materialize_paths(
                [source],
                source_root=root,
                output_dir=Path(td) / "tree",
            )

        self.assertEqual([d.action for d in decisions], ["quarantine"])
        self.assertIn(curate_bridge.REASON_RASTER_ROUTING, decisions[0].manifest["reason_codes"])


class SpikeProbeInputExpansion(unittest.TestCase):
    """One input reached twice must be read once."""

    def test_duplicate_probe_inputs_do_not_double_the_totals(self):
        """Naming a file twice -- or once directly and once through a
        containing directory -- appended it per target, so every raster was
        emitted twice and the spike and energy totals silently doubled,
        changing the weighting of a distillation dataset."""
        record = gate_snn_fixture()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            batch = root / "batch-r02.jsonl"
            batch.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

            once = spike_probe.jsonl_paths([batch])
            twice = spike_probe.jsonl_paths([batch, batch])
            via_dir = spike_probe.jsonl_paths([root, batch])
            relative = spike_probe.jsonl_paths([batch, Path(str(batch))])

            self.assertEqual(len(once), 1)
            self.assertEqual(twice, once)
            self.assertEqual(via_dir, once)
            self.assertEqual(relative, once)

            single, _problems = spike_probe.load_rasters([batch])
            doubled, _again = spike_probe.load_rasters([batch, batch])
            through_dir, _more = spike_probe.load_rasters([root, batch])

        self.assertEqual(len(single), 1)
        self.assertEqual(len(doubled), 1)
        self.assertEqual(len(through_dir), 1)
        self.assertEqual(
            sum(entry["spikes"] for entry in doubled),
            sum(entry["spikes"] for entry in single),
        )
        self.assertEqual(
            sum(entry["energy_pJ"] for entry in through_dir),
            sum(entry["energy_pJ"] for entry in single),
        )


if __name__ == "__main__":
    unittest.main()
