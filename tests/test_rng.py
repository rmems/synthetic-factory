#!/usr/bin/env python3
"""The shared seeded draw stream (``pipelines/oracle_grounded/rng.py``).

Lifted from the fault-recovery family: the stream values pinned by
``test_fault_scenario`` must not move, the seed domain is refused with a
``ContractError`` and never a raw ``ValueError``, and the fault family's
``DrawStream`` is the shared one behind its own codes.
"""

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from distill_contract_test_support import REPO, envelope  # noqa: E402
from oracle_grounded import fault_scenario, fault_vocabulary as fv, rng  # noqa: E402


class PinnedStream(unittest.TestCase):
    def test_the_first_draw_of_seed_zero_is_pinned(self):
        """``sha256(b"0:1")[:8]`` big-endian: the value ``test_fault_scenario`` pins too."""
        self.assertEqual(rng.DrawStream(0).bits(), 17227200041832915037)
        self.assertEqual(rng.DrawStream(0).bits(), fault_scenario.DrawStream(0).bits())

    def test_draws_are_deterministic_and_seed_distinct(self):
        first, twin = rng.DrawStream(3), rng.DrawStream(3)
        self.assertEqual([first.bits() for _ in range(8)], [twin.bits() for _ in range(8)])
        self.assertNotEqual([rng.DrawStream(4).bits() for _ in range(4)], [twin.bits() for _ in range(4)])
        self.assertEqual((first.seed, first.draws), (3, 8))

    def test_choice_randint_sample_and_chance_use_one_draw_each(self):
        stream = rng.DrawStream(11)
        self.assertIn(stream.choice("ab"), "ab")
        self.assertTrue(all(1 <= stream.randint(1, 4) <= 4 for _ in range(50)))
        self.assertEqual(sorted(stream.sample(["c0", "c1", "c2", "c3"], 4)), ["c0", "c1", "c2", "c3"])
        self.assertIsInstance(stream.chance(0.5), bool)
        self.assertEqual(stream.draws, 1 + 50 + 4 + 1)
        self.assertEqual(rng.DrawStream(fv.MAX_SEED).bits(), rng.DrawStream(rng.MAX_SEED).bits())

    def test_no_random_module_anywhere_near_the_stream(self):
        self.assertNotIn("import random", inspect.getsource(rng))


class SeedRefusals(unittest.TestCase):
    def test_non_integers_and_bools_are_refused_with_a_contract_error(self):
        for seed in ("abc", 2.0, True, None, [1]):
            with self.subTest(seed=repr(seed)), self.assertRaises(envelope.ContractError) as caught:
                rng.DrawStream(seed)
            self.assertIn("genuine integer", str(caught.exception))

    def test_the_64_bit_domain_is_refused_without_formatting_the_value(self):
        for seed in (-1, rng.MAX_SEED + 1, 10**5000):
            with self.subTest(bits=seed.bit_length()), self.assertRaises(envelope.ContractError) as caught:
                rng.DrawStream(seed)
            self.assertIn("must lie in [0", str(caught.exception))
            self.assertNotIn("got", str(caught.exception))
        self.assertEqual(rng.DrawStream(rng.MAX_SEED).draws, 0)

    def test_the_fault_family_keeps_its_own_codes_in_front(self):
        self.assertTrue(issubclass(fault_scenario.DrawStream, rng.DrawStream))
        with self.assertRaises(fv.FaultRefusal) as caught:
            fault_scenario.DrawStream(-1)
        self.assertEqual(caught.exception.code, fv.FINDING_SEED_OUT_OF_DOMAIN)
        with self.assertRaises(fv.FaultRefusal) as caught:
            fault_scenario.DrawStream(True)
        self.assertEqual(caught.exception.code, fv.FINDING_SEED_NOT_AN_INTEGER)


class ImportBinding(unittest.TestCase):
    def test_both_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.oracle_grounded import rng as packaged

        self.assertIs(packaged, rng)
        self.assertIs(packaged.DrawStream, rng.DrawStream)


if __name__ == "__main__":
    unittest.main()
