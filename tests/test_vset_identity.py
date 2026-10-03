#!/usr/bin/env python3
"""Actor-identity normalization tests (#154).

Author, solver, reviewer, and certifier are distinct actors. Case, zero-width
characters, homoglyphs, and Unicode normalization must not make two actors
look independent, and a sentinel identity is not an identity.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import ACCEPT, codes as _codes, load_record as _load, vset  # noqa: E402


def _same_actor(record: dict, role: str, source: str, *, run_id: str) -> None:
    record[role]["model"] = record[source]["model"]
    record[role]["version"] = record[source]["version"]
    record[role]["run_id"] = run_id


class ActorIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(ACCEPT / "review-remediation-validated.json")

    def _codes(self, record: dict) -> list[str]:
        return _codes(vset.validate_record(record))

    def test_case_variant_author_is_not_a_distinct_solver(self) -> None:
        record = copy.deepcopy(self.record)
        _same_actor(
            record,
            "solver",
            "task_author",
            run_id=record["task_author"]["run_id"].upper(),
        )
        self.assertIn("vset.actors_conflated", self._codes(record))

    def test_zero_width_run_id_does_not_split_author_and_solver(self) -> None:
        record = copy.deepcopy(self.record)
        _same_actor(
            record,
            "solver",
            "task_author",
            run_id=record["task_author"]["run_id"] + "\u200b",
        )
        self.assertIn("vset.actors_conflated", self._codes(record))

    def test_homoglyph_model_does_not_split_author_and_solver(self) -> None:
        record = copy.deepcopy(self.record)
        author = record["task_author"]["run_id"]
        record["task_author"]["model"] = "fixture-author"
        record["solver"]["model"] = "fixture-auth\u043er"  # Cyrillic o
        record["solver"]["version"] = record["task_author"]["version"]
        record["solver"]["run_id"] = author
        self.assertIn("vset.actors_conflated", self._codes(record))

    def test_nfd_run_id_matches_nfc(self) -> None:
        record = copy.deepcopy(self.record)
        composed = "author-run-caf\u00e9"
        record["task_author"]["run_id"] = composed
        record["solver"]["model"] = record["task_author"]["model"]
        record["solver"]["version"] = record["task_author"]["version"]
        record["solver"]["run_id"] = "author-run-cafe\u0301"
        self.assertIn("vset.actors_conflated", self._codes(record))

    def test_reviewer_cannot_be_the_solver_or_the_author(self) -> None:
        for source in ("solver", "task_author"):
            with self.subTest(source=source):
                record = copy.deepcopy(self.record)
                _same_actor(record, "reviewer", source, run_id=record[source]["run_id"])
                self.assertIn("vset.actors_conflated", self._codes(record))

    def test_certifier_cannot_be_any_actor_identity(self) -> None:
        record = copy.deepcopy(self.record)
        record["oracle"]["certifier"] = record["reviewer"]["run_id"].upper()
        self.assertIn("vset.oracle_self_certified", self._codes(record))

    def test_sentinel_identities_are_rejected(self) -> None:
        for sentinel in ("null", "None", "unknown", "n/a", "na", "-", "0", "tbd", "placeholder"):
            with self.subTest(sentinel=sentinel):
                record = copy.deepcopy(self.record)
                record["solver"]["model"] = sentinel
                self.assertIn("vset.actor_fields_invalid", self._codes(record))

    def test_distinct_actors_still_pass(self) -> None:
        self.assertEqual(self._codes(self.record), [])


if __name__ == "__main__":
    unittest.main()
