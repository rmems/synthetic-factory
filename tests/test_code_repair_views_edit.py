#!/usr/bin/env python3
"""The chat and edit views: projections of one verified pair; every leak code has a tamper."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import catalog, refusal, smoke_run, views, views_chat, views_edit
from code_repair_test_support import vocabulary as cv

PROGRAM = "program.py"


def positives():
    _summary, records, _run_dir = smoke_run()
    return [r for r in records if views.is_positive(r)]


def rejected():
    _summary, records, _run_dir = smoke_run()
    return [r for r in records if not views.is_positive(r)]


def broken_of(record):
    return record["scenario"]["broken_program"]["files"][PROGRAM]


def before_instructions(prompt):
    return prompt.rsplit("### Instructions\n", 1)[0]


class EditProjection(unittest.TestCase):
    def test_every_positive_yields_a_minimal_verified_block(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                row = views_edit.edit_row(record)
                sft = views.sft_row(record)
                self.assertEqual(set(row), views.VIEW_KEYS)
                self.assertTrue(row["prompt"].startswith(cv.TASK_SPECIFICATION))
                self.assertTrue(row["prompt"].endswith(cv.EDIT_INSTRUCTIONS + "\n"))
                self.assertEqual(before_instructions(row["prompt"]),
                                 before_instructions(sft["prompt"]))
                applied, code = views_edit.apply_block(broken_of(record), row["completion"])
                self.assertIsNone(code)
                self.assertEqual(applied, sft["completion"])
                self.assertEqual(catalog.sha256_text(applied), record["result"]["repaired_sha256"])
                search, replace = views_edit.parse_block(row["completion"])
                self.assertEqual(broken_of(record).count(search), 1)
                self.assertNotEqual(search, replace)
                self.assertLess(len(row["completion"]), len(sft["completion"]))
                self.assertEqual(views_edit.edit_findings(record, row), [])

    def test_rejected_or_provisional_records_are_refused(self):
        self.assertTrue(rejected())
        for record in rejected():
            with self.subTest(record=record["id"]), refusal(
                self, cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE, "not an accepted"
            ):
                views_edit.edit_row(record)

    def test_edit_rows_are_a_pure_function_of_the_record(self):
        record = positives()[0]
        self.assertEqual(views_edit.edit_row(record), views_edit.edit_row(copy.deepcopy(record)))


class EditTampers(unittest.TestCase):
    def setUp(self):
        self.record = positives()[0]
        self.row = views_edit.edit_row(self.record)
        self.search, self.replace = views_edit.parse_block(self.row["completion"])

    def findings(self, row=None, record=None):
        return views_edit.edit_findings(record or self.record, self.row if row is None else row)

    def with_completion(self, completion):
        return {**self.row, "completion": completion}

    def test_extra_keys_or_a_non_row(self):
        self.assertEqual(self.findings({**self.row, "extra": 1}), [cv.LEAK_VIEW_EXTRA_KEYS])
        self.assertEqual(self.findings("not a row"), [cv.LEAK_VIEW_EXTRA_KEYS])

    def test_the_prompt_must_carry_the_edit_instruction_and_the_broken_text(self):
        sft_prompt = views.sft_row(self.record)["prompt"]
        self.assertIn(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
                      self.findings({**self.row, "prompt": sft_prompt}))
        self.assertIn(cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT,
                      self.findings({**self.row, "prompt": "x"}))

    def test_malformed_blocks(self):
        block = self.row["completion"]
        divider = cv.EDIT_DIVIDER + "\n"
        cases = (
            block.replace(divider, divider + divider, 1),
            block[:-1],
            block.replace(cv.EDIT_SEARCH_MARKER, "<<<<<<< FIND"),
            "",
            None,
            views.sft_row(self.record)["completion"],
        )
        for completion in cases:
            with self.subTest(completion=completion if completion is None else completion[:24]):
                self.assertEqual(self.findings(self.with_completion(completion)),
                                 [cv.LEAK_EDIT_BLOCK_MALFORMED])

    def test_a_block_that_does_not_reproduce_the_repair(self):
        wrong = views_edit.render_block(self.search, self.replace + "    pass\n")
        self.assertEqual(self.findings(self.with_completion(wrong)), [cv.LEAK_EDIT_DOES_NOT_APPLY])
        unchanged = views_edit.render_block(self.search, self.search)
        self.assertEqual(self.findings(self.with_completion(unchanged)),
                         [cv.LEAK_COMPLETION_EQUALS_BROKEN, cv.LEAK_EDIT_DOES_NOT_APPLY])

    def test_a_wider_window_applies_but_is_not_canonical(self):
        broken = broken_of(self.record)
        lines = broken.splitlines(keepends=True)
        first_line = broken[:broken.index(self.search)].count("\n")
        self.assertGreater(first_line, 0, "the fixture window must start after the first line")
        before = lines[first_line - 1]
        wider = views_edit.render_block(before + self.search, before + self.replace)
        applied, code = views_edit.apply_block(broken, wider)
        self.assertIsNone(code)
        self.assertEqual(applied, views.sft_row(self.record)["completion"])
        self.assertEqual(self.findings(self.with_completion(wider)),
                         [cv.LEAK_EDIT_BLOCK_NOT_CANONICAL])

    def test_a_search_that_is_not_unique_cannot_apply(self):
        block = views_edit.render_block("a\n", "c\n")
        not_unique = (None, cv.LEAK_EDIT_SEARCH_NOT_UNIQUE)
        self.assertEqual(views_edit.apply_block("a\nb\na\n", block), not_unique)
        self.assertEqual(views_edit.apply_block("b\n", block), not_unique)
        self.assertEqual(views_edit.apply_block("a\nb\n", block), ("c\nb\n", None))

    def test_a_demoted_record_or_edited_evidence_is_reported(self):
        demoted = copy.deepcopy(self.record)
        demoted["result"]["oracle_status"] = cv.STATUS_PROVISIONAL
        self.assertIn(cv.LEAK_EDIT_DOES_NOT_APPLY, self.findings(record=demoted))
        edited = copy.deepcopy(self.record)
        edited["result"]["public_failure_evidence"][0]["got"] = "a fabricated failure"
        self.assertIn(cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS, self.findings(record=edited))

    def test_hidden_reasoning_keys_in_the_public_sections_are_visible(self):
        tampered = copy.deepcopy(self.record)
        tampered["scenario"]["internal_reasoning"] = "x"
        self.assertIn(cv.LEAK_HIDDEN_REASONING_KEY, self.findings(record=tampered))


class ChatProjection(unittest.TestCase):
    def test_chat_rows_carry_exactly_the_sft_pair(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                row = views_chat.chat_row(record)
                sft = views.sft_row(record)
                self.assertEqual(set(row), views_chat.CHAT_KEYS)
                self.assertEqual(views_chat.chat_pair(row), (sft["prompt"], sft["completion"]))
                self.assertEqual([m["role"] for m in row["messages"]],
                                 [views_chat.ROLE_USER, views_chat.ROLE_ASSISTANT])
                self.assertEqual(views_chat.chat_findings(record, row), [])

    def test_rejected_records_are_refused(self):
        for record in rejected():
            with self.subTest(record=record["id"]), refusal(
                self, cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE, "not an accepted"
            ):
                views_chat.chat_row(record)

    def test_tampers(self):
        record = positives()[0]
        row = views_chat.chat_row(record)
        self.assertEqual(views_chat.chat_findings(record, {**row, "extra": 1}),
                         [cv.LEAK_VIEW_EXTRA_KEYS])
        swapped = {"messages": list(reversed(row["messages"]))}
        self.assertEqual(views_chat.chat_findings(record, swapped),
                         [cv.LEAK_CHAT_MESSAGES_MALFORMED])
        three = {"messages": [*row["messages"], row["messages"][1]]}
        self.assertEqual(views_chat.chat_findings(record, three),
                         [cv.LEAK_CHAT_MESSAGES_MALFORMED])
        annotated = {"messages": [{**row["messages"][0], "thought": "x"}, row["messages"][1]]}
        self.assertEqual(views_chat.chat_findings(record, annotated),
                         [cv.LEAK_CHAT_MESSAGES_MALFORMED])
        non_text = {"messages": [{"role": "user", "content": 1}, row["messages"][1]]}
        self.assertIsNone(views_chat.chat_pair(non_text))
        edited = copy.deepcopy(row)
        edited["messages"][1]["content"] = broken_of(record)
        findings = views_chat.chat_findings(record, edited)
        self.assertIn(cv.LEAK_COMPLETION_NOT_VERIFIED, findings)
        self.assertIn(cv.LEAK_COMPLETION_EQUALS_BROKEN, findings)


class Windows(unittest.TestCase):
    def test_the_window_is_the_changed_lines_when_unique(self):
        self.assertEqual(
            views_edit.search_replace("def f():\n    return 1\n", "def f():\n    return 2\n"),
            ("    return 1\n", "    return 2\n"),
        )

    def test_the_window_widens_until_the_search_text_is_unique(self):
        self.assertEqual(
            views_edit.search_replace("x = 1\ny = 1\nx = 1\n", "x = 1\ny = 1\nx = 2\n"),
            ("y = 1\nx = 1\n", "y = 1\nx = 2\n"),
        )
        self.assertEqual(views_edit.search_replace("x = 1\ny\nx = 1\nz\n", "x = 2\ny\nx = 1\nz\n"),
                         ("x = 1\ny\n", "x = 2\ny\n"))

    def test_a_deleted_or_inserted_line_keeps_both_sides_nonempty(self):
        search, replace = views_edit.search_replace("a\nb\nc\n", "a\nc\n")
        self.assertTrue(search and replace)
        self.assertEqual("a\nb\nc\n".replace(search, replace, 1), "a\nc\n")
        search, replace = views_edit.search_replace("a\nc\n", "a\nb\nc\n")
        self.assertTrue(search and replace)
        self.assertEqual("a\nc\n".replace(search, replace, 1), "a\nb\nc\n")

    def test_overlapping_repeats_never_read_as_unique(self):
        self.assertEqual(views_edit.occurrences("a\na\na\n", "a\na\n"), 2)
        self.assertEqual("a\na\na\n".count("a\na\n"), 1)
        broken, repaired = "a\na\na\n", "a\na\nb\n"
        search, replace = views_edit.search_replace(broken, repaired)
        self.assertEqual((search, replace), (broken, repaired))
        applied, code = views_edit.apply_block(broken, views_edit.render_block(search, replace))
        self.assertEqual((applied, code), (repaired, None))
        ambiguous = views_edit.render_block("a\na\n", "a\nb\n")
        self.assertEqual(views_edit.apply_block(broken, ambiguous),
                         (None, cv.LEAK_EDIT_SEARCH_NOT_UNIQUE))

    def test_identical_texts_are_refused(self):
        with refusal(self, cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE):
            views_edit.search_replace("a\n", "a\n")

    def test_parse_block_round_trips_and_rejects_markers_inside_content(self):
        block = views_edit.render_block("s\n", "r\n")
        self.assertEqual(views_edit.parse_block(block), ("s\n", "r\n"))
        divider_inside = views_edit.render_block(cv.EDIT_DIVIDER + "\n", "r\n")
        marker_inside = views_edit.render_block("s\n", cv.EDIT_SEARCH_MARKER + "\n")
        self.assertIsNone(views_edit.parse_block(divider_inside))
        self.assertIsNone(views_edit.parse_block(marker_inside))
        self.assertIsNone(views_edit.parse_block(views_edit.render_block("s", "r\n")))
        self.assertIsNone(views_edit.parse_block(block + "\n"))


if __name__ == "__main__":
    unittest.main()
