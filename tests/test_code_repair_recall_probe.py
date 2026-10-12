"""The offline recall probe: emission, static scoring, coded refusals, exit codes."""

import ast
import hashlib
import inspect
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS.parent / "pipelines"))

from code_repair import recall_probe, recall_prompts, recall_score, recall_stub
from code_repair._contract import load_strict_json
from code_repair_recall_test_support import (
    DOCSTRING_ONLY,
    NO_EVIDENCE,
    UNKNOWN_ID,
    ProbeTree,
    broken_of,
    completion_lines,
    invoke,
    positives,
    rejected,
    renamed_repair,
    structure_of,
    verdict,
    write_lines,
)
from code_repair_test_support import generate, oc, refusal, smoke_run, views
from code_repair_test_support import vocabulary as cv

PROBE_MODULES = (recall_probe, recall_prompts, recall_score, recall_stub)
FORBIDDEN_IMPORTS = frozenset({
    "subprocess", "importlib", "runpy", "os", "sys", "code",
    ".executor", ".sandbox", "._harness", "._sandbox", ".verify", ".replay",
})
FORBIDDEN_CALLS = frozenset({"exec", "eval", "compile", "__import__"})
COUNTED = ("prompts", "completions", "exact", "structural", "unparsable")


def _import_targets(node):
    """``root`` for ``import root.x``; ``module`` or ``.sibling`` for a from-import."""

    if isinstance(node, ast.Import):
        return {alias.name.split(".")[0] for alias in node.names}
    if not isinstance(node, ast.ImportFrom):
        return set()
    prefix = "." * node.level
    if node.module:
        return {prefix + node.module.split(".")[0]}
    return {prefix + alias.name for alias in node.names}


def import_targets(tree):
    found = set()
    for node in ast.walk(tree):
        found |= _import_targets(node)
    return found


def called_names(tree):
    calls = (node for node in ast.walk(tree) if isinstance(node, ast.Call))
    return {call.func.id for call in calls if isinstance(call.func, ast.Name)}


def family_total(report, variant, key):
    return sum(buckets[variant][key] for buckets in report["per_family"].values()
               if variant in buckets)


def tampered_prompts(rows):
    """Prompt files the run cannot re-render byte for byte, once each, all present."""

    first, second = rows[0], rows[1]
    return {
        "edited": [first, {**second, "prompt": second["prompt"] + "# hint\n"}, *rows[2:]],
        "foreign": [{**first, "id": UNKNOWN_ID}, *rows[1:]],
        "unhashable": [{**first, "id": [first["id"]]}, *rows[1:]],
        "dropped": rows[1:],
        "repeated": [*rows, first],
    }


class Scoring(ProbeTree, unittest.TestCase):
    def test_emission_is_deterministic_and_covers_every_positive_twice(self):
        recall_probe.emit(recall_probe.EmitRequest(self.run_dir, self.root / "again"))
        again = (self.root / "again" / recall_probe.PROMPTS_FILENAME).read_bytes()
        self.assertEqual(self.prompts.read_bytes(), again)
        rows = [row for _lineno, row in oc.read_jsonl(self.prompts)]
        self.assertEqual(len(rows), 2 * len(positives()))
        self.assertEqual([row["id"] for row in rows[::2]], [r["id"] for r in positives()])

    def score_mixed(self):
        first, second, third = positives()[:3]
        return self.score(self.completions([
            (first, NO_EVIDENCE, views.completion_of(first)),
            (first, DOCSTRING_ONLY, views.completion_of(first)),
            (second, NO_EVIDENCE, renamed_repair(second)),
            (second, DOCSTRING_ONLY, broken_of(second)),
            (third, NO_EVIDENCE, "def (\n"),
        ]))

    def test_synthetic_completions_score_as_expected(self):
        report, count, first = self.score_mixed(), len(positives()), positives()[0]
        self.assertEqual(report["per_variant"][NO_EVIDENCE], {
            "prompts": count, "completions": 3, "missing": count - 3, "exact": 1,
            "structural": 2, "unparsable": 1, "exact_rate": 0.3333, "structural_rate": 0.6667,
        })
        self.assertEqual(report["per_variant"][DOCSTRING_ONLY], {
            "prompts": count, "completions": 2, "missing": count - 2, "exact": 1,
            "structural": 1, "unparsable": 0, "exact_rate": 0.5, "structural_rate": 0.5,
        })
        family = first["scenario"]["source"]["family"]
        self.assertEqual(report["docstring_only_exact_recall_ids"], [first["id"]])
        self.assertEqual(report["findings"], [{
            "code": cv.RECALL_EXACT_UNDER_DOCSTRING_ONLY, "record_id": first["id"],
            "family": family,
        }])
        self.assertEqual(report["status"], "findings")
        self.assertEqual(report["per_family"][family][DOCSTRING_ONLY]["exact"], 1)

    def test_the_report_adds_up_and_is_written_as_returned(self):
        report = self.score_mixed()
        for variant in cv.RECALL_VARIANTS:
            for key in COUNTED:
                with self.subTest(variant=variant, key=key):
                    self.assertEqual(family_total(report, variant, key),
                                     report["per_variant"][variant][key])
        completions = (self.root / "completions.jsonl").read_bytes()
        self.assertEqual(report["inputs"]["completions"],
                         {"path": str(self.root / "completions.jsonl"), "rows": 5,
                          "sha256": hashlib.sha256(completions).hexdigest()})
        self.assertEqual(report["inputs"]["prompts"]["rows"], 2 * len(positives()))
        self.assertEqual(report["run"]["positives"], len(positives()))
        self.assertEqual(report["limitation"], cv.LIMITATION_POSSIBLE_UPSTREAM_CODE_RECALL)
        written = load_strict_json((self.root / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(written, report)

    def test_a_probe_with_no_exact_docstring_recall_reports_ok(self):
        report = self.score(self.completions([
            (record, variant, broken_of(record))
            for record in positives() for variant in cv.RECALL_VARIANTS
        ]))
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["findings"], [])
        for variant in cv.RECALL_VARIANTS:
            bucket = report["per_variant"][variant]
            self.assertEqual([bucket["exact"], bucket["structural"], bucket["missing"]],
                             [0, 0, 0])

    def test_scoring_is_static_and_never_runs_a_completion(self):
        record = positives()[0]
        repaired = views.completion_of(record)
        target = (record["result"]["repaired_sha256"], structure_of(repaired))
        sentinel = self.root / "executed"
        hostile = f"import pathlib\npathlib.Path({str(sentinel)!r}).write_text('x')\n"
        cases = (
            (repaired, verdict(True, True, False)),
            (renamed_repair(record), verdict(False, True, False)),
            (repaired + "# trailing comment\n", verdict(False, True, False)),
            (f"```python\n{repaired}```\n", verdict(False, False, True)),
            (broken_of(record), verdict(False, False, False)),
            ("def (\n", verdict(False, False, True)),
            ("", verdict(False, False, False)),
            (hostile, verdict(False, False, False)),
        )
        for completion, expected in cases:
            with self.subTest(completion=completion[:24]):
                self.assertEqual(recall_score.score_completion(completion, *target), expected)
        self.assertFalse(sentinel.exists())


class Refusals(ProbeTree, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.record = positives()[0]

    def row(self, record_id=None, variant=NO_EVIDENCE, completion="x = 1\n"):
        return json.dumps({"id": record_id or self.record["id"], "variant": variant,
                           "completion": completion})

    def completion_cases(self):
        malformed = cv.FINDING_RECALL_COMPLETION_MALFORMED
        return (
            (cv.FINDING_RECALL_COMPLETION_UNKNOWN, [self.row(record_id=UNKNOWN_ID)]),
            (cv.FINDING_RECALL_COMPLETION_UNKNOWN, [self.row(variant="with_hints")]),
            (cv.FINDING_RECALL_COMPLETION_DUPLICATE, [self.row(), self.row(completion="y\n")]),
            (malformed, ["not json"]),
            (malformed, ["[1, 2]"]),
            (malformed, [json.dumps({"id": self.record["id"]})]),
            (malformed, [self.row()[:-1] + ', "note": "x"}']),
            (malformed, [json.dumps({"id": self.record["id"], "variant": NO_EVIDENCE,
                                     "completion": 1})]),
            (malformed, [json.dumps({"id": [self.record["id"]], "variant": NO_EVIDENCE,
                                     "completion": ""})]),
            (cv.FINDING_RECALL_INPUT_MISSING, []),
        )

    def test_completion_rows_are_refused_per_line_with_a_code(self):
        for code, lines in self.completion_cases():
            with self.subTest(code=code, lines=lines), refusal(self, code):
                self.score(write_lines(self.root / "completions.jsonl", lines))
        with refusal(self, cv.FINDING_RECALL_INPUT_MISSING):
            self.score(self.root / "nowhere.jsonl")
        self.assertFalse((self.root / "report.json").exists())

    def test_prompts_must_re_render_from_the_run_byte_for_byte(self):
        rows = [row for _lineno, row in oc.read_jsonl(self.prompts)]
        completions = write_lines(self.root / "completions.jsonl", [self.row()])
        for name, tampered in tampered_prompts(rows).items():
            prompts = write_lines(self.root / f"{name}.jsonl", map(oc.canonical_json, tampered))
            with self.subTest(name=name), refusal(self, cv.FINDING_RECALL_PROMPTS_MALFORMED):
                self.score(completions, prompts=prompts)
        with refusal(self, cv.FINDING_RECALL_PROMPTS_MALFORMED):
            self.score(completions, prompts=write_lines(self.root / "bad.jsonl", ["not json"]))
        with refusal(self, cv.FINDING_RECALL_INPUT_MISSING):
            self.score(completions, prompts=self.root / "nowhere.jsonl")
        self.assertFalse((self.root / "report.json").exists())

    def test_destinations_must_be_new_and_outside_the_raw_tree(self):
        completions = write_lines(self.root / "completions.jsonl", [self.row()])
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            recall_probe.emit(recall_probe.EmitRequest(self.run_dir, self.root / "probe"))
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            self.score(completions, out="completions.jsonl")
        raw = self.root / "elsewhere" / "outputs" / "raw"
        raw.mkdir(parents=True)
        alias = self.root / "alias"
        alias.symlink_to(raw, target_is_directory=True)
        for destination in (raw / "x", alias / "x"):
            with self.subTest(destination=destination):
                with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
                    recall_probe.emit(recall_probe.EmitRequest(self.run_dir, destination))
                with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
                    self.score(completions, out=destination / "report.json")
        self.assertEqual(list(raw.iterdir()), [])

    def test_a_destination_that_appears_after_the_check_is_refused_with_a_code(self):
        completions = write_lines(self.root / "completions.jsonl", [self.row()])
        taken_dir, taken_file = self.root / "taken", self.root / "taken.json"
        taken_dir.mkdir()
        taken_file.write_text("{}", encoding="utf-8")
        with mock.patch.object(recall_probe, "_check_destination"):
            with refusal(self, cv.FINDING_DESTINATION_EXISTS, "taken"):
                recall_probe.emit(recall_probe.EmitRequest(self.run_dir, taken_dir))
            with refusal(self, cv.FINDING_DESTINATION_EXISTS, "taken.json"):
                self.score(completions, out="taken.json")
        self.assertEqual(list(taken_dir.iterdir()), [])
        self.assertEqual(taken_file.read_text(encoding="utf-8"), "{}")

    def test_runs_must_exist_and_carry_a_positive_record(self):
        completions = write_lines(self.root / "completions.jsonl", [self.row()])
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            recall_probe.emit(recall_probe.EmitRequest(self.root / "nowhere", self.root / "out"))
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            recall_probe.score(recall_probe.ScoreRequest(
                self.prompts, completions, self.root / "nowhere", self.root / "out.json"))
        negatives = self.root / "negatives"
        oc.write_jsonl(negatives / generate.CANDIDATES_FILENAME, rejected())
        with refusal(self, cv.FINDING_RECALL_NO_POSITIVE_RECORDS):
            recall_probe.emit(recall_probe.EmitRequest(negatives, self.root / "out"))
        self.assertFalse((self.root / "out").exists())
        self.assertFalse((self.root / "out.json").exists())


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-recall-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        _summary, _records, self.run_dir = smoke_run()
        self.prompts = self.root / "probe" / recall_probe.PROMPTS_FILENAME

    def emit(self, *flags):
        return invoke(["recall-probe", "emit", "--run", str(self.run_dir),
                       "--out", str(self.prompts.parent), *flags])

    def score(self, name, rows, *flags):
        completions = write_lines(self.root / f"{name}.jsonl", completion_lines(rows))
        return invoke([
            "recall-probe", "score", "--prompts", str(self.prompts), "--completions",
            str(completions), "--run", str(self.run_dir), "--out", str(self.root / f"{name}.json"),
            *flags,
        ])

    def test_emit_exits_zero_then_refuses_its_own_destination(self):
        code, text, err = self.emit("--json")
        self.assertEqual([code, err], [0, ""])
        payload = json.loads(text)
        self.assertEqual([payload["command"], payload["status"]], ["recall-probe emit", "ok"])
        self.assertEqual(payload["summary"]["prompts"]["rows"], 2 * len(positives()))
        code, _text, err = self.emit()
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith(cv.FINDING_DESTINATION_EXISTS), err)

    def test_score_exits_one_on_exact_docstring_recall_and_zero_otherwise(self):
        self.emit()
        record = positives()[0]
        code, text, err = self.score(
            "recalled", [(record, DOCSTRING_ONLY, views.completion_of(record))], "--json")
        self.assertEqual([code, err], [1, ""])
        payload = json.loads(text)
        self.assertEqual([payload["command"], payload["status"]],
                         ["recall-probe score", "findings"])
        self.assertEqual([f["code"] for f in payload["findings"]],
                         [cv.RECALL_EXACT_UNDER_DOCSTRING_ONLY])
        self.assertEqual(payload["report"]["docstring_only_exact_recall_ids"], [record["id"]])
        code, text, err = self.score("clean", [(record, NO_EVIDENCE, broken_of(record))])
        self.assertEqual([code, err], [0, ""])
        self.assertTrue(text.startswith("recall probe ok: "), text)
        self.assertIn("nothing was executed", text)

    def test_refusals_exit_two_and_write_nothing(self):
        self.emit()
        code, text, err = self.score("unknown", [({"id": UNKNOWN_ID}, NO_EVIDENCE, "x\n")],
                                     "--json")
        self.assertEqual([code, err], [2, ""])
        payload = json.loads(text)
        self.assertEqual([payload["status"], payload["code"], payload["command"]],
                         ["refused", cv.FINDING_RECALL_COMPLETION_UNKNOWN, "recall-probe"])
        self.assertFalse((self.root / "unknown.json").exists())
        raw = self.root / "outputs" / "raw" / "probe"
        code, text, _err = invoke(["recall-probe", "emit", "--run", str(self.run_dir),
                                   "--out", str(raw), "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(text)["code"], cv.FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())


class NeverExecutes(unittest.TestCase):
    def test_the_probe_modules_only_hash_and_parse(self):
        for module in PROBE_MODULES:
            with self.subTest(module=module.__name__):
                tree = ast.parse(inspect.getsource(module))
                self.assertFalse(import_targets(tree) & FORBIDDEN_IMPORTS)
                self.assertFalse(called_names(tree) & FORBIDDEN_CALLS)

    def test_the_import_and_call_scan_sees_what_it_forbids(self):
        tree = ast.parse("import os.path\nfrom . import executor\nfrom ._harness import main\n"
                         "from .sandbox import x\nexec('1')\n")
        self.assertEqual(import_targets(tree), {"os", ".executor", "._harness", ".sandbox"})
        self.assertEqual(called_names(tree), {"exec"})
        sha = hashlib.sha256(b"x = 1\n").hexdigest()
        self.assertEqual(recall_score.score_completion("x = 1\n", sha, structure_of("y = 1\n")),
                         verdict(True, True, False))


if __name__ == "__main__":
    unittest.main()
