"""Pin the int-but-not-bool rule of the mill round, index and count guards.

Each guard accepts a plain ``int`` and refuses ``bool`` (an ``int`` subclass),
``float``, ``str`` and ``None`` with the module's own error. The cases hold for
the ``type(value) is int`` spelling and for the ``_is_plain_int`` helper alike.
"""

from __future__ import annotations

import unittest
from functools import partial
from unittest import mock

from pipelines.brw import _contract as brw
from pipelines.code_leftover3 import _contract as code_contract
from pipelines.code_leftover3 import catalog as code_catalog
from pipelines.ffpc import _contract as ffpc
from pipelines.irc import _contract as irc
from pipelines.maos import _contract as maos
from pipelines.nelb import _contract as nelb
from pipelines.pay import _contract as pay_contract
from pipelines.pay import archive_b_deferred as pay_deferred
from pipelines.pkg import _contract as pkg
from pipelines.srl import _contract as srl
from pipelines.srl import catalog as srl_catalog
from pipelines.ttf import _contract as ttf
from pipelines.ttf import catalog as ttf_catalog

NOT_PLAIN_INTS = (True, False, 1.0, "1", None)
DEFERRED_PATH = "experiments/mill_plants_x.py"
ROUND_CONTRACTS = (
    (brw, brw.BrwError),
    (srl, srl.SrlError),
    (ffpc, ffpc.FfpcRefusal),
    (maos, maos.MaosRefusal),
    (nelb, nelb.NelbRefusal),
    (pkg, pkg.PkgRefusal),
    (ttf, ttf.TtfRefusal),
    (irc, irc.IrcRefusal),
)


class RequireRoundTests(unittest.TestCase):
    def test_a_positive_plain_int_is_returned_unchanged(self):
        for module, _error in ROUND_CONTRACTS:
            with self.subTest(module=module.__name__):
                self.assertEqual(module.require_round(1), 1)
                self.assertEqual(module.require_round(7), 7)

    def test_bools_non_ints_and_non_positive_ints_are_refused(self):
        for module, error in ROUND_CONTRACTS:
            for value in (*NOT_PLAIN_INTS, 0, -1):
                with self.subTest(module=module.__name__, value=value), self.assertRaises(error):
                    module.require_round(value)


class SrlPlantAtTests(unittest.TestCase):
    def test_index_zero_is_a_plant_but_false_is_not(self):
        self.assertEqual(srl_catalog.plant_at(0), srl_catalog.PLANTS[0])
        for value in NOT_PLAIN_INTS:
            with self.subTest(value=value), self.assertRaises(srl.SrlError):
                srl_catalog.plant_at(value)


class CodedRefusalAssertions(unittest.TestCase):
    def assert_refused(self, error, code, thunk):
        with self.assertRaises(error) as caught:
            thunk()
        self.assertEqual(caught.exception.code, code)


class TtfCatalogTests(CodedRefusalAssertions):
    def setUp(self):
        self.plant = ttf_catalog.load_catalog().plants[-1]

    def test_plants_for_round_refuses_a_non_int_round(self):
        self.assertIn(self.plant, ttf_catalog.plants_for_round(self.plant.source_round))
        for value in NOT_PLAIN_INTS:
            with self.subTest(value=value):
                self.assert_refused(
                    ttf.TtfRefusal,
                    ttf.FINDING_ROUND_OUT_OF_DOMAIN,
                    partial(ttf_catalog.plants_for_round, value),
                )

    def test_plant_mapping_refuses_a_non_int_round_or_index(self):
        values = self.plant.as_mapping()
        self.assertEqual(ttf_catalog.plant_from_mapping(values), self.plant)
        for field in ("source_round", "index"):
            for value in NOT_PLAIN_INTS:
                with self.subTest(field=field, value=value):
                    self.assert_refused(
                        ttf.TtfRefusal,
                        ttf.FINDING_FIELD_INVALID,
                        partial(ttf_catalog.plant_from_mapping, {**values, field: value}),
                    )


class CodeLeftover3CatalogTests(CodedRefusalAssertions):
    def test_plants_for_round_refuses_a_non_int_round(self):
        first = code_catalog.plants_for_round(code_catalog.WAVE_FIRST_ROUND)
        self.assertEqual(len(first), code_catalog.PLANTS_PER_ROUND)
        for value in NOT_PLAIN_INTS:
            with self.subTest(value=value):
                self.assert_refused(
                    code_contract.CodeRefusal,
                    code_contract.FINDING_ROUND_OUT_OF_DOMAIN,
                    partial(code_catalog.plants_for_round, value),
                )

    def test_plant_mapping_refuses_a_non_int_line(self):
        plant = code_catalog.load_catalog().plants[0]
        values = plant.as_mapping()
        self.assertEqual(code_catalog.plant_from_mapping(values), plant)
        for value in NOT_PLAIN_INTS:
            with self.subTest(value=value):
                self.assert_refused(
                    code_contract.CodeRefusal,
                    code_contract.FINDING_FIELD_INVALID,
                    partial(code_catalog.plant_from_mapping, {**values, "line": value}),
                )


class PayDeferredCountTests(unittest.TestCase):
    def test_a_non_int_or_non_positive_pair_count_is_refused_before_git(self):
        for value in (*NOT_PLAIN_INTS, 0):
            entry = {"path": DEFERRED_PATH, "n_pairs": value}
            with self.subTest(value=value), mock.patch.object(
                pay_deferred, "git_show_deferred_source"
            ) as show:
                with self.assertRaises(pay_contract.PayRefusal) as caught:
                    pay_deferred.extract_all_deferred([entry])
                self.assertEqual(caught.exception.code, pay_contract.FINDING_CATALOG_FIELD_INVALID)
                show.assert_not_called()

    def test_a_positive_int_pair_count_reaches_the_extractor(self):
        entry = {"path": DEFERRED_PATH, "n_pairs": 2}
        extracted = ({"row": 1}, {"row": 2})
        with mock.patch.object(
            pay_deferred, "git_show_deferred_source", return_value="source"
        ), mock.patch.object(pay_deferred, "deferred_source_rows", return_value=extracted) as rows:
            self.assertEqual(pay_deferred.extract_all_deferred([entry]), extracted)
        rows.assert_called_once_with("source", path=DEFERRED_PATH, expected_rows=2)


if __name__ == "__main__":
    unittest.main()
