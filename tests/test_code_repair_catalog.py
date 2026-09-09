#!/usr/bin/env python3
"""The pinned catalog: loading, every coded refusal, and the original-passes check."""

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    FIXTURE_CATALOG, FakeExecutor, catalog, executor, fixture, program, refusal, report, rows,
    vocabulary as cv,
)


def copied_fixture(root):
    """A private copy of the fixture catalog under ``root``."""

    destination = Path(root) / "catalog"
    shutil.copytree(FIXTURE_CATALOG, destination)
    return destination


def rewrite_programs(directory, edit):
    """Apply ``edit`` to every program row and re-pin the programs digest in CATALOG.json."""

    path = directory / catalog.PROGRAMS_FILENAME
    rows_ = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    for row in rows_:
        edit(row)
    lines = [json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for row in rows_]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta_path = directory / catalog.CATALOG_FILENAME
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["programs_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class Loading(unittest.TestCase):
    def test_the_fixture_loads_with_every_pin_verified(self):
        loaded = fixture()
        self.assertEqual(loaded.catalog_id, "code-repair-fixture-v1")
        self.assertEqual(len(loaded.programs), 6)
        self.assertTrue({p.function for p in loaded.programs}.issuperset({"factorial", "abs_val"}))
        self.assertEqual(loaded.meta["upstream"]["license"], "MIT")
        self.assertEqual(len(loaded.license_sha256), 64)
        for prog in loaded.programs:
            with self.subTest(program=prog.function):
                self.assertEqual(catalog.sha256_text(prog.text), prog.sha256)
                self.assertTrue(prog.text.endswith("\n"))
                self.assertGreaterEqual(len(prog.examples), 3)
                self.assertTrue(prog.cases)
                self.assertIn(prog.reference.kind, cv.REFERENCE_KINDS)
                self.assertIn(prog.split, ("train", "validation", "held_out"))
                self.assertTrue(prog.group_id.startswith("g-"))
        self.assertEqual(loaded.split_policy.salt, "python-repair-v1")
        self.assertEqual({p.split for p in loaded.programs}, {"train", "validation", "held_out"})

    def test_examples_are_parsed_from_the_docstring_in_order(self):
        prog = program("factorial")
        self.assertEqual(prog.examples[0].source, "import math\n")
        self.assertEqual(prog.examples[-1].key(), ("factorial(0)\n", "1\n", None))
        self.assertIsNotNone(prog.examples[2].exc_msg)
        self.assertEqual(catalog.examples_of("x = 1\n", "f"), ())
        self.assertEqual(catalog.examples_sha256(prog.examples), prog.examples_sha256)

    def test_references_are_pinned_and_classified(self):
        self.assertEqual(program("sum_of_digits").reference.kind, cv.REFERENCE_SIBLING)
        self.assertEqual(program("sum_of_digits").reference.function, "sum_of_digits_compact")
        self.assertTrue(program("factorial").reference.certifying)
        self.assertFalse(program("is_square_free").reference.certifying)
        self.assertIsNone(program("is_square_free").reference.source)
        with refusal(self, cv.FINDING_PROGRAM_NOT_FOUND, "no program"):
            fixture().program("tap-0000000000000000")


class Refusals(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="code-repair-catalog-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.directory = copied_fixture(self.root)

    def test_missing_files_and_broken_pins_are_coded(self):
        (self.directory / catalog.LICENSE_FILENAME).unlink()
        with refusal(self, cv.FINDING_CATALOG_FILE_MISSING, "LICENSE"):
            catalog.load_catalog(self.directory)
        shutil.rmtree(self.directory)
        with refusal(self, cv.FINDING_CATALOG_FILE_MISSING, catalog.CATALOG_FILENAME):
            catalog.load_catalog(self.directory)

    def test_a_missing_catalog_field_carries_the_catalog_code(self):
        path = self.directory / catalog.CATALOG_FILENAME
        meta = json.loads(path.read_text(encoding="utf-8"))
        del meta["catalog_id"]
        path.write_text(json.dumps(meta), encoding="utf-8")
        with refusal(self, cv.FINDING_CATALOG_FIELD_MISSING, "catalog_id"):
            catalog.load_catalog(self.directory)

    def test_a_programs_file_that_drifted_from_its_digest_is_refused(self):
        path = self.directory / catalog.PROGRAMS_FILENAME
        path.write_text(path.read_text(encoding="utf-8").replace('"family":"maths"', '"family":"math"'), encoding="utf-8")
        with refusal(self, cv.FINDING_PROGRAMS_SHA_MISMATCH, "programs.jsonl"):
            catalog.load_catalog(self.directory)

    def test_each_program_pin_is_verified(self):
        cases = {
            cv.FINDING_PROGRAM_SHA256_MISMATCH: lambda row: row["module"].update(text=row["module"]["text"] + "# x\n"),
            cv.FINDING_PROGRAM_NOT_LF_FRAMED: lambda row: row["module"].update(text=row["module"]["text"].rstrip("\n")),
            cv.FINDING_TARGET_FUNCTION_NOT_FOUND: lambda row: row["upstream"].update(function="nobody"),
            cv.FINDING_REFERENCE_KIND_UNKNOWN: lambda row: row["hidden"]["reference"].update(kind="oracle_of_delphi"),
            cv.FINDING_PROGRAM_FIELD_MISSING: lambda row: row.pop("family"),
            cv.FINDING_PROGRAM_FIELD_INVALID: lambda row: row.update(split="dev"),
            cv.FINDING_EXAMPLES_SHA_MISMATCH: lambda row: row["public"].update(example_count=99),
            cv.FINDING_CATALOG_FIELD_INVALID: lambda row: row["upstream"].update(commit="deadbeef"),
        }
        for code, edit in cases.items():
            with self.subTest(code=code):
                shutil.rmtree(self.directory)
                self.directory = copied_fixture(self.root)

                def one(row, edit=edit):
                    if row["upstream"]["function"] == "abs_val":
                        edit(row)

                rewrite_programs(self.directory, one)
                with refusal(self, code):
                    catalog.load_catalog(self.directory)

    def test_a_wrong_type_catalog_field_carries_the_catalog_code(self):
        path = self.directory / catalog.CATALOG_FILENAME
        meta = json.loads(path.read_text(encoding="utf-8"))
        meta["catalog_id"] = 7
        path.write_text(json.dumps(meta), encoding="utf-8")
        with refusal(self, cv.FINDING_CATALOG_FIELD_INVALID, "catalog_id"):
            catalog.load_catalog(self.directory)

    def test_a_certifying_reference_without_hidden_cases_is_refused(self):
        def one(row):
            if row["upstream"]["function"] == "abs_val":
                row["hidden"]["cases"] = []

        rewrite_programs(self.directory, one)
        with refusal(self, cv.FINDING_PROGRAM_FIELD_INVALID, "hidden case"):
            catalog.load_catalog(self.directory)

    def test_a_malformed_doctest_directive_is_a_coded_refusal(self):
        def one(row):
            if row["upstream"]["function"] != "abs_val":
                return
            text = row["module"]["text"].replace(
                ">>> abs_val(-5.1)", ">>> abs_val(-5.1)  # doctest: +NO_SUCH_OPTION", 1
            )
            row["module"].update(text=text, sha256=hashlib.sha256(text.encode()).hexdigest())

        rewrite_programs(self.directory, one)
        with refusal(self, cv.FINDING_PROGRAM_FIELD_INVALID, "parser refuses"):
            catalog.load_catalog(self.directory)

    def test_a_non_string_group_id_is_refused_not_dropped(self):
        """Codex on #196: malformed grouping metadata must not read as "ungrouped"."""

        def one(row):
            if row["upstream"]["function"] == "abs_val":
                row["structure"] = {"group_id": 5}

        rewrite_programs(self.directory, one)
        with refusal(self, cv.FINDING_PROGRAM_FIELD_INVALID, "group_id"):
            catalog.load_catalog(self.directory)

    def test_a_reference_source_must_parse_and_define_its_function(self):
        for code, edit in (
            (cv.FINDING_PROGRAM_NOT_PARSEABLE, lambda ref: ref.update(source="def (\n")),
            (cv.FINDING_TARGET_FUNCTION_NOT_FOUND, lambda ref: ref.update(source="x = 1\n")),
            (cv.FINDING_PROGRAM_FIELD_INVALID, None),
        ):
            with self.subTest(code=code):
                shutil.rmtree(self.directory)
                self.directory = copied_fixture(self.root)

                def one(row, edit=edit):
                    if row["upstream"]["function"] != "factorial":
                        return
                    if edit is None:
                        row["hidden"]["cases"][0]["args"] = "(" + "1" * 5000 + ",)"
                        return
                    edit(row["hidden"]["reference"])
                    row["hidden"]["reference"]["sha256"] = hashlib.sha256(
                        row["hidden"]["reference"]["source"].encode()
                    ).hexdigest()

                rewrite_programs(self.directory, one)
                with refusal(self, code):
                    catalog.load_catalog(self.directory)

    def test_a_duplicate_program_id_is_refused(self):
        path = self.directory / catalog.PROGRAMS_FILENAME
        first = path.read_text(encoding="utf-8").splitlines()[0]
        rewrite_programs(self.directory, lambda row: None)
        path.write_text(path.read_text(encoding="utf-8") + first + "\n", encoding="utf-8")
        meta_path = self.directory / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["programs_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        meta["program_count"] = 7
        meta_path.write_text(json.dumps(meta, sort_keys=True), encoding="utf-8")
        with refusal(self, cv.FINDING_PROGRAM_ID_DUPLICATE, "repeats"):
            catalog.load_catalog(self.directory)


class OriginalPasses(unittest.TestCase):
    def test_the_fixture_originals_pass_and_references_agree_for_real(self):
        """Real subprocess evidence: the 'original passes' demonstration."""

        self.assertEqual(catalog.catalog_check(fixture(), executor.Executor(timeout_s=5.0)), [])

    def test_check_findings_are_coded_from_the_reports(self):
        prog = program("factorial")
        ok = report(rows("public", len(prog.examples)), rows("hidden", len(prog.cases)))
        engines = {
            cv.REASON_ORIGINAL_FAILS_PUBLIC: {"original": report(rows("public", 7, (2,)), rows("hidden", 15)), "reference": ok},
            cv.REASON_ORIGINAL_FAILS_HIDDEN: {"original": report(rows("public", 7), rows("hidden", 15, (1,))), "reference": ok},
            cv.REASON_ORIGINAL_TIMEOUT: {"original": report(failure="timeout"), "reference": ok},
            cv.REASON_ORIGINAL_HARNESS_ERROR: {"original": report(failure="load", detail="boom"), "reference": ok},
            cv.CHECK_REFERENCE_DISAGREES: {"original": ok, "reference": report((), rows("hidden", 15, (4,)))},
            cv.CHECK_REFERENCE_TIMEOUT: {"original": ok, "reference": report(failure="timeout")},
        }
        single = catalog.Catalog("x", FIXTURE_CATALOG, {}, "", "", (prog,))
        for code, by_phase in engines.items():
            with self.subTest(code=code):
                findings = catalog.catalog_check(single, FakeExecutor(by_phase))
                self.assertEqual([f["code"] for f in findings], [code])
                self.assertEqual(findings[0]["program_id"], prog.program_id)

    def test_a_failure_of_the_second_original_run_is_an_execution_finding(self):
        prog = program("factorial")
        answers = iter([report(rows("public", 7), rows("hidden", 15)), report(failure="timeout")])
        fake = FakeExecutor({"original": lambda job: next(answers), "reference": report((), rows("hidden", 15))})
        single = catalog.Catalog("x", FIXTURE_CATALOG, {}, "", "", (prog,))
        codes = [f["code"] for f in catalog.catalog_check(single, fake)]
        self.assertEqual(codes, [cv.REASON_ORIGINAL_TIMEOUT])

    def test_two_differing_original_runs_are_nondeterministic(self):
        prog = program("factorial")
        answers = iter([report(rows("public", 7), rows("hidden", 15)), report(rows("public", 7, (1,)), rows("hidden", 15))])
        fake = FakeExecutor({"original": lambda job: next(answers), "reference": report((), rows("hidden", 15))})
        single = catalog.Catalog("x", FIXTURE_CATALOG, {}, "", "", (prog,))
        codes = [f["code"] for f in catalog.catalog_check(single, fake)]
        self.assertEqual(codes, [cv.CHECK_SOURCE_NONDETERMINISTIC])


if __name__ == "__main__":
    unittest.main()


class StructureChecks(unittest.TestCase):
    """Groups, splits and the split policy are pins too."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="code-repair-structure-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.directory = copied_fixture(self.root)

    def check(self):
        loaded = catalog.load_catalog(self.directory)
        return [f["code"] for f in catalog._structure_findings(loaded)]

    def test_the_fixture_has_no_structural_drift(self):
        self.assertEqual(self.check(), [])

    def test_a_moved_split_or_group_is_a_drift_finding(self):
        def swap(row):
            if row["upstream"]["function"] == "factorial":
                row["split"] = "held_out" if row["split"] != "held_out" else "train"
                row["structure"]["group_id"] = "g-" + "0" * 32

        rewrite_programs(self.directory, swap)
        self.assertEqual(sorted(self.check()), [cv.CHECK_GROUP_DRIFT, cv.CHECK_SPLIT_DRIFT])

    def test_an_empty_split_is_reported_with_the_remedy(self):
        rewrite_programs(self.directory, lambda row: row.update(split="train"))
        loaded = catalog.load_catalog(self.directory)
        findings = catalog._structure_findings(loaded)
        self.assertIn(cv.CHECK_SPLIT_EMPTY, [f["code"] for f in findings])
        self.assertIn("change the salt", next(f["detail"] for f in findings if f["code"] == cv.CHECK_SPLIT_EMPTY))

    def test_a_policy_that_does_not_match_its_digest_is_refused(self):
        meta_path = self.directory / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["split_policy"]["salt"] = "another"
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with refusal(self, cv.FINDING_SPLIT_POLICY_INVALID, "does not match"):
            catalog.load_catalog(self.directory)
