"""The recall probe's prompts: public reads only, the stub cut, and a named tamper per leak."""

import ast
import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent / "pipelines"))

from code_repair import recall_probe, recall_prompts, recall_stub
from code_repair_recall_test_support import (
    NO_EVIDENCE,
    PLACEHOLDER_LINE,
    broken_of,
    function_of,
    positives,
    rejected,
    shown_code,
)
from code_repair_test_support import catalog, refusal, smoke_run, views
from code_repair_test_support import vocabulary as cv

DECORATED = (
    "import functools\n\n@functools.cache\ndef f(\n    x,\n):\n  '''doc\n\n  more'''\n"
    "  return x  # tail\n"
)
AFTER_A_HELPER = (
    "def g():\n    'other'\n    return 1\n\n\ndef f():\n    '''doc'''  # note\n"
    "    return g()\n"
)
NON_ASCII = "# é\ndef f(x='é'):\n    '''dé'''\n    return x\n"
CUT_CASES = (
    ("def f(x):\n    '''doc'''\n    return x\n", "def f(x):\n    '''doc'''\n    ...\n"),
    ("def f(x):\n\t'''doc'''\n\treturn x\n", "def f(x):\n\t'''doc'''\n\t...\n"),
    (DECORATED, "@functools.cache\ndef f(\n    x,\n):\n  '''doc\n\n  more'''\n  ...\n"),
    (AFTER_A_HELPER, "def f():\n    '''doc'''  # note\n    ...\n"),
    (NON_ASCII, "def f(x='é'):\n    '''dé'''\n    ...\n"),
)
UNRENDERABLE = (
    ("def f():\n    return 1\n", "no docstring"),
    ("x = 1\n", "not a parseable module-level def"),
    ("def (\n", "not a parseable module-level def"),
    ("class C:\n    def f(self):\n        'doc'\n        return 1\n",
     "not a parseable module-level def"),
    ("def f():\n    'doc'\n", "no body after its docstring"),
    ("def f(): 'doc'; return 1\n", "on a line of its own"),
    ("def f(é=1): 'doc'; return é\n", "on a line of its own"),
    ("def f():\n    'doc'; return 1\n", "on a line of its own"),
)


def identity_of(record):
    split_lineage = record["provenance"]["split_lineage"]
    return {
        "id": record["id"], "lineage_id": split_lineage["lineage_id"],
        "group_id": split_lineage["group_id"], "split": split_lineage["split"],
        "family": record["scenario"]["source"]["family"],
    }


def body_lines(broken, node):
    """The target's non-blank lines after its docstring."""

    lines = broken.split("\n")
    header = lines[node.lineno - 1:node.body[0].end_lineno]
    after = lines[node.body[0].end_lineno:node.end_lineno]
    return [line for line in after if line.strip() and line not in header]


class Prompts(unittest.TestCase):
    def assert_rows(self, record):
        rows = recall_prompts.prompt_rows(record)
        self.assertEqual([row["variant"] for row in rows], list(cv.RECALL_VARIANTS))
        for row in rows:
            self.assertEqual(set(row), recall_prompts.PROMPT_KEYS)
            self.assertEqual(recall_prompts.prompt_findings(record, row), [])
            self.assertEqual({key: row[key] for key in identity_of(record)}, identity_of(record))
        no_evidence, docstring_only = (row["prompt"] for row in rows)
        self.assertTrue(no_evidence.startswith(cv.TASK_SPECIFICATION))
        self.assertTrue(no_evidence.endswith(cv.PROMPT_INSTRUCTIONS + "\n"))
        self.assertNotIn("Failed example:", no_evidence)
        self.assertTrue(docstring_only.startswith(cv.DOCSTRING_ONLY_TASK))
        self.assertTrue(docstring_only.endswith(cv.DOCSTRING_ONLY_INSTRUCTIONS + "\n"))

    def test_two_variants_per_positive_rendered_from_the_public_reads(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                self.assert_rows(record)

    def test_no_evidence_is_the_sft_prompt_minus_its_evidence_section(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                view = views.public_view(record)
                section = f"### Failing doctest examples\n{view.evidence_text}\n\n"
                sft = views.render_prompt(view)
                self.assertIn(section, sft)
                prompt = recall_prompts.prompt_rows(record)[0]["prompt"]
                self.assertEqual(prompt, sft.replace(section, ""))

    def assert_docstring_only(self, record):
        broken, function = broken_of(record), function_of(record)
        node = catalog.function_node(broken, function)
        stub = recall_stub.docstring_stub(broken, function)
        prompt = recall_prompts.prompt_rows(record)[1]["prompt"]
        self.assertEqual(shown_code(prompt), stub)
        self.assertTrue(stub.endswith(PLACEHOLDER_LINE))
        body = body_lines(broken, node)
        self.assertTrue(body)
        self.assertFalse([line for line in body if line in prompt])
        for example in record["scenario"]["public_tests"]["examples"]:
            self.assertIn(example["source"].rstrip("\n"), prompt)
        stub_node = catalog.function_node(stub, function)  # the stub is a module
        self.assertEqual(ast.get_docstring(stub_node), ast.get_docstring(node))

    def test_docstring_only_shows_the_header_and_docstring_and_elides_the_body(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                self.assert_docstring_only(record)

    def assert_span_hidden(self, record, row):
        broken = broken_of(record).encode()
        site = record["intervention"]["site"]
        start, replacement = site["start_byte"], site["replacement_text"].encode()
        shown = shown_code(row["prompt"]).encode()
        if row["variant"] == NO_EVIDENCE:
            self.assertEqual(shown, broken)
            self.assertEqual(shown[start:start + len(replacement)], replacement)
            return
        header = shown.removesuffix(PLACEHOLDER_LINE.encode())
        self.assertLessEqual(broken.index(header) + len(header), start)  # the site is elided

    def test_no_variant_contains_the_repair_or_the_restored_span(self):
        for record in positives():
            site = record["intervention"]["site"]
            self.assertNotEqual(site["replacement_text"], site["original_text"])
            for row in recall_prompts.prompt_rows(record):
                with self.subTest(record=record["id"], variant=row["variant"]):
                    self.assertNotIn(views.completion_of(record), row["prompt"])
                    self.assert_span_hidden(record, row)

    def test_the_view_reads_three_public_fields_and_private_fields_cannot_reach_a_prompt(self):
        record = positives()[0]
        self.assertEqual(set(recall_prompts.ProbeView.__dataclass_fields__),
                         {"task_specification", "program_text", "function"})
        expected = [row["prompt"] for row in recall_prompts.prompt_rows(record)]
        tampered = copy.deepcopy(record)
        tampered["intervention"]["site"]["original_text"] = "SENTINEL"
        tampered["candidate_prediction"]["predicted_repair"]["files"]["program.py"] = "SENTINEL\n"
        tampered["result"]["public_failure_evidence"] = [{"got": "SENTINEL"}]
        tampered["oracle"]["configuration"]["hidden_check"] = {"cases": ["SENTINEL"]}
        view = recall_prompts.probe_view(tampered)
        rendered = [recall_prompts.render_no_evidence(view),
                    recall_prompts.render_docstring_only(view)]
        self.assertEqual(rendered, expected)
        self.assertNotIn("SENTINEL", "".join(rendered))


class Stub(unittest.TestCase):
    def test_the_stub_keeps_decorators_and_the_body_indentation(self):
        for text, expected in CUT_CASES:
            with self.subTest(text=text):
                self.assertEqual(recall_stub.docstring_stub(text, "f"), expected)

    def test_header_offsets_are_utf8_byte_offsets(self):
        cut = recall_stub.header(NON_ASCII, "f")
        self.assertEqual(cut.start_byte, len("# é\n".encode()))
        self.assertEqual(NON_ASCII.encode()[cut.start_byte:cut.end_byte].decode(), cut.text)
        self.assertEqual(cut.indent, "    ")

    def test_a_target_without_a_clean_header_is_not_renderable(self):
        for text, fragment in UNRENDERABLE:
            with (self.subTest(text=text),
                  refusal(self, cv.FINDING_RECALL_TARGET_NOT_RENDERABLE, fragment)):
                recall_stub.docstring_stub(text, "f")


class LeakCheck(unittest.TestCase):
    def setUp(self):
        self.record = positives()[0]
        self.rows = recall_prompts.prompt_rows(self.record)
        self.completion = views.completion_of(self.record)

    def findings(self, row, **changes):
        return recall_prompts.prompt_findings(self.record, {**row, **changes})

    def test_a_prompt_carrying_the_repair_or_other_code_is_a_leak(self):
        hint = f"### Hint\n```python\n{self.completion}```\n\n### Instructions"
        for row in self.rows:
            with self.subTest(variant=row["variant"]):
                leaky = self.findings(row, prompt=row["prompt"].replace("### Instructions", hint))
                self.assertEqual(leaky, [cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
                                         cv.LEAK_PROMPT_CONTAINS_REPAIR])
                edited = row["prompt"].replace("```python\n", "```python\n# x\n", 1)
                self.assertEqual(self.findings(row, prompt=edited),
                                 [cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
                                  cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT])

    def test_extra_keys_hidden_reasoning_and_unknown_variants_are_leaks(self):
        self.assertEqual(self.findings(self.rows[0], thought="x"),
                         [cv.LEAK_VIEW_EXTRA_KEYS, cv.LEAK_HIDDEN_REASONING_KEY])
        for variant in ("with_hints", ["no_evidence"], None):
            with self.subTest(variant=variant):
                self.assertEqual(self.findings(self.rows[0], variant=variant),
                                 [cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
                                  cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT])
        self.assertIn(cv.LEAK_PROMPT_CONTAINS_REPAIR, cv.LEAK_CODE_SET)
        self.assertFalse(cv.RECALL_CODE_SET & (cv.FINDING_CODE_SET | cv.LEAK_CODE_SET))

    def test_a_mutated_span_inside_the_shown_code_is_a_leak(self):
        tampered = copy.deepcopy(self.record)
        definition = f"def {function_of(self.record)}(".encode()
        tampered["intervention"]["site"]["start_byte"] = broken_of(self.record).encode().index(
            definition) + 4
        for row in self.rows:
            with self.subTest(variant=row["variant"]):
                self.assertEqual(self.findings(row), [])
                self.assertEqual(recall_prompts.prompt_findings(tampered, row),
                                 [cv.LEAK_PROMPT_CONTAINS_REPAIR])

    def test_a_rendering_that_would_carry_the_repair_is_refused_before_anything_is_written(self):
        def leaky(view):
            return recall_prompts.NO_EVIDENCE_TEMPLATE.format(
                task=view.task_specification, program=self.completion,
                instructions=cv.PROMPT_INSTRUCTIONS,
            )

        root = Path(tempfile.mkdtemp(prefix="code-repair-recall-"))
        self.addCleanup(shutil.rmtree, root, True)
        _summary, _records, run_dir = smoke_run()
        with mock.patch.object(recall_prompts, "render_no_evidence", leaky):
            with refusal(self, cv.FINDING_RECALL_PROMPT_LEAK, cv.LEAK_PROMPT_CONTAINS_REPAIR):
                recall_prompts.prompt_rows(self.record)
            with refusal(self, cv.FINDING_RECALL_PROMPT_LEAK,
                         cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT):
                recall_probe.emit(recall_probe.EmitRequest(run_dir, root / "probe"))
        self.assertFalse((root / "probe").exists())

    def test_non_positive_records_are_refused(self):
        with refusal(self, cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE):
            recall_prompts.prompt_rows(rejected()[0])


if __name__ == "__main__":
    unittest.main()
