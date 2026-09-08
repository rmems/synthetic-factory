#!/usr/bin/env python3
"""Direct tests of ``fault_vocabulary``: the vocabularies, the code sets, the
coded refusal type, the oracle-label declaration and the import binding."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import (
    FAULT_MODULES,
    REPO,
    envelope,
    fault_oracle,
    fault_vocabulary as fv,
    oc,
)


class Vocabularies(unittest.TestCase):
    def test_the_nine_disturbances_keep_their_seeded_order(self):
        self.assertEqual(
            fv.DISTURBANCES,
            (
                "sensor_loss", "stale_sensor", "event_jitter", "burst_corruption", "thermal_excursion",
                "missing_channel", "malformed_spike_burst", "delayed_result", "temporary_saturation",
            ),
        )
        self.assertEqual(set(fv.PARAMETER_SPEC), set(fv.DISTURBANCES))
        self.assertEqual(set(fv.PREDICTION_BY_KIND), set(fv.DISTURBANCES))

    def test_six_outcomes_each_labelled_and_placed_once_in_the_precedence(self):
        self.assertEqual(len(fv.OUTCOMES), 6)
        self.assertEqual(set(fv.OUTCOME_LABELS), set(fv.OUTCOMES))
        self.assertEqual(sorted(fv.OUTCOME_PRECEDENCE), sorted(fv.OUTCOMES))
        self.assertEqual(fv.OUTCOME_PRECEDENCE[0], "fail_closed")
        self.assertEqual(fv.OUTCOME_PRECEDENCE[-1], "continue")

    def test_the_relay_defaults_and_the_family_are_registered(self):
        self.assertEqual(len(fv.SYSTEM_KEYS), 17)
        self.assertIn(fv.FAMILY, oc.FAMILIES)
        self.assertLessEqual(set(fv.QUANTITY_METER_ROLES), set(oc.QUANTITY_UNITS))
        self.assertEqual(fv.MALFORMED_INTEGRITY_KINDS, {"non_monotonic_time", "negative_amplitude"})

    def test_reason_and_finding_codes_are_unique_and_disjoint(self):
        self.assertEqual(len(fv.REASON_CODES), 16)
        self.assertEqual(len(fv.REASON_CODE_SET), 16)
        self.assertEqual(len(fv.FINDING_CODES), 28)
        self.assertEqual(len(fv.FINDING_CODE_SET), 28)
        self.assertFalse(fv.REASON_CODE_SET & fv.FINDING_CODE_SET)
        self.assertFalse(fv.FINDING_CODE_SET & oc.ORACLE_ONLY_KEYS)

    def test_default_system_never_aliases_the_module_constant(self):
        copied = fv.default_system()
        self.assertEqual(copied, fv.DEFAULT_SYSTEM)
        self.assertIsNot(copied["channels"], fv.DEFAULT_SYSTEM["channels"])
        copied["channels"].append("ghost")
        self.assertEqual(fv.DEFAULT_SYSTEM["channels"], ["c0", "c1", "c2", "c3"])

    def test_identity_strings_are_the_chosen_literals(self):
        self.assertEqual(fv.ORACLE_NAME, "relay-reflex-sim")
        self.assertEqual(
            fv.ORACLE_IMPLEMENTATION,
            "pipelines/oracle_grounded/fault_simulator.py:RelayReflexSimulator",
        )
        self.assertEqual(fv.PRODUCER, "pipelines/oracle_grounded/fault_oracle.py")
        self.assertEqual(fv.GENERATOR_NAME, "fault-scenario-generator")


class CodedRefusals(unittest.TestCase):
    def test_a_refusal_is_a_contract_error_under_both_spellings(self):
        exc = fv.FaultRefusal(fv.FINDING_INPUT_NOT_AN_OBJECT, "scenario must be an object")
        self.assertIsInstance(exc, envelope.ContractError)
        self.assertIsInstance(exc, oc.ContractError)
        self.assertEqual(str(exc), "INPUT_NOT_AN_OBJECT: scenario must be an object")
        self.assertEqual((exc.code, exc.message), ("INPUT_NOT_AN_OBJECT", "scenario must be an object"))

    def test_an_undeclared_code_is_a_programming_error(self):
        with self.assertRaises(LookupError):
            fv.FaultRefusal("NOT_A_CODE", "x")
        with self.assertRaises(LookupError):
            fv.refuse("WITHIN_TOLERANCE", "a reason code is not a finding code")

    def test_refuse_first_raises_the_first_holding_problem_only(self):
        fv.refuse_first(((False, fv.FINDING_SEED_NOT_AN_INTEGER, "a"),))
        with self.assertRaises(fv.FaultRefusal) as caught:
            fv.refuse_first(
                (
                    (False, fv.FINDING_SEED_NOT_AN_INTEGER, "skipped"),
                    (True, fv.FINDING_COUNT_OUT_OF_DOMAIN, "first"),
                    (True, fv.FINDING_INPUT_NOT_AN_OBJECT, "never reached"),
                )
            )
        self.assertEqual(caught.exception.code, fv.FINDING_COUNT_OUT_OF_DOMAIN)

    def test_shown_prints_a_value_or_its_width_when_python_refuses(self):
        """Codex round 7: ``repr`` of an integer past the string-conversion limit raises
        ``ValueError``, alone or inside a container, so a finding about one must not
        build its message with ``!r``."""
        for value in (2.0, "c0", None, True, ["c0"], 2**300):
            with self.subTest(value=repr(value)[:20]):
                self.assertEqual(fv.shown(value), repr(value))
        self.assertEqual(fv.shown(10**5000), "an unprintable int of 16610 bits")
        self.assertEqual(fv.shown([10**5000]), "an unprintable list")
        self.assertEqual(fv.shown({"ticks": 10**5000}), "an unprintable dict")

    def test_finding_code_round_trips_and_ignores_uncoded_text(self):
        text = str(fv.FaultRefusal(fv.FINDING_HORIZON_NOT_FINITE, "tick_ms 1e308: overflow"))
        self.assertEqual(fv.finding_code(text), "HORIZON_NOT_FINITE")
        self.assertIsNone(fv.finding_code("HORIZON_NOT_FINITE without a separator"))
        self.assertIsNone(fv.finding_code("prose: only"))


class LabelPolicy(unittest.TestCase):
    def test_the_sixteen_label_keys_are_declared_once_from_family_code(self):
        self.assertEqual(len(fv.ORACLE_LABEL_KEYS), 16)
        self.assertEqual(fv.RESULT_LABEL_KEYS | fv.TRACE_SUMMARY_KEYS, fv.ORACLE_LABEL_KEYS)
        self.assertEqual(fv.ORACLE_LABEL_KEYS, fault_oracle.EMITTED_LABEL_KEYS)
        self.assertIn(fv.FAMILY, oc.declared_families())
        self.assertIs(oc.oracle_label_policy(fv.FAMILY), fv.ORACLE_LABEL_POLICY)
        self.assertIs(oc.declare_oracle_labels(fv.FAMILY, fv.ORACLE_LABEL_KEYS), fv.ORACLE_LABEL_POLICY)

    def test_a_different_set_is_refused_under_a_patched_registry(self):
        from oracle_grounded import distill_labels

        with mock.patch.dict(distill_labels._POLICIES, {}, clear=True):
            oc.declare_oracle_labels(fv.FAMILY, fv.ORACLE_LABEL_KEYS)
            with self.assertRaises(oc.ContractError):
                oc.declare_oracle_labels(fv.FAMILY, fv.ORACLE_LABEL_KEYS | {"ticks"})
        self.assertIs(oc.oracle_label_policy(fv.FAMILY), fv.ORACLE_LABEL_POLICY)

    def test_label_keys_never_collide_with_a_generator_side_key(self):
        parameter_names = {name for spec in fv.PARAMETER_SPEC.values() for names in spec for name in names}
        proposal_keys = {"index", "system", "mission", "disturbance_kind", "kind", "parameters"}
        for name, keys in (
            ("system", fv.SYSTEM_KEYS),
            ("parameters", parameter_names),
            ("proposal", proposal_keys),
            ("prediction", oc.PREDICTION_FREE_KEYS),
        ):
            with self.subTest(name=name):
                self.assertFalse(fv.ORACLE_LABEL_KEYS & keys)


class ImportBinding(unittest.TestCase):
    def test_every_fault_module_is_one_object_under_both_spellings(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from oracle_grounded import fault_oracle as flat
        from pipelines.oracle_grounded import fault_oracle as packaged

        self.assertIs(flat, packaged)
        for name in FAULT_MODULES:
            with self.subTest(name=name):
                self.assertIs(
                    sys.modules[f"oracle_grounded.{name}"],
                    sys.modules[f"pipelines.oracle_grounded.{name}"],
                )
