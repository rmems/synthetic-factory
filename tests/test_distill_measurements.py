#!/usr/bin/env python3
"""Direct tests of the measurement checks and the energy-claim scan
(``distill_measurements`` and the no-theoretical-energy rule)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared test support, by bare name

from distill_contract_test_support import (  # noqa: E402
    measured_energy_reading,
    minimal_record,
    oc,
)


class MeasurementContract(unittest.TestCase):
    def test_unknown_quantity_is_refused_at_build_time(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("vibes", 1.0, "simulator_state")

    def test_unit_must_match_the_registry(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("latency_ms", 1.0, "clock", unit="s")

    def test_non_finite_value_is_refused(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("latency_ms", float("inf"), "clock")

    def test_energy_requires_a_measured_energy_meter(self):
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("energy_j", 8.0, "analytic_op_count")
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("energy_j", 8.0, "intel_rapl_powercap", measured=False)
        reading = oc.new_measurement("energy_j", 8.0, "intel_rapl_powercap")
        self.assertEqual(reading["unit"], "J")

    def test_a_modelled_meter_never_claims_a_measured_reading(self):
        # `measured` follows the meter registry for every quantity, not only
        # energy: a modelled meter with measured: true used to satisfy the
        # curation gate's NO_MEASURED_READING check on the producer's say-so.
        reading = oc.new_measurement("latency_ms", 3.5, "analytic_op_count")
        self.assertFalse(reading["measured"])
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("latency_ms", 3.5, "analytic_op_count", measured=True)
        self.assertTrue(oc.new_measurement("latency_ms", 3.5, "simulator_clock")["measured"])
        lowered = oc.new_measurement("latency_ms", 3.5, "simulator_clock", measured=False)
        self.assertFalse(lowered["measured"])

    def test_a_modelled_meter_claiming_measured_is_a_finding_that_blocks_curation(self):
        record = minimal_record()
        reading = oc.new_measurement("recovery_latency_ms", 4.0, "analytic_op_count")
        reading["measured"] = True  # the tamper: a model's output relabelled
        record["result"]["measurements"] = [reading]
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        errors = oc.check_measurements(record, "x")
        self.assertTrue(any("MODELLED_METER_CLAIMS_MEASURED" in error for error in errors))
        eligible, _reasons = oc.curation_eligible(record, errors)
        self.assertFalse(eligible)
        # Honestly labelled, the same reading is structurally valid but still
        # not a measured result, so curation refuses it for that reason.
        reading["measured"] = False
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        self.assertEqual(oc.check_measurements(record, "x"), [])
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("NO_MEASURED_READING", reasons)

    def test_measurements_must_declare_an_oracle_source(self):
        record = minimal_record()
        record["result"]["measurements"][0]["source"] = "generator"
        errors = oc.check_measurements(record, "x")
        self.assertTrue(any("source must be 'oracle'" in error for error in errors))


class NoTheoreticalEnergy(unittest.TestCase):
    def test_modelled_energy_measurement_is_rejected(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            {
                "quantity": "energy_j",
                "value": 0.0000023,
                "unit": "J",
                "meter": "synops_model",
                "measured": True,
                "source": "oracle",
            }
        )
        errors = oc.check_no_theoretical_energy_claim(record, "x")
        self.assertTrue(any("THEORETICAL_ENERGY_CLAIM" in error for error in errors))

    def test_spike_count_energy_estimate_is_rejected(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            {
                "quantity": "energy_j",
                "value": 0.001,
                "unit": "J",
                "meter": "spike_energy_model",
                "measured": True,
                "source": "oracle",
            }
        )
        self.assertTrue(oc.check_no_theoretical_energy_claim(record, "x"))

    def test_energy_denominated_preference_needs_measured_energy(self):
        record = minimal_record()
        record["result"]["preference"] = {
            "preferred": "a",
            "cost_quantity": "energy_j",
        }
        errors = oc.check_no_theoretical_energy_claim(record, "x")
        self.assertTrue(
            any("preference" in error and "THEORETICAL" in error for error in errors)
        )

    def test_measured_energy_backs_an_energy_preference(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            oc.new_measurement("energy_j", 8.0, "intel_rapl_powercap")
        )
        record["result"]["preference"] = {
            "preferred": "a",
            "cost_quantity": "energy_j",
        }
        self.assertEqual(oc.check_no_theoretical_energy_claim(record, "x"), [])


class EnergyClaimScan(unittest.TestCase):
    """D3: energy numbers are legal only in explicitly supported structures."""

    def claims(self, record) -> list:
        return [
            e for e in oc.check_no_theoretical_energy_claim(record, "x")
            if "THEORETICAL_ENERGY_CLAIM" in e
        ]

    def test_the_energy_tokens_derive_from_the_registry(self):
        self.assertEqual(oc.ENERGY_UNITS, frozenset({"J", "W", "Wh"}))
        for token in ("j", "pj", "uj", "mw", "kwh", "energy", "joules", "watt"):
            self.assertIn(token, oc.ENERGY_TOKENS)
        for token in ("while", "when", "kops", "wall", "power"):
            self.assertNotIn(token, oc.ENERGY_TOKENS)

    def test_lists_under_energy_keys_are_claims(self):
        record = minimal_record()
        record["result"]["energy_j_samples"] = [1e-7, 2e-7]
        record["result"]["joules"] = [1e-7]
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        for path in ("result.energy_j_samples[0]", "result.energy_j_samples[1]", "result.joules[0]"):
            self.assertIn(path, claims[0])

    def test_a_nested_object_identified_by_its_unit_is_a_claim(self):
        record = minimal_record()
        record["result"]["derived"] = {"energy": {"value": 1e-7, "unit": "J"}}
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("result.derived.energy (no measured energy_j/energy_per_op_j reading", claims[0])

    def test_a_relocated_measurement_object_needs_backing_and_a_measuring_meter(self):
        relocated = {"quantity": "energy_j", "value": 1e-7, "meter": "synops_model", "measured": False}
        record = minimal_record()
        record["result"]["modelled_energy"] = relocated
        self.assertIn("result.modelled_energy (modelled meter 'synops_model')", self.claims(record)[0])
        # Backed by a measured reading and naming the measuring meter: legal.
        record["result"]["measurements"].append(measured_energy_reading())
        record["result"]["modelled_energy"] = {
            "quantity": "energy_j", "value": 8.0, "meter": "intel_rapl_powercap", "measured": True,
        }
        self.assertEqual(self.claims(record), [])
        # Backing never launders a modelled meter or a declared-unmeasured value.
        record["result"]["modelled_energy"]["meter"] = "synops_model"
        self.assertIn("modelled meter", self.claims(record)[0])
        record["result"]["modelled_energy"] = {"quantity": "energy_j", "value": 8.0, "measured": False}
        self.assertIn("declared unmeasured", self.claims(record)[0])

    def test_unit_suffixed_keys_are_claims(self):
        record = minimal_record()
        record["result"].update(
            {"power_mw": 12.5, "pj_per_synop": 23.6, "uj_total": 1.2, "cost_j": 3e-9}
        )
        record["result"]["candidates"] = [{"id": "a", "est_pj": 23.6}]
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        for path in (
            "result.power_mw", "result.pj_per_synop", "result.uj_total", "result.cost_j",
            "result.candidates[0].est_pj",
        ):
            self.assertIn(path, claims[0])

    def test_false_positives_and_metadata_stay_legal(self):
        record = minimal_record()
        record["result"].update(
            {"ticks_while_degraded": 4, "quality_when_degraded": 0.9, "throughput_kops": 12}
        )
        record["result"]["meter_probe"] = {
            "cost_is_energy": True,
            "cost_quantity": "energy_j",
            "selected": "intel_rapl_powercap",
            "probed": [
                {"meter": "intel_rapl_powercap", "available": False,
                 "measures_energy": True, "detail": "/sys/class/powercap absent"},
            ],
        }
        self.assertEqual(self.claims(record), [])

    def test_relabelling_the_result_as_energy_needs_a_measured_reading(self):
        # ENERGY-METER-IDENTITY (b): result.cost_quantity flipped to energy_j
        # beside numeric content, with no measured energy reading behind it.
        record = minimal_record()
        record["result"].update({"cost_quantity": "energy_j", "reference_objective": 0.218})
        self.assertIn("result (no measured energy_j reading backs it)", self.claims(record)[0])
        record["result"]["measurements"].append(measured_energy_reading())
        self.assertEqual(self.claims(record), [])

    def test_preference_is_governed_by_the_backing_rule_once(self):
        record = minimal_record()
        record["result"]["preference"] = {
            "cost_quantity": "energy_j", "cost_value": 2.8e-6, "quality_floor": 0.98,
            "preferred": "analytic_kkt",
        }
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("result.preference: THEORETICAL_ENERGY_CLAIM", claims[0])
        record["result"]["measurements"].append(measured_energy_reading())
        self.assertEqual(self.claims(record), [])

    def test_candidate_cost_objects_need_backing(self):
        candidate = {
            "id": "analytic_kkt", "cost_quantity": "energy_j", "cost_value": 1e-6,
            "cost_meter": "intel_rapl_powercap", "task_quality": 1.0, "safety_ok": True,
        }
        record = minimal_record()
        record["result"]["candidates"] = [candidate]
        self.assertIn("result.candidates[0] (no measured energy_j reading", self.claims(record)[0])
        record["result"]["candidates"] = {"analytic_kkt": dict(candidate)}
        self.assertIn("result.candidates.analytic_kkt (no measured", self.claims(record)[0])
        record["result"]["measurements"].append(measured_energy_reading())
        self.assertEqual(self.claims(record), [])

    def test_measurement_entries_stay_with_the_measurement_rule(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            {"quantity": "energy_j", "value": 2.3e-6, "unit": "J", "meter": "synops_model",
             "measured": True, "source": "oracle"}
        )
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)  # reported once, by the measurement rule
        self.assertIn("result.measurements[1]", claims[0])
        record["result"]["measurements"][1] = measured_energy_reading()
        self.assertEqual(self.claims(record), [])

    def test_detail_of_a_measured_energy_reading_is_not_a_claim(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            oc.new_measurement(
                "energy_j", 8.0, "intel_rapl_powercap",
                detail={"raw_counter_uj": 1000000, "samples_uj": [1.0, 2.0]},
            )
        )
        self.assertEqual(self.claims(record), [])

    def test_the_hit_cap_bounds_collected_findings_and_the_walk_is_flat(self):
        # The cap bounds how many findings are collected, not the work of
        # visiting the record or the length of a path; the listing stays
        # short here because each path is short.
        record = minimal_record()
        record["result"]["junk"] = [{"unit": "J", "value": index} for index in range(10_000)]
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("scan capped", claims[0])
        self.assertLess(len(claims[0]), 4_000)
        deep: dict = {}
        cursor = deep
        for _ in range(5_000):
            cursor["k"] = {}
            cursor = cursor["k"]
        cursor["energy_j"] = 1e-7
        record = minimal_record()
        record["result"]["deep"] = deep
        self.assertEqual(len(self.claims(record)), 1)


class EnergyIdentityAcrossContainers(unittest.TestCase):
    """Energy identity survives containers, checked through the public contract API.

    An object that identifies energy through its own fields, or a container
    under an energy-identifying key, is a claim whenever any number sits
    beneath it, however many lists or dicts deep. Cases A to D are the
    owner's reproducers on 766f06fe, where only A was reported.
    """

    CASES = {
        "A object with a numeric value": {"quantity": "energy_j", "unit": "J", "value": 5.0},
        "B object whose value is a list": {"quantity": "energy_j", "unit": "J", "value": [5.0]},
        "C object whose value is a dict": {
            "quantity": "energy_j", "unit": "J", "value": {"sample": 5.0},
        },
        "D energy-keyed container": {"energy_j": {"value": 5.0}},
        "E object whose value is a nested list": {
            "quantity": "energy_j", "unit": "J", "value": [[5.0]],
        },
        "F energy-keyed list of objects": {"energy_j": [{"sample": 5.0}]},
    }
    IDENTIFIED_OBJECTS = (
        "A object with a numeric value",
        "B object whose value is a list",
        "C object whose value is a dict",
        "E object whose value is a nested list",
    )
    ENERGY_KEYED = ("D energy-keyed container", "F energy-keyed list of objects")

    def findings(self, extra, backed: bool = False) -> list:
        record = minimal_record()
        if backed:
            record["result"]["measurements"].append(measured_energy_reading())
        record["result"]["extra"] = extra
        return [
            e for e in oc.check_no_theoretical_energy_claim(record, "x")
            if "THEORETICAL_ENERGY_CLAIM" in e
        ]

    def test_unbacked_energy_identity_is_a_claim_through_any_container(self):
        for name, extra in self.CASES.items():
            with self.subTest(case=name):
                findings = self.findings(extra)
                self.assertEqual(len(findings), 1, findings)
                self.assertIn("result.extra", findings[0])

    def test_backing_makes_identified_objects_legal_but_not_bare_energy_keys(self):
        for name in self.IDENTIFIED_OBJECTS:
            with self.subTest(case=name):
                self.assertEqual(self.findings(self.CASES[name], backed=True), [])
        # A container under a bare energy key names no meter and no quantity
        # of its own, so no reading can back it (R2 has no backing exemption).
        for name in self.ENERGY_KEYED:
            with self.subTest(case=name):
                self.assertEqual(len(self.findings(self.CASES[name], backed=True)), 1)

    def test_nonnumeric_metadata_under_an_energy_identity_is_not_a_claim(self):
        for extra in (
            {"quantity": "energy_j", "unit": "J", "note": "planned", "tags": ["draft"]},
            {"energy_j": {"unit": "J", "meter": "intel_rapl_powercap", "available": False}},
            {"quantity": "energy_j", "unit": "J", "value": {"note": "none", "flags": [True]}},
        ):
            with self.subTest(extra=extra):
                self.assertEqual(self.findings(extra), [])



class MeasurementDomainErrors(unittest.TestCase):
    """The per-measurement findings of ``check_measurements``, by message."""

    def findings(self, item):
        record = minimal_record()
        record["result"]["measurements"] = [item]
        return oc.check_measurements(record, "x")

    def reading(self, **changes):
        item = oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock")
        item.update(changes)
        return item

    def test_domain_findings(self):
        cases = {
            "negative latency": (self.reading(value=-1.0), "recovery_latency_ms cannot be negative"),
            "ratio above one": (
                oc.new_measurement("corrupt_ratio", 1.5, "simulator_clock"), "corrupt_ratio must lie in [0, 1]"
            ),
            "value is a string": (self.reading(value="fast"), "value must be a finite number"),
            "unknown quantity": (self.reading(quantity="vibes"), "unknown quantity 'vibes'"),
            "unit disagrees with the registry": (self.reading(unit="s"), "must declare unit"),
            "empty meter": (self.reading(meter=""), "meter must be a non-empty string"),
            "measured is a string": (self.reading(measured="yes"), "measured must be a boolean"),
            "not an object": ("4 ms", "measurement must be an object"),
        }
        for name, (item, fragment) in cases.items():
            with self.subTest(case=name):
                errors = self.findings(item)
                self.assertTrue(any(fragment in e for e in errors), (fragment, errors))

    def test_a_result_that_is_not_an_object_or_has_no_array_is_a_finding(self):
        record = minimal_record()
        record["result"] = "done"
        self.assertEqual(oc.check_measurements(record, "x"), ["x.result must be an object"])
        record["result"] = {"status": "measured", "measurements": {}}
        self.assertEqual(oc.check_measurements(record, "x"), ["x.result.measurements must be an array"])

    def test_a_valid_reading_has_no_findings(self):
        self.assertEqual(self.findings(self.reading()), [])


class WalkKeysPublicSurface(unittest.TestCase):
    """``walk_keys`` is exported: every dict entry beneath a value, with its path."""

    def test_walk_keys_yields_dict_entries_at_every_depth_through_lists(self):
        value = {"a": 1, "b": {"c": [{"d": 2}, 3]}}
        self.assertEqual(
            list(oc.walk_keys(value, "result")),
            [
                ("result.a", "a", 1),
                ("result.b", "b", {"c": [{"d": 2}, 3]}),
                ("result.b.c", "c", [{"d": 2}, 3]),
                ("result.b.c[0].d", "d", 2),
            ],
        )

    def test_walk_keys_yields_nothing_for_a_scalar_and_only_entries_for_a_list(self):
        self.assertEqual(list(oc.walk_keys(5, "x")), [])
        self.assertEqual(list(oc.walk_keys([1, {"k": 2}], "x")), [("x[1].k", "k", 2)])


class EnergyRuleEdges(unittest.TestCase):
    """Branches of the energy rule the matrix rows do not reach on their own."""

    def claims(self, record):
        return [
            e for e in oc.check_no_theoretical_energy_claim(record, "x")
            if "THEORETICAL_ENERGY_CLAIM" in e
        ]

    def test_energy_from_a_measuring_but_non_energy_meter_is_a_claim(self):
        record = minimal_record()
        record["result"]["measurements"].append(
            {"quantity": "energy_j", "value": 1.0, "unit": "J", "meter": "simulator_clock",
             "measured": True, "source": "oracle"}
        )
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("needs a meter in", claims[0])

    def test_non_object_and_non_energy_entries_are_left_to_the_measurement_rule(self):
        record = minimal_record()
        record["result"]["measurements"] += ["4 ms", {"quantity": "latency_ms", "value": 1.0}]
        self.assertEqual(self.claims(record), [])
        self.assertTrue(oc.check_measurements(record, "x"))

    def test_a_result_that_is_not_an_object_yields_no_energy_findings(self):
        record = minimal_record()
        record["result"] = "done"
        self.assertEqual(oc.check_no_theoretical_energy_claim(record, "x"), [])



class MeasurementDetailShape(unittest.TestCase):
    def test_detail_must_be_an_object_in_the_check_and_the_builder(self):
        record = minimal_record()
        record["result"]["measurements"][0]["detail"] = "not an object"
        errors = oc.check_measurements(record, "x")
        self.assertTrue(any("detail must be an object" in e for e in errors), errors)
        with self.assertRaises(oc.ContractError):
            oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock", detail="nope")
        with_detail = oc.new_measurement(
            "recovery_latency_ms", 4.0, "simulator_clock", detail={"ticks": 3}
        )
        self.assertEqual(with_detail["detail"], {"ticks": 3})


class BackedObjectsNeedAnEnergyMeter(unittest.TestCase):
    """Post-ready finding: backing never launders a meter that is not an energy meter.

    The measurement rule already refuses energy from a measuring but
    non-energy meter; an S3 object naming one used to pass whenever a
    measured reading backed its quantity.
    """

    def object_claims(self, meter):
        record = minimal_record()
        record["result"]["measurements"].append(measured_energy_reading())
        extra = {"quantity": "energy_j", "unit": "J", "value": 8.0, "measured": True}
        if meter is not None:
            extra["meter"] = meter
        record["result"]["extra"] = extra
        return [
            e for e in oc.check_no_theoretical_energy_claim(record, "x")
            if "THEORETICAL_ENERGY_CLAIM" in e
        ]

    def test_a_backed_object_naming_a_non_energy_or_unknown_meter_is_a_claim(self):
        for meter in ("simulator_clock", "made_up_meter"):
            with self.subTest(meter=meter):
                claims = self.object_claims(meter)
                self.assertEqual(len(claims), 1, claims)
                self.assertIn(f"meter {meter!r} is not an energy meter", claims[0])

    def test_a_backed_object_with_an_energy_meter_or_no_meter_stays_legal(self):
        self.assertEqual(self.object_claims("intel_rapl_powercap"), [])
        self.assertEqual(self.object_claims(None), [])

    def test_a_cost_meter_is_judged_beside_a_valid_meter(self):
        record = minimal_record()
        record["result"]["measurements"].append(measured_energy_reading())
        for cost_meter, fragment in (
            ("synops_model", "modelled meter 'synops_model'"),
            ("simulator_clock", "meter 'simulator_clock' is not an energy meter"),
        ):
            with self.subTest(cost_meter=cost_meter):
                record["result"]["extra"] = {
                    "quantity": "energy_j", "unit": "J", "value": 8.0,
                    "meter": "intel_rapl_powercap", "cost_meter": cost_meter,
                }
                claims = [
                    e for e in oc.check_no_theoretical_energy_claim(record, "x")
                    if "THEORETICAL_ENERGY_CLAIM" in e
                ]
                self.assertEqual(len(claims), 1, claims)
                self.assertIn(fragment, claims[0])


class BackingShelterNothingBeneath(unittest.TestCase):
    """Post-ready findings: identity reads every field, and backing shelters no key beneath."""

    def claims(self, record) -> list:
        return [
            e for e in oc.check_no_theoretical_energy_claim(record, "x")
            if "THEORETICAL_ENERGY_CLAIM" in e
        ]

    def test_a_non_energy_field_does_not_mask_its_energy_counterpart(self):
        for budget in (
            {"quantity": "latency_ms", "cost_quantity": "energy_j", "cost_value": 9999.0},
            {"unit": "ms", "cost_unit": "J", "cost_value": 9999.0},
            {"quantity": "task_quality", "cost_unit": "J", "cost_value": 9999.0},
        ):
            with self.subTest(budget=budget):
                record = minimal_record()
                record["result"]["budget"] = budget
                claims = self.claims(record)
                self.assertEqual(len(claims), 1, claims)
                self.assertIn("result.budget (no measured", claims[0])

    def test_a_preference_denominated_by_unit_alone_needs_backing(self):
        record = minimal_record()
        record["result"]["preference"] = {"preferred": "a", "cost_unit": "J", "cost_value": 2.8e-6}
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("result.preference: THEORETICAL_ENERGY_CLAIM", claims[0])
        record["result"]["measurements"].append(measured_energy_reading())
        self.assertEqual(self.claims(record), [])
        # Watt-hours name no registry quantity, so nothing can back them.
        record["result"]["preference"]["cost_unit"] = "Wh"
        self.assertIn("denominated in 'an energy unit'", self.claims(record)[0])

    def test_an_identity_on_result_itself_shelters_nothing_beneath_it(self):
        record = minimal_record()
        record["result"]["measurements"].append(measured_energy_reading())
        record["result"]["cost_quantity"] = "energy_j"
        record["result"]["extra"] = {"projected_energy_j": 999.0}
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("result.extra.projected_energy_j", claims[0])

    def test_every_declared_quantity_needs_its_own_backing(self):
        record = minimal_record()
        record["result"]["measurements"].append(measured_energy_reading())
        for x in (
            {"quantity": "energy_j", "value": 1.0, "cost_quantity": "power_w", "cost_value": 9999},
            {"quantity": "energy_j", "value": 1.0, "cost_unit": "W", "cost_value": 9999},
        ):
            with self.subTest(x=x):
                record["result"]["x"] = x
                claims = self.claims(record)
                self.assertEqual(len(claims), 1, claims)
                self.assertIn("result.x (no measured power_w reading backs it)", claims[0])
        record["result"]["x"] = {
            "quantity": "energy_j", "value": 1.0, "cost_quantity": "energy_j", "cost_value": 2.0,
        }
        self.assertEqual(self.claims(record), [])

    def test_a_backed_object_shelters_no_energy_key_beneath_it(self):
        record = minimal_record()
        record["result"]["measurements"].append(measured_energy_reading())
        record["result"]["x"] = {"quantity": "energy_j", "value": 1.0, "modeled_power_w": 500}
        claims = self.claims(record)
        self.assertEqual(len(claims), 1, claims)
        self.assertIn("result.x.modeled_power_w", claims[0])
        del record["result"]["x"]["modeled_power_w"]
        self.assertEqual(self.claims(record), [])


if __name__ == "__main__":
    unittest.main()


class IntegerCounts(unittest.TestCase):
    """Executed-check counts are integers (Greptile on #195); older counts keep their domain (#199)."""

    def test_a_fractional_check_count_is_refused_by_the_builder_and_found_by_the_check(self):
        for quantity in sorted(oc.INTEGER_QUANTITIES):
            with self.subTest(quantity=quantity):
                with self.assertRaises(oc.ContractError):
                    oc.new_measurement(quantity, 1.5, "python_subprocess_harness")
                with self.assertRaises(oc.ContractError):
                    oc.new_measurement(quantity, True, "python_subprocess_harness")
                reading = oc.new_measurement(quantity, 3, "python_subprocess_harness")
                self.assertEqual(reading["value"], 3)
                record = minimal_record()
                record["result"]["measurements"] = [dict(reading, value=1.5)]
                findings = oc.check_measurements(record, "x")
                self.assertEqual(len(findings), 1, findings)
                self.assertIn("must be an integer", findings[0])
                record["result"]["measurements"] = [reading]
                self.assertEqual(oc.check_measurements(record, "x"), [])

    def test_the_older_count_quantities_keep_their_historical_domain(self):
        self.assertFalse(oc.INTEGER_QUANTITIES & {"healthy_channel_count", "dropped_event_count", "repeats"})
        self.assertTrue(oc.INTEGER_QUANTITIES.issubset(oc.NON_NEGATIVE_QUANTITIES))

