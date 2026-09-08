#!/usr/bin/env python3
"""The SFT view: built only from the public allowlist; every leak code has a named tamper."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import catalog, refusal, smoke_run, views, vocabulary as cv  # noqa: E402


def positives():
    _summary, records, _run_dir = smoke_run()
    return [r for r in records if views.is_positive(r)]


def rejected():
    _summary, records, _run_dir = smoke_run()
    return [r for r in records if not views.is_positive(r)]


class Projection(unittest.TestCase):
    def test_a_positive_record_yields_exactly_prompt_and_completion(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                row = views.sft_row(record)
                self.assertEqual(set(row), views.VIEW_KEYS)
                broken = record["scenario"]["broken_program"]["files"]["program.py"]
                self.assertIn(f"```python\n{broken}```", row["prompt"])
                self.assertIn("### Failing doctest examples\nFailed example:", row["prompt"])
                self.assertTrue(row["prompt"].startswith(cv.TASK_SPECIFICATION))
                self.assertTrue(row["prompt"].endswith(cv.PROMPT_INSTRUCTIONS + "\n"))
                self.assertEqual(row["completion"], record["candidate_prediction"]["predicted_repair"]["files"]["program.py"])
                self.assertEqual(catalog.sha256_text(row["completion"]), record["result"]["repaired_sha256"])
                self.assertNotEqual(row["completion"], broken)
                self.assertEqual(views.view_findings(record, row), [])

    def test_the_prompt_never_contains_the_restored_span_or_the_completion(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                row = views.sft_row(record)
                site = record["intervention"]["site"]
                program = views.public_view(record).program_text.encode("utf-8")
                start = site["start_byte"]
                self.assertEqual(program[start:start + len(site["replacement_text"])].decode(), site["replacement_text"])
                self.assertNotIn(row["completion"], row["prompt"])

    def test_rejected_or_provisional_records_never_become_examples(self):
        self.assertTrue(rejected())
        for record in rejected():
            with self.subTest(record=record["id"]), refusal(self, cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE, "not an accepted"):
                views.sft_row(record)
        provisional = copy.deepcopy(positives()[0])
        provisional["result"]["oracle_status"] = cv.STATUS_PROVISIONAL
        self.assertFalse(views.is_positive(provisional))

    def test_the_agoge_row_carries_identity_and_one_rendered_text(self):
        record = positives()[0]
        row = views.agoge_row(record)
        self.assertEqual(set(row), {"canonical_id", "lineage_id", "group_id", "split", "text"})
        self.assertEqual(row["canonical_id"], record["id"])
        self.assertEqual(row["lineage_id"], record["scenario"]["source"]["program_id"])
        sft = views.sft_row(record)
        self.assertEqual(row["text"], sft["prompt"] + cv.AGOGE_SEPARATOR + sft["completion"])


class PrivateFieldsCannotInfluenceThePrompt(unittest.TestCase):
    def test_replacing_every_private_field_leaves_the_prompt_bytes_unchanged(self):
        record = positives()[0]
        expected = views.render_prompt(views.public_view(record))
        tampered = copy.deepcopy(record)
        tampered["intervention"] = {"kind": "SENTINEL", "site": {"original_text": "SENTINEL"}}
        tampered["candidate_prediction"]["predicted_repair"]["files"]["program.py"] = "SENTINEL\n"
        tampered["oracle"]["configuration"]["hidden_check"] = {"cases": ["SENTINEL"]}
        tampered["result"]["phases"] = {"original": None, "mutant": None, "repaired": None}
        tampered["result"]["reason_codes"] = ["SENTINEL"]
        tampered["provenance"]["split_lineage"] = {"lineage_id": "SENTINEL"}
        tampered["id"] = "SENTINEL"
        tampered["scenario"]["source"] = {"program_id": "SENTINEL"}
        tampered["scenario"]["public_tests"] = {"kind": "SENTINEL", "examples": []}
        self.assertEqual(views.render_prompt(views.public_view(tampered)), expected)
        self.assertNotIn("SENTINEL", expected)

    def test_the_projection_reads_three_public_fields_only(self):
        view = views.public_view(positives()[0])
        self.assertEqual(set(view.__dataclass_fields__), {"task_specification", "program_text", "evidence_text"})


class LeakCodes(unittest.TestCase):
    def setUp(self):
        self.record = copy.deepcopy(positives()[0])
        self.row = views.sft_row(self.record)

    def findings(self, record=None, row=None):
        return views.view_findings(record or self.record, row or self.row)

    def test_extra_or_missing_keys(self):
        self.assertIn(cv.LEAK_VIEW_EXTRA_KEYS, self.findings(row={**self.row, "hint": "x"}))
        self.assertIn(cv.LEAK_VIEW_EXTRA_KEYS, self.findings(row={"prompt": self.row["prompt"]}))

    def test_a_prompt_not_rendered_from_the_public_view(self):
        edited = {**self.row, "prompt": self.row["prompt"].replace("### Instructions", "### Hints\n" + self.row["completion"] + "\n### Instructions")}
        found = self.findings(row=edited)
        self.assertIn(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW, found)

    def test_a_prompt_whose_program_is_not_the_broken_text(self):
        edited = {**self.row, "prompt": self.row["prompt"].replace("```python\n", "```python\n# fixed below\n", 1)}
        found = self.findings(row=edited)
        self.assertIn(cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT, found)
        self.assertIn(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW, found)

    def test_evidence_that_is_not_the_mutant_s_failing_rows(self):
        self.record["result"]["public_failure_evidence"][0]["want"] = "something else\n"
        self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, self.findings())
        forged = copy.deepcopy(positives()[0])
        forged["result"]["public_failure_evidence"][0]["got"] = "a fabricated failure"
        self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, self.findings(record=forged))
        row = next(r for r in forged["result"]["phases"]["mutant"]["public"] if r["status"] != "pass")
        self.assertEqual(len(row["got_sha256"]), 64)
        record = copy.deepcopy(positives()[0])
        record["result"]["public_failure_omitted"] = 5
        self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, self.findings(record=record))

    def test_a_completion_that_is_not_the_verified_repair(self):
        self.assertIn(cv.LEAK_COMPLETION_NOT_VERIFIED, self.findings(row={**self.row, "completion": self.row["completion"] + "# x\n"}))
        broken = self.record["scenario"]["broken_program"]["files"]["program.py"]
        found = self.findings(row={**self.row, "completion": broken})
        self.assertIn(cv.LEAK_COMPLETION_EQUALS_BROKEN, found)
        self.assertIn(cv.LEAK_COMPLETION_NOT_VERIFIED, found)
        demoted = copy.deepcopy(self.record)
        demoted["result"]["outcome"] = cv.OUTCOME_REJECTED
        self.assertIn(cv.LEAK_COMPLETION_NOT_VERIFIED, self.findings(record=demoted))

    def test_hidden_reasoning_keys_anywhere_visible(self):
        self.assertIn(cv.LEAK_HIDDEN_REASONING_KEY, self.findings(row={**self.row, "thought": "x"}))
        self.record["scenario"]["internal_reasoning"] = "x"
        self.assertIn(cv.LEAK_HIDDEN_REASONING_KEY, self.findings())


if __name__ == "__main__":
    unittest.main()
