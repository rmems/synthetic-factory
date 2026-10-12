"""Pin the exact-int rule of the mill round, index and count guards.

Each guard accepts exactly ``int``. ``bool`` and every other ``int`` subclass
(an ``IntEnum`` member here) are refused, as are ``float``, ``str`` and
``None``, with the error, finding code and message of main's
``type(value) is int`` spelling. Each stand-in carries a value the guard would
otherwise accept, so only the type decides.
"""

from __future__ import annotations

import unittest
from enum import IntEnum
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

DEFERRED_PATH = "experiments/mill_plants_x.py"
POSITIVE_ROUND = "round must be a positive int, got {!r}"
ANY_ROUND = "round must be an int, got {!r}"
ROUND_GUARDS = (
    (brw.require_round, brw.BrwError, "invalid_round: {!r}"),
    (srl.require_round, srl.SrlError, "invalid_round: {!r}"),
    (ffpc.require_round, ffpc.FfpcRefusal, f"{ffpc.FINDING_ROUND_OUT_OF_DOMAIN}: {POSITIVE_ROUND}"),
    (maos.require_round, maos.MaosRefusal, f"{maos.FINDING_ROUND_OUT_OF_DOMAIN}: {POSITIVE_ROUND}"),
    (nelb.require_round, nelb.NelbRefusal, f"{nelb.FINDING_ROUND_OUT_OF_DOMAIN}: {POSITIVE_ROUND}"),
    (pkg.require_round, pkg.PkgRefusal, f"{pkg.FINDING_ROUND_OUT_OF_DOMAIN}: {POSITIVE_ROUND}"),
    (ttf.require_round, ttf.TtfRefusal, f"{ttf.FINDING_ROUND_OUT_OF_DOMAIN}: {POSITIVE_ROUND}"),
    (irc.require_round, irc.IrcRefusal, f"{irc.FINDING_ROUND_INVALID}: {{!r}}"),
)


def int_subclass(value: int) -> int:
    """An ``IntEnum`` member equal to ``value``: an ``int``, but not exactly one."""

    return IntEnum("Exact", {"MEMBER": value}).MEMBER


def non_exact(value: int) -> tuple[object, ...]:
    """Stand-ins for the valid ``value`` that are not exactly ``int``."""

    return (True, False, int_subclass(value), float(value), str(value), None)


def assert_refusal(case, error, expected, thunk):
    """``thunk()`` raises ``error`` whose text is exactly ``expected``."""

    with case.assertRaises(error) as caught:
        thunk()
    case.assertEqual(str(caught.exception), expected)


class RequireRoundTests(unittest.TestCase):
    def test_an_exact_positive_int_is_returned_unchanged(self):
        for guard, _error, _message in ROUND_GUARDS:
            with self.subTest(guard=guard.__module__):
                self.assertEqual(guard(7), 7)

    def test_a_bool_int_subclass_or_non_positive_round_is_refused(self):
        for guard, error, message in ROUND_GUARDS:
            for value in (*non_exact(7), 0, -1):
                with self.subTest(guard=guard.__module__, value=value):
                    assert_refusal(self, error, message.format(value), partial(guard, value))


class SrlPlantAtTests(unittest.TestCase):
    def test_an_exact_index_is_a_plant_but_a_bool_or_int_subclass_is_not(self):
        self.assertEqual(srl_catalog.plant_at(3), srl_catalog.PLANTS[3])
        for value in (*non_exact(3), len(srl_catalog.PLANTS)):
            with self.subTest(value=value):
                assert_refusal(
                    self,
                    srl.SrlError,
                    f"unknown_plant_index: {value!r}",
                    partial(srl_catalog.plant_at, value),
                )


class TtfCatalogTests(unittest.TestCase):
    def setUp(self):
        self.plant = ttf_catalog.load_catalog().plants[-1]

    def test_plants_for_round_refuses_a_non_exact_round(self):
        round_n = self.plant.source_round
        self.assertIn(self.plant, ttf_catalog.plants_for_round(round_n))
        for value in non_exact(round_n):
            with self.subTest(value=value):
                assert_refusal(
                    self,
                    ttf.TtfRefusal,
                    f"{ttf.FINDING_ROUND_OUT_OF_DOMAIN}: {ANY_ROUND.format(value)}",
                    partial(ttf_catalog.plants_for_round, value),
                )

    def test_plant_mapping_refuses_a_non_exact_round_or_index(self):
        values = self.plant.as_mapping()
        self.assertEqual(ttf_catalog.plant_from_mapping(values), self.plant)
        messages = {
            "source_round": "plant.source_round must be a positive int, got {!r}",
            "index": f"plant.index must be 1..{ttf.QUOTA_PER_ROUND}, got {{!r}}",
        }
        for field, message in messages.items():
            for value in non_exact(values[field]):
                with self.subTest(field=field, value=value):
                    assert_refusal(
                        self,
                        ttf.TtfRefusal,
                        f"{ttf.FINDING_FIELD_INVALID}: {message.format(value)}",
                        partial(ttf_catalog.plant_from_mapping, {**values, field: value}),
                    )


class CodeLeftover3CatalogTests(unittest.TestCase):
    def test_plants_for_round_refuses_a_non_exact_round(self):
        first = code_catalog.plants_for_round(code_catalog.WAVE_FIRST_ROUND)
        self.assertEqual(len(first), code_catalog.PLANTS_PER_ROUND)
        for value in non_exact(code_catalog.WAVE_FIRST_ROUND):
            with self.subTest(value=value):
                assert_refusal(
                    self,
                    code_contract.CodeRefusal,
                    f"{code_contract.FINDING_ROUND_OUT_OF_DOMAIN}: {ANY_ROUND.format(value)}",
                    partial(code_catalog.plants_for_round, value),
                )

    def test_plant_mapping_refuses_a_non_exact_line(self):
        plant = code_catalog.load_catalog().plants[0]
        values = plant.as_mapping()
        self.assertEqual(code_catalog.plant_from_mapping(values), plant)
        message = f"{code_contract.FINDING_FIELD_INVALID}: plant.line must be an int, got {{!r}}"
        for value in non_exact(plant.line):
            with self.subTest(value=value):
                assert_refusal(
                    self,
                    code_contract.CodeRefusal,
                    message.format(value),
                    partial(code_catalog.plant_from_mapping, {**values, "line": value}),
                )


class PayDeferredCountTests(unittest.TestCase):
    def test_a_non_exact_or_non_positive_pair_count_is_refused_before_git(self):
        expected = (
            f"{pay_contract.FINDING_CATALOG_FIELD_INVALID}: "
            f"{DEFERRED_PATH} n_pairs must be positive int"
        )
        for value in (*non_exact(2), 0):
            entry = {"path": DEFERRED_PATH, "n_pairs": value}
            with self.subTest(value=value), mock.patch.object(
                pay_deferred, "git_show_deferred_source"
            ) as show:
                assert_refusal(
                    self,
                    pay_contract.PayRefusal,
                    expected,
                    partial(pay_deferred.extract_all_deferred, [entry]),
                )
                show.assert_not_called()

    def test_an_exact_positive_pair_count_reaches_the_extractor(self):
        entry = {"path": DEFERRED_PATH, "n_pairs": 2}
        extracted = ({"row": 1}, {"row": 2})
        with mock.patch.object(
            pay_deferred, "git_show_deferred_source", return_value="source"
        ), mock.patch.object(pay_deferred, "deferred_source_rows", return_value=extracted) as rows:
            self.assertEqual(pay_deferred.extract_all_deferred([entry]), extracted)
        rows.assert_called_once_with("source", path=DEFERRED_PATH, expected_rows=2)


if __name__ == "__main__":
    unittest.main()
