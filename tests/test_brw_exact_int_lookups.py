"""Pin main's exact-int rule on the brw r212/r383/r395 leftover lookups.

``rNNN_pair_at`` and ``rNNN_pair_for_round`` accept exactly ``int``. ``True``
and every other ``int`` subclass (an ``IntEnum`` member here) are refused with
the ``BrwError`` code and message of main's ``type(value) is int`` spelling.
Each stand-in carries a value the lookup would otherwise accept, so only the
type decides. The error class is read from ``catalog`` itself: other brw test
modules import ``brw`` by its flat name, and the class must be the one the
lookups raise whichever form was loaded first.
"""

from __future__ import annotations

import unittest
from enum import IntEnum

from pipelines.brw import catalog

LOOKUPS = (
    ("r212", catalog.r212_pair_at, catalog.r212_pair_for_round,
     catalog.R212_CATALOG_FIRST, catalog.R212_PAIRS),
    ("r383", catalog.r383_pair_at, catalog.r383_pair_for_round,
     catalog.R383_CATALOG_FIRST, catalog.R383_PAIRS),
    ("r395", catalog.r395_pair_at, catalog.r395_pair_for_round,
     catalog.R395_CATALOG_FIRST, catalog.R395_PAIRS),
)


def int_subclass(value: int) -> int:
    """An ``IntEnum`` member equal to ``value``: an ``int``, but not exactly one."""

    return IntEnum("Exact", {"MEMBER": value}).MEMBER


class BrwExactIntLookups(unittest.TestCase):
    def test_an_exact_int_selects_the_pair(self):
        for mill, pair_at, pair_for_round, first, pairs in LOOKUPS:
            with self.subTest(mill=mill):
                self.assertIs(pair_at(1), pairs[1])
                self.assertIs(pair_for_round(first + 1), pairs[1])

    def test_true_or_an_int_enum_index_is_refused(self):
        for mill, pair_at, _pair_for_round, _first, _pairs in LOOKUPS:
            for value, shown in ((True, "True"), (int_subclass(1), "<Exact.MEMBER: 1>")):
                with self.subTest(mill=mill, value=shown):
                    with self.assertRaises(catalog.BrwError) as caught:
                        pair_at(value)
                    self.assertEqual(str(caught.exception), f"unknown_{mill}_index: {shown}")

    def test_true_or_an_int_enum_round_is_refused(self):
        for mill, _pair_at, pair_for_round, first, _pairs in LOOKUPS:
            member = int_subclass(first + 1)
            for value, shown in ((True, "True"), (member, f"<Exact.MEMBER: {first + 1}>")):
                with self.subTest(mill=mill, value=shown):
                    with self.assertRaises(catalog.BrwError) as caught:
                        pair_for_round(value)
                    self.assertEqual(str(caught.exception), f"invalid_round: {shown}")


if __name__ == "__main__":
    unittest.main()
