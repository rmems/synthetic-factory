#!/usr/bin/env python3
"""Lineage, structural groups and the consumer's bucket policy (pinned against Agoge)."""

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import FIXTURE_CATALOG, fixture, program, refusal, vocabulary as cv  # noqa: E402
from code_repair import lineage  # noqa: E402

POLICY = {
    "algorithm": "sha256-atomic-bucket-v1", "seed": 20260908, "salt": "python-repair-v1",
    "weights": {"train": 80, "validation": 10, "held_out": 10},
}


class BucketPolicy(unittest.TestCase):
    def test_the_factory_bucket_reproduces_agoge_s_own_assignment(self):
        captured = json.loads((FIXTURE_CATALOG / "agoge-bucket-fixture.json").read_text(encoding="utf-8"))
        policy = lineage.SplitPolicy.from_json(captured["policy"])
        derived = {
            row["canonical_id"]: lineage.bucket_split(
                lineage.anchor_for(row.get("group_id"), row["lineage_id"]), policy
            )
            for row in captured["rows"]
        }
        self.assertEqual(derived, captured["assignment"])
        self.assertEqual(captured["captured_from"], "agoge_forger.split_materialize.assign_records")
        self.assertEqual(set(derived.values()), set(lineage.SPLITS))

    def test_grouped_rows_share_one_anchor_and_lineages_stand_alone(self):
        self.assertEqual(lineage.anchor_for("g-1", "tap-1"), "group:g-1")
        self.assertEqual(lineage.anchor_for(None, "tap-1"), "lineage:tap-1")
        policy = lineage.SplitPolicy.from_json(POLICY)
        self.assertEqual(policy.total, 100)
        self.assertEqual(len(policy.sha256), 64)
        self.assertEqual(lineage.SplitPolicy.from_json(policy.as_json()), policy)

    def test_an_unsound_policy_is_refused(self):
        for broken in (
            {**POLICY, "algorithm": "md5"}, {**POLICY, "seed": "7"}, {**POLICY, "salt": 3},
            {**POLICY, "weights": {"train": 0, "validation": 0, "held_out": 0}},
            {**POLICY, "weights": {"train": -1, "validation": 1, "held_out": 1}}, {"weights": []}, None,
        ):
            with self.subTest(policy=str(broken)[:40]), refusal(self, cv.FINDING_SPLIT_POLICY_INVALID):
                lineage.SplitPolicy.from_json(broken)


class Structure(unittest.TestCase):
    def test_renamed_copies_share_a_structure_digest_and_different_programs_do_not(self):
        text = program("sum_of_digits").text
        renamed = re.sub(r"\bsum_of_digits\b", "digit_total", text)
        renamed = re.sub(r"\bres\b", "acc", renamed)
        renamed = re.sub(r"\bn\b", "num", renamed)
        self.assertNotEqual(renamed, text)
        self.assertEqual(lineage.structure_digest(renamed), lineage.structure_digest(text))
        without_docstring = re.sub(r' {4}""".*?"""\n', "", text, count=1, flags=re.S)
        self.assertEqual(lineage.structure_digest(without_docstring), lineage.structure_digest(text))
        self.assertNotEqual(lineage.structure_digest(program("abs_val").text), lineage.structure_digest(text))
        changed_constant = text.replace("n % 10", "n % 11", 1)
        self.assertNotEqual(lineage.structure_digest(changed_constant), lineage.structure_digest(text))

    def test_groups_join_same_file_same_structure_and_linked_programs(self):
        members = (
            lineage.Member("a", "maths/x.py", "s1"), lineage.Member("b", "maths/x.py", "s2"),
            lineage.Member("c", "maths/y.py", "s2"), lineage.Member("d", "maths/z.py", "s3", ("e",)),
            lineage.Member("e", "maths/w.py", "s4"), lineage.Member("f", "maths/v.py", "s5"),
        )
        groups = lineage.group_ids(members)
        self.assertEqual(groups["a"], groups["b"])  # same file
        self.assertEqual(groups["b"], groups["c"])  # same structure, transitively with a
        self.assertEqual(groups["d"], groups["e"])  # reference link
        self.assertEqual(len({groups[k] for k in "abcdef"}), 3)
        self.assertTrue(all(g.startswith("g-") and len(g) == 34 for g in groups.values()))
        self.assertEqual(lineage.group_ids(members), groups)

    def test_the_fixture_catalog_pins_groups_and_all_three_splits(self):
        loaded = fixture()
        self.assertIsNotNone(loaded.split_policy)
        self.assertEqual({p.split for p in loaded.programs}, set(lineage.SPLITS))
        for prog in loaded.programs:
            anchor = lineage.anchor_for(prog.group_id, prog.program_id)
            self.assertEqual(lineage.bucket_split(anchor, loaded.split_policy), prog.split)


if __name__ == "__main__":
    unittest.main()
