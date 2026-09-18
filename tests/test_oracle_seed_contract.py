"""Seed identity is checked before deriving or initializing a deterministic stream."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
from oracle_grounded import envelope, families, record, rng


class OracleSeedContract(unittest.TestCase):
    def test_invalid_seed_identities_cannot_create_streams_or_records(self):
        boundaries = (
            rng.Rng,
            lambda seed: rng.seed_from_label(seed, "boundary"),
            lambda seed: record.build_record(families.ENCODER_FAMILY, 0, seed=seed, environ={}),
        )
        for seed in (True, 1.9, "1", -1, rng.MAX_SEED + 1):
            for index, boundary in enumerate(boundaries):
                with self.subTest(seed=seed, boundary=index):
                    with self.assertRaises(envelope.ContractError):
                        boundary(seed)

    def test_valid_seed_streams_and_derivations_keep_their_published_vectors(self):
        vectors = (
            (0, 2736385686330453607, (16294208416658607535, 7960286522194355700, 487617019471545679)),
            (7, 2736385686330453600, (7191089600892374487, 309689372594955804, 16616101746815609346)),
            (rng.MAX_SEED, 15710358387379098008, (16490336266968443936, 16834447057089888969, 4048727598324417001)),
        )
        for seed, derived, expected in vectors:
            with self.subTest(seed=seed):
                self.assertEqual(rng.seed_from_label(seed, "boundary"), derived)
                stream = rng.Rng(seed)
                self.assertEqual(tuple(stream.next_u64() for _ in expected), expected)


if __name__ == "__main__":
    unittest.main()
