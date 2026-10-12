"""The offline recall probe: leak-free prompts, static scoring, coded refusals, exit codes."""

import ast
import contextlib
import copy
import hashlib
import inspect
import io
import json
import shutil
import sys
import tempfile
import tokenize
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent / "pipelines"))

from code_repair import lineage
from code_repair import recall_probe as probe
from code_repair._contract import load_strict_json
from code_repair_test_support import (
    catalog,
    cli,
    generate,
    oc,
    refusal,
    smoke_run,
    views,
)
from code_repair_test_support import vocabulary as cv

NO_EVIDENCE, DOCSTRING_ONLY = cv.RECALL_VARIANT_NO_EVIDENCE, cv.RECALL_VARIANT_DOCSTRING_ONLY
PLACEHOLDER_LINE = "    ...\n"
DECORATED = (
    "import functools\n\n@functools.cache\ndef f(\n    x,\n):\n  '''doc\n\n  more'''\n"
    "  return x  # tail\n"
)
AFTER_A_HELPER = (
    "def g():\n    'other'\n    return 1\n\n\ndef f():\n    '''doc'''  # note\n"
    "    return g()\n"
)


def positives():
    _summary, records, _run_dir = smoke_run()
    return [r for r in records if views.is_positive(r)]


def broken_of(record):
    return record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]


def function_of(record):
    return record["scenario"]["source"]["upstream"]["function"]


def shown_code(prompt):
    return prompt.split("```python\n", 1)[1].split("```", 1)[0]


def rename_identifiers(text, names):
    """Every NAME token in ``names`` renamed consistently; strings and comments untouched."""

    lines = text.split("\n")
    edits = [
        (token.start, token.end, f"renamed_{token.string}")
        for token in tokenize.generate_tokens(io.StringIO(text).readline)
        if token.type == tokenize.NAME and token.string in names
    ]
    for (row, start), (_row, end), replacement in reversed(edits):
        lines[row - 1] = lines[row - 1][:start] + replacement + lines[row - 1][end:]
    return "\n".join(lines)


def renamed_repair(record):
    """The repaired module with its function and parameters renamed: same structure, new text."""

    repaired = views.completion_of(record)
    node = catalog.function_node(repaired, function_of(record))
    renamed = rename_identifiers(repaired, {node.name, *(arg.arg for arg in node.args.args)})
    assert renamed != repaired
    assert lineage.structure_digest(renamed) == lineage.structure_digest(repaired)
    return renamed


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def write_lines(path, lines):
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


def completion_lines(rows):
    return [json.dumps({"id": r["id"], "variant": v, "completion": c}) for r, v, c in rows]


class Prompts(unittest.TestCase):
    def test_two_variants_per_positive_rendered_from_the_public_reads(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                rows = probe.prompt_rows(record)
                self.assertEqual([row["variant"] for row in rows], list(cv.RECALL_VARIANTS))
                split_lineage = record["provenance"]["split_lineage"]
                for row in rows:
                    self.assertEqual(set(row), probe.PROMPT_KEYS)
                    self.assertEqual(probe.prompt_findings(record, row), [])
                    identity = (row["id"], row["lineage_id"], row["group_id"], row["split"],
                                row["family"])
                    self.assertEqual(identity, (
                        record["id"], split_lineage["lineage_id"], split_lineage["group_id"],
                        split_lineage["split"], record["scenario"]["source"]["family"],
                    ))
                no_evidence, docstring_only = (row["prompt"] for row in rows)
                self.assertTrue(no_evidence.startswith(cv.TASK_SPECIFICATION))
                self.assertTrue(no_evidence.endswith(cv.PROMPT_INSTRUCTIONS + "\n"))
                self.assertIn(f"```python\n{broken_of(record)}```", no_evidence)
                self.assertNotIn("### Failing doctest examples", no_evidence)
                self.assertNotIn("Failed example:", no_evidence)
                self.assertTrue(docstring_only.startswith(cv.DOCSTRING_ONLY_TASK))
                self.assertTrue(docstring_only.endswith(cv.DOCSTRING_ONLY_INSTRUCTIONS + "\n"))

    def test_no_evidence_is_the_sft_prompt_minus_its_evidence_section(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                view = views.public_view(record)
                sft = views.render_prompt(view)
                section = f"### Failing doctest examples\n{view.evidence_text}\n\n"
                self.assertIn(section, sft)
                self.assertEqual(probe.prompt_rows(record)[0]["prompt"], sft.replace(section, ""))

    def test_docstring_only_shows_the_header_and_docstring_and_elides_the_body(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                broken, function = broken_of(record), function_of(record)
                node = catalog.function_node(broken, function)
                lines = broken.split("\n")
                header = lines[node.lineno - 1:node.body[0].end_lineno]
                body = [line for line in lines[node.body[0].end_lineno:node.end_lineno]
                        if line.strip() and line not in header]
                stub = probe.docstring_stub(broken, function)
                self.assertEqual(stub, "\n".join(header) + "\n" + PLACEHOLDER_LINE)
                prompt = probe.prompt_rows(record)[1]["prompt"]
                self.assertEqual(shown_code(prompt), stub)
                self.assertTrue(body)
                for line in body:
                    self.assertNotIn(line, prompt)
                for example in record["scenario"]["public_tests"]["examples"]:
                    self.assertIn(example["source"].rstrip("\n"), prompt)
                stub_node = catalog.function_node(stub, function)  # the stub is a module
                self.assertEqual(ast.get_docstring(stub_node), ast.get_docstring(node))

    def test_no_variant_contains_the_repair_or_the_restored_span(self):
        for record in positives():
            with self.subTest(record=record["id"]):
                completion, broken = views.completion_of(record), broken_of(record)
                site = record["intervention"]["site"]
                start, replacement = site["start_byte"], site["replacement_text"].encode()
                self.assertNotEqual(site["replacement_text"], site["original_text"])
                for row in probe.prompt_rows(record):
                    self.assertNotIn(completion, row["prompt"])
                    shown = shown_code(row["prompt"])
                    if row["variant"] == NO_EVIDENCE:
                        self.assertEqual(shown, broken)
                        self.assertEqual(shown.encode()[start:start + len(replacement)],
                                         replacement)
                        continue
                    header = shown.removesuffix(PLACEHOLDER_LINE).encode()
                    offset = broken.encode().index(header)
                    self.assertLessEqual(offset + len(header), start)  # the site is elided

    def test_the_view_reads_three_public_fields_and_private_fields_cannot_reach_a_prompt(self):
        record = positives()[0]
        self.assertEqual(set(probe.ProbeView.__dataclass_fields__),
                         {"task_specification", "program_text", "function"})
        expected = [row["prompt"] for row in probe.prompt_rows(record)]
        tampered = copy.deepcopy(record)
        tampered["intervention"]["site"]["original_text"] = "SENTINEL"
        tampered["candidate_prediction"]["predicted_repair"]["files"]["program.py"] = "SENTINEL\n"
        tampered["result"]["public_failure_evidence"] = [{"got": "SENTINEL"}]
        tampered["oracle"]["configuration"]["hidden_check"] = {"cases": ["SENTINEL"]}
        view = probe.probe_view(tampered)
        rendered = [probe.render_no_evidence(view), probe.render_docstring_only(view)]
        self.assertEqual(rendered, expected)
        self.assertNotIn("SENTINEL", "".join(rendered))


class Stub(unittest.TestCase):
    def test_the_stub_keeps_decorators_and_the_body_indentation(self):
        cases = (
            ("def f(x):\n    '''doc'''\n    return x\n", "def f(x):\n    '''doc'''\n    ...\n"),
            ("def f(x):\n\t'''doc'''\n\treturn x\n", "def f(x):\n\t'''doc'''\n\t...\n"),
            (DECORATED, "@functools.cache\ndef f(\n    x,\n):\n  '''doc\n\n  more'''\n  ...\n"),
            (AFTER_A_HELPER, "def f():\n    '''doc'''  # note\n    ...\n"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(probe.docstring_stub(text, "f"), expected)

    def test_a_target_without_a_clean_header_is_not_renderable(self):
        cases = (
            ("def f():\n    return 1\n", "no docstring"),
            ("x = 1\n", "not a parseable module-level def"),
            ("def (\n", "not a parseable module-level def"),
            ("class C:\n    def f(self):\n        'doc'\n        return 1\n",
             "not a parseable module-level def"),
            ("def f():\n    'doc'\n", "no body after its docstring"),
            ("def f(): 'doc'; return 1\n", "on a line of its own"),
            ("def f():\n    'doc'; return 1\n", "on a line of its own"),
        )
        for text, fragment in cases:
            with (self.subTest(text=text),
                  refusal(self, cv.FINDING_RECALL_TARGET_NOT_RENDERABLE, fragment)):
                probe.docstring_stub(text, "f")


class LeakCheck(unittest.TestCase):
    def setUp(self):
        self.record = positives()[0]
        self.rows = probe.prompt_rows(self.record)
        self.completion = views.completion_of(self.record)

    def test_every_leak_code_has_a_named_tamper(self):
        for row in self.rows:
            hint = f"### Hint\n```python\n{self.completion}```\n\n### Instructions"
            leaky = {**row, "prompt": row["prompt"].replace("### Instructions", hint)}
            found = probe.prompt_findings(self.record, leaky)
            self.assertIn(cv.LEAK_PROMPT_CONTAINS_REPAIR, found)
            self.assertIn(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW, found)
            edited = {**row, "prompt": row["prompt"].replace("```python\n", "```python\n# x\n", 1)}
            self.assertIn(cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT,
                          probe.prompt_findings(self.record, edited))
        extra = probe.prompt_findings(self.record, {**self.rows[0], "thought": "x"})
        self.assertIn(cv.LEAK_VIEW_EXTRA_KEYS, extra)
        self.assertIn(cv.LEAK_HIDDEN_REASONING_KEY, extra)
        for variant in ("with_hints", ["no_evidence"], None):
            with self.subTest(variant=variant):
                unknown = probe.prompt_findings(self.record, {**self.rows[0], "variant": variant})
                self.assertEqual(unknown, [cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
                                           cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT])
        self.assertIn(cv.LEAK_PROMPT_CONTAINS_REPAIR, cv.LEAK_CODE_SET)
        self.assertFalse(cv.RECALL_CODE_SET & (cv.FINDING_CODE_SET | cv.LEAK_CODE_SET))

    def test_a_mutated_span_inside_the_shown_code_is_a_leak(self):
        broken = broken_of(self.record).encode()
        tampered = copy.deepcopy(self.record)
        site = tampered["intervention"]["site"]
        site["start_byte"] = broken.index(f"def {function_of(self.record)}(".encode()) + 4
        for row in self.rows:
            with self.subTest(variant=row["variant"]):
                self.assertEqual(probe.prompt_findings(self.record, row), [])
                self.assertEqual(probe.prompt_findings(tampered, row),
                                 [cv.LEAK_PROMPT_CONTAINS_REPAIR])

    def test_a_rendering_that_would_carry_the_repair_is_refused_before_anything_is_written(self):
        def leaky(view):
            return probe.NO_EVIDENCE_TEMPLATE.format(
                task=view.task_specification, program=self.completion,
                instructions=cv.PROMPT_INSTRUCTIONS,
            )

        root = Path(tempfile.mkdtemp(prefix="code-repair-recall-"))
        self.addCleanup(shutil.rmtree, root, True)
        _summary, _records, run_dir = smoke_run()
        with mock.patch.object(probe, "render_no_evidence", leaky):
            with refusal(self, cv.FINDING_RECALL_PROMPT_LEAK, cv.LEAK_PROMPT_CONTAINS_REPAIR):
                probe.prompt_rows(self.record)
            with refusal(self, cv.FINDING_RECALL_PROMPT_LEAK,
                         cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT):
                probe.emit(probe.EmitRequest(run_dir, root / "probe"))
        self.assertFalse((root / "probe").exists())

    def test_non_positive_records_are_refused(self):
        _summary, records, _run_dir = smoke_run()
        rejected = next(r for r in records if not views.is_positive(r))
        with refusal(self, cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE):
            probe.prompt_rows(rejected)


class ProbeTree(unittest.TestCase):
    """A temporary root holding the emitted prompts of the smoke run."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-recall-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        _summary, _records, self.run_dir = smoke_run()
        self.prompts = self.root / "probe" / probe.PROMPTS_FILENAME
        probe.emit(probe.EmitRequest(self.run_dir, self.root / "probe"))

    def score(self, completions, prompts=None, out="report.json"):
        return probe.score(probe.ScoreRequest(prompts or self.prompts, completions, self.run_dir,
                                              self.root / out))

    def completions(self, rows, name="completions.jsonl"):
        return write_lines(self.root / name, completion_lines(rows))


class Scoring(ProbeTree):
    def test_emission_is_deterministic_and_covers_every_positive_twice(self):
        probe.emit(probe.EmitRequest(self.run_dir, self.root / "again"))
        again = (self.root / "again" / probe.PROMPTS_FILENAME).read_bytes()
        self.assertEqual(self.prompts.read_bytes(), again)
        rows = [row for _lineno, row in oc.read_jsonl(self.prompts)]
        self.assertEqual(len(rows), 2 * len(positives()))
        self.assertEqual([row["id"] for row in rows[::2]], [r["id"] for r in positives()])

    def test_synthetic_completions_score_as_expected(self):
        first, second, third = positives()[:3]
        report = self.score(self.completions([
            (first, NO_EVIDENCE, views.completion_of(first)),
            (first, DOCSTRING_ONLY, views.completion_of(first)),
            (second, NO_EVIDENCE, renamed_repair(second)),
            (second, DOCSTRING_ONLY, broken_of(second)),
            (third, NO_EVIDENCE, "def (\n"),
        ]))
        count = len(positives())
        self.assertEqual(report["per_variant"][NO_EVIDENCE], {
            "prompts": count, "completions": 3, "missing": count - 3, "exact": 1,
            "structural": 2, "unparsable": 1, "exact_rate": 0.3333, "structural_rate": 0.6667,
        })
        self.assertEqual(report["per_variant"][DOCSTRING_ONLY], {
            "prompts": count, "completions": 2, "missing": count - 2, "exact": 1,
            "structural": 1, "unparsable": 0, "exact_rate": 0.5, "structural_rate": 0.5,
        })
        self.assertEqual(report["docstring_only_exact_recall_ids"], [first["id"]])
        family = first["scenario"]["source"]["family"]
        self.assertEqual(report["findings"], [{
            "code": cv.RECALL_EXACT_UNDER_DOCSTRING_ONLY, "record_id": first["id"],
            "family": family,
        }])
        self.assertEqual(report["status"], "findings")
        self.assertEqual(report["per_family"][family][DOCSTRING_ONLY]["exact"], 1)
        for variant in cv.RECALL_VARIANTS:
            for key in ("prompts", "completions", "exact", "structural", "unparsable"):
                total = sum(b[variant][key] for b in report["per_family"].values() if variant in b)
                self.assertEqual(total, report["per_variant"][variant][key], (variant, key))
        completions = (self.root / "completions.jsonl").read_bytes()
        self.assertEqual(report["inputs"]["completions"]["rows"], 5)
        self.assertEqual(report["inputs"]["completions"]["sha256"],
                         hashlib.sha256(completions).hexdigest())
        self.assertEqual(report["inputs"]["prompts"]["rows"], 2 * count)
        self.assertEqual(report["run"]["positives"], count)
        written = load_strict_json((self.root / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(written, report)
        self.assertEqual(report["limitation"], cv.LIMITATION_POSSIBLE_UPSTREAM_CODE_RECALL)

    def test_a_probe_with_no_exact_docstring_recall_reports_ok(self):
        report = self.score(self.completions([
            (record, variant, broken_of(record))
            for record in positives() for variant in cv.RECALL_VARIANTS
        ]))
        self.assertEqual((report["status"], report["findings"]), ("ok", []))
        for variant in cv.RECALL_VARIANTS:
            bucket = report["per_variant"][variant]
            self.assertEqual((bucket["exact"], bucket["structural"], bucket["missing"]), (0, 0, 0))

    def test_scoring_is_static_and_never_runs_a_completion(self):
        record = positives()[0]
        repaired = views.completion_of(record)
        target = (record["result"]["repaired_sha256"], lineage.structure_digest(repaired))
        sentinel = self.root / "executed"
        hostile = f"import pathlib\npathlib.Path({str(sentinel)!r}).write_text('x')\n"
        cases = (
            (repaired, (True, True, False)),
            (renamed_repair(record), (False, True, False)),
            (repaired + "# trailing comment\n", (False, True, False)),
            (f"```python\n{repaired}```\n", (False, False, True)),
            (broken_of(record), (False, False, False)),
            ("def (\n", (False, False, True)),
            ("", (False, False, False)),
            (hostile, (False, False, False)),
        )
        for completion, expected in cases:
            with self.subTest(completion=completion[:24]):
                verdict = probe.score_completion(completion, *target)
                self.assertEqual(
                    (verdict["exact"], verdict["structural"], verdict["unparsable"]), expected
                )
        self.assertFalse(sentinel.exists())


class Refusals(ProbeTree):
    def setUp(self):
        super().setUp()
        self.record = positives()[0]

    def row(self, record_id=None, variant=NO_EVIDENCE, completion="x = 1\n"):
        return json.dumps({"id": record_id or self.record["id"], "variant": variant,
                           "completion": completion})

    def test_completion_rows_are_refused_per_line_with_a_code(self):
        cases = (
            (cv.FINDING_RECALL_COMPLETION_UNKNOWN, [self.row(record_id="pfr-0-99999")]),
            (cv.FINDING_RECALL_COMPLETION_UNKNOWN, [self.row(variant="with_hints")]),
            (cv.FINDING_RECALL_COMPLETION_DUPLICATE, [self.row(), self.row(completion="y\n")]),
            (cv.FINDING_RECALL_COMPLETION_MALFORMED, ["not json"]),
            (cv.FINDING_RECALL_COMPLETION_MALFORMED, ["[1, 2]"]),
            (cv.FINDING_RECALL_COMPLETION_MALFORMED, [json.dumps({"id": self.record["id"]})]),
            (cv.FINDING_RECALL_COMPLETION_MALFORMED, [self.row()[:-1] + ', "note": "x"}']),
            (cv.FINDING_RECALL_COMPLETION_MALFORMED,
             [json.dumps({"id": self.record["id"], "variant": NO_EVIDENCE, "completion": 1})]),
            (cv.FINDING_RECALL_COMPLETION_MALFORMED,
             [json.dumps({"id": [self.record["id"]], "variant": NO_EVIDENCE, "completion": ""})]),
            (cv.FINDING_RECALL_INPUT_MISSING, []),
        )
        for code, lines in cases:
            with self.subTest(code=code, lines=lines), refusal(self, code):
                self.score(write_lines(self.root / "completions.jsonl", lines))
        with refusal(self, cv.FINDING_RECALL_INPUT_MISSING):
            self.score(self.root / "nowhere.jsonl")
        self.assertFalse((self.root / "report.json").exists())

    def test_prompts_must_re_render_from_the_run_byte_for_byte(self):
        rows = [row for _lineno, row in oc.read_jsonl(self.prompts)]
        edited = [{**row, "prompt": row["prompt"] + "# hint\n"} if i == 1 else row
                  for i, row in enumerate(rows)]
        foreign = [{**row, "id": "pfr-0-99999"} if i == 0 else row for i, row in enumerate(rows)]
        unhashable = [{**row, "id": [row["id"]]} if i == 0 else row for i, row in enumerate(rows)]
        cases = {
            "edited": edited, "foreign": foreign, "unhashable": unhashable, "dropped": rows[1:],
            "repeated": rows + rows[:1], "malformed": ["not json"],
        }
        completions = write_lines(self.root / "completions.jsonl", [self.row()])
        for name, lines in cases.items():
            payload = [line if isinstance(line, str) else oc.canonical_json(line) for line in lines]
            with self.subTest(name=name), refusal(self, cv.FINDING_RECALL_PROMPTS_MALFORMED):
                self.score(completions, prompts=write_lines(self.root / f"{name}.jsonl", payload))
        with refusal(self, cv.FINDING_RECALL_INPUT_MISSING):
            self.score(completions, prompts=self.root / "nowhere.jsonl")
        self.assertFalse((self.root / "report.json").exists())

    def test_destinations_must_be_new_and_outside_the_raw_tree(self):
        completions = write_lines(self.root / "completions.jsonl", [self.row()])
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            probe.emit(probe.EmitRequest(self.run_dir, self.root / "probe"))
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            self.score(completions, out="completions.jsonl")
        raw = self.root / "elsewhere" / "outputs" / "raw"
        raw.mkdir(parents=True)
        alias = self.root / "alias"
        alias.symlink_to(raw, target_is_directory=True)
        for destination in (raw / "x", alias / "x"):
            with self.subTest(destination=destination):
                with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
                    probe.emit(probe.EmitRequest(self.run_dir, destination))
                with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
                    probe.score(probe.ScoreRequest(self.prompts, completions, self.run_dir,
                                                   destination / "report.json"))
        self.assertEqual(list(raw.iterdir()), [])

    def test_runs_must_exist_and_carry_a_positive_record(self):
        completions = write_lines(self.root / "completions.jsonl", [self.row()])
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            probe.emit(probe.EmitRequest(self.root / "nowhere", self.root / "out"))
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            probe.score(probe.ScoreRequest(self.prompts, completions, self.root / "nowhere",
                                           self.root / "out.json"))
        negatives = self.root / "negatives"
        _summary, records, _run_dir = smoke_run()
        oc.write_jsonl(negatives / generate.CANDIDATES_FILENAME,
                       [r for r in records if not views.is_positive(r)])
        with refusal(self, cv.FINDING_RECALL_NO_POSITIVE_RECORDS):
            probe.emit(probe.EmitRequest(negatives, self.root / "out"))
        self.assertFalse((self.root / "out").exists())
        self.assertFalse((self.root / "out.json").exists())


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-recall-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        _summary, _records, self.run_dir = smoke_run()

    def completions(self, name, rows):
        return write_lines(self.root / name, completion_lines(rows))

    def test_exit_codes_and_json_shapes(self):
        out = self.root / "probe"
        code, text, err = invoke(["recall-probe", "emit", "--run", str(self.run_dir),
                                  "--out", str(out), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(text)
        self.assertEqual((payload["command"], payload["status"]), ("recall-probe emit", "ok"))
        self.assertEqual(payload["summary"]["prompts"]["rows"], 2 * len(positives()))
        code, _text, err = invoke(["recall-probe", "emit", "--run", str(self.run_dir),
                                   "--out", str(out)])
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_DESTINATION_EXISTS), err)

        prompts = out / probe.PROMPTS_FILENAME
        record = positives()[0]
        recalled = self.completions("recalled.jsonl",
                                    [(record, DOCSTRING_ONLY, views.completion_of(record))])
        code, text, err = invoke([
            "recall-probe", "score", "--prompts", str(prompts), "--completions", str(recalled),
            "--run", str(self.run_dir), "--out", str(self.root / "recalled.json"), "--json",
        ])
        self.assertEqual((code, err), (1, ""))
        payload = json.loads(text)
        self.assertEqual((payload["command"], payload["status"]),
                         ("recall-probe score", "findings"))
        self.assertEqual([f["code"] for f in payload["findings"]],
                         [cv.RECALL_EXACT_UNDER_DOCSTRING_ONLY])
        self.assertEqual(payload["report"]["docstring_only_exact_recall_ids"], [record["id"]])

        clean = self.completions("clean.jsonl", [(record, NO_EVIDENCE, broken_of(record))])
        code, text, err = invoke([
            "recall-probe", "score", "--prompts", str(prompts), "--completions", str(clean),
            "--run", str(self.run_dir), "--out", str(self.root / "clean.json"),
        ])
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(text.startswith("recall probe ok: "), text)
        self.assertIn("nothing was executed", text)

        unknown = self.completions("unknown.jsonl", [({"id": "pfr-0-99999"}, NO_EVIDENCE, "x\n")])
        code, text, err = invoke([
            "recall-probe", "score", "--prompts", str(prompts), "--completions", str(unknown),
            "--run", str(self.run_dir), "--out", str(self.root / "unknown.json"), "--json",
        ])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(text)
        self.assertEqual((payload["status"], payload["code"], payload["command"]),
                         ("refused", cv.FINDING_RECALL_COMPLETION_UNKNOWN, "recall-probe"))
        self.assertFalse((self.root / "unknown.json").exists())

    def test_a_raw_destination_is_a_coded_refusal_at_the_command_line(self):
        raw = self.root / "outputs" / "raw" / "probe"
        code, text, _err = invoke(["recall-probe", "emit", "--run", str(self.run_dir),
                                   "--out", str(raw), "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(text)["code"], cv.FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())


class NeverExecutes(unittest.TestCase):
    def test_the_module_only_hashes_and_parses(self):
        tree = ast.parse(inspect.getsource(probe))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
        } | {
            node.module.split(".")[0] for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0
        }
        self.assertFalse(imported & {"subprocess", "importlib", "runpy", "os", "sys", "code"})
        relative = {
            alias.name for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module is None
            for alias in node.names
        }
        self.assertFalse(relative & {"executor", "sandbox", "_harness", "verify", "replay"})
        called = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertFalse(called & {"exec", "eval", "compile", "__import__"})
        self.assertEqual(
            probe.score_completion("x = 1\n", hashlib.sha256(b"x = 1\n").hexdigest(),
                               lineage.structure_digest("y = 1\n")),
            {"exact": True, "structural": True, "unparsable": False},
        )


if __name__ == "__main__":
    unittest.main()
