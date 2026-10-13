"""The cross-run duplicate report: bound inputs, keep-first order, three codes, read-only."""

import ast
import contextlib
import copy
import hashlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
sys.path[:0] = [str(TESTS), str(TESTS.parent / "pipelines")]

from code_repair import candidate_io, dedup, lineage
from code_repair import vocabulary as cv
from code_repair._contract import dumps_exact_json, load_strict_json
from code_repair_test_support import (
    SEED,
    catalog,
    cli,
    envelope,
    generate,
    oc,
    refusal,
    required_item,
    smoke_run,
    verify,
    views,
)

SECOND_SEED = SEED + 1
TAIL = "\nUNUSED_TAIL = 0\n"


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def runs():
    """The smoke run and a second seed over the same catalog: ``(run_a, run_b)``."""

    return smoke_run()[2], smoke_run(seed=SECOND_SEED, count=12)[2]


def report(*run_dirs, out=None):
    return dedup.report(dedup.DedupRequest(tuple(run_dirs), out))


def records_of(run_dir):
    return [r for _n, r in oc.read_jsonl(run_dir / generate.CANDIDATES_FILENAME)]


def positive_ids(run_dir):
    return sorted(r["id"] for r in records_of(run_dir) if views.is_positive(r))


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_digests(root):
    """Every file under ``root`` by relative path and digest: the read-only witness."""

    return {str(p.relative_to(root)): file_digest(p)
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


def broken_text(record):
    return record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]


def function_node(text, function):
    """The module's ``def`` of this name."""

    return required_item(n for n in ast.walk(ast.parse(text))
                         if isinstance(n, ast.FunctionDef) and n.name == function)


def docstring_lines(node):
    """The line numbers of the function's docstring, which a rename leaves alone."""

    if ast.get_docstring(node) is None:
        return range(0)
    return range(node.body[0].lineno, node.body[0].end_lineno + 1)


def local_names(node):
    """The function's parameters and the names it binds."""

    names = (n for n in ast.walk(node) if isinstance(n, ast.Name))
    return {a.arg for a in node.args.args} | {n.id for n in names if isinstance(n.ctx, ast.Store)}


def rename_identifiers(text, function):
    """The function's parameters and locals renamed consistently everywhere but its docstring."""

    node = function_node(text, function)
    protected = docstring_lines(node)
    names = sorted(local_names(node), key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(names) + r")\b")
    return "\n".join(
        line if number in protected else pattern.sub(r"\1_renamed", line)
        for number, line in enumerate(text.split("\n"), 1)
    )


def rebind_broken(record, text):
    """Replace the broken module and restamp every digest that binds it, so it stays positive."""

    digest = catalog.sha256_text(text)
    record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME] = text
    record["scenario"]["broken_program"]["sha256"] = digest
    record["result"]["broken_sha256"] = digest
    record["result"]["phases"]["mutant"]["module_sha256"] = digest
    record["result"]["evidence_sha256"] = verify.result_hash(record["result"]["phases"])
    record["provenance"]["record_sha256"] = envelope.record_digest(record)
    return record


def first_positive(records):
    return required_item(r for r in sorted(records, key=lambda r: r["id"]) if views.is_positive(r))


class RunCopies:
    """Private copies of the smoke run with edited candidates and a rebound RUN.json."""

    def __init__(self, case):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-dedup-"))
        case.addCleanup(shutil.rmtree, self.root, True)

    def copy(self, name, edit=None, run_edit=None):
        copied = self.root / name
        shutil.copytree(smoke_run()[2], copied)
        records = [copy.deepcopy(r) for r in records_of(copied)]
        if edit is not None:
            edit(records)
        candidates = copied / generate.CANDIDATES_FILENAME
        candidates.unlink()
        oc.write_jsonl(candidates, records)
        run_file = copied / generate.RUN_FILENAME
        summary = load_strict_json(run_file.read_bytes())
        summary["candidates_sha256"] = file_digest(candidates)
        if run_edit is not None:
            run_edit(summary)
        run_file.write_text(
            dumps_exact_json(summary, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return copied


class KeepFirst(unittest.TestCase):
    def test_two_seeds_keep_first_by_run_order_then_sorted_id(self):
        run_a, run_b = runs()
        ids_a, ids_b = positive_ids(run_a), positive_ids(run_b)
        self.assertEqual((report(run_a)["dropped"], report(run_b)["dropped"]), ([], []))
        forward, backward = report(run_a, run_b), report(run_b, run_a)
        self.assertEqual(forward["format"], dedup.DEDUP_FORMAT)
        self.assertEqual(forward["runs"], [
            {"path": str(run_dir), "records": len(records_of(run_dir)), "positives": len(ids),
             "candidates_sha256": file_digest(run_dir / generate.CANDIDATES_FILENAME)}
            for run_dir, ids in ((run_a, ids_a), (run_b, ids_b))
        ])
        self.assertTrue(forward["dropped"], "the fixture seeds must share a mutant")
        self.assertEqual(forward["kept"][:len(ids_a)], ids_a)
        self.assertEqual(backward["kept"][:len(ids_b)], ids_b)
        self.assertNotEqual(forward["kept"], backward["kept"])
        for manifest, first, second in ((forward, ids_a, ids_b), (backward, ids_b, ids_a)):
            dropped = manifest["dropped"]
            self.assertEqual({d["run"] for d in dropped}, {1})
            self.assertLessEqual({d["id"] for d in dropped}, set(second))
            self.assertLessEqual({d["duplicate_of"] for d in dropped}, set(first))
            self.assertLessEqual({d["code"] for d in dropped}, cv.DEDUP_CODE_SET)
            self.assertEqual(set(manifest["kept"]) | {d["id"] for d in dropped},
                             set(ids_a) | set(ids_b))
        by_code = forward["counts"]["by_code"]
        self.assertEqual(list(by_code), list(cv.DEDUP_CODES))
        self.assertEqual(forward["counts"], {
            "runs": 2, "records": len(records_of(run_a)) + len(records_of(run_b)),
            "positives": len(ids_a) + len(ids_b), "kept": len(forward["kept"]),
            "dropped": sum(by_code.values()), "by_code": by_code,
        })
        self.assertEqual(report(run_a, run_b), forward)

    def test_the_same_run_twice_makes_every_positive_an_exact_duplicate_of_itself(self):
        run_a, _run_b = runs()
        ids = positive_ids(run_a)
        manifest = report(run_a, run_a)
        self.assertEqual(manifest["kept"], ids)
        self.assertEqual(manifest["dropped"], [
            {"id": i, "run": 1, "duplicate_of": i, "code": cv.DEDUP_DUPLICATE_EXACT} for i in ids
        ])
        self.assertEqual(manifest["counts"]["by_code"], {
            cv.DEDUP_DUPLICATE_EXACT: len(ids), cv.DEDUP_DUPLICATE_STRUCTURAL: 0,
            cv.DEDUP_DUPLICATE_SITE: 0,
        })

    def test_the_codes_are_their_own_family(self):
        self.assertEqual(len(cv.DEDUP_CODES), len(cv.DEDUP_CODE_SET))
        for other in (cv.EXPORT_CODE_SET, cv.FINDING_CODE_SET, cv.SKIP_CODE_SET,
                      cv.REASON_CODE_SET):
            self.assertFalse(cv.DEDUP_CODE_SET & other)


class WithinOneRun(unittest.TestCase):
    """Duplicates inside one run stay the export's selection: never reported, never claimed."""

    def setUp(self):
        self.copies = RunCopies(self)

    def test_an_in_run_twin_is_kept_and_a_later_run_repeats_the_first_claimant(self):
        run_a, _run_b = runs()
        twinned = {}

        def edit(records):
            original = first_positive(records)
            twin = copy.deepcopy(original)
            twin["id"] = original["id"][:-5] + "99999"
            twin["provenance"]["record_sha256"] = envelope.record_digest(twin)
            self.assertTrue(views.is_positive(twin))
            records.append(twin)
            twinned.update(original=original["id"], twin=twin["id"])

        doubled = self.copies.copy("doubled", edit)
        alone = report(doubled)
        self.assertEqual(alone["dropped"], [])
        self.assertEqual(alone["kept"], positive_ids(doubled))
        self.assertLess(twinned["original"], twinned["twin"])
        self.assertIn(twinned["twin"], alone["kept"])
        later = report(doubled, run_a)
        self.assertEqual(later["kept"], positive_ids(doubled))
        repeats = [d["duplicate_of"] for d in later["dropped"] if d["id"] == twinned["original"]]
        self.assertEqual(repeats, [twinned["original"]])
        earlier = report(run_a, doubled)
        self.assertEqual(
            {d["id"]: (d["duplicate_of"], d["code"]) for d in earlier["dropped"]
             if d["duplicate_of"] == twinned["original"]},
            {i: (twinned["original"], cv.DEDUP_DUPLICATE_EXACT)
             for i in (twinned["original"], twinned["twin"])},
        )


class Codes(unittest.TestCase):
    def setUp(self):
        self.copies = RunCopies(self)

    def _edited_positive(self, name, change):
        """A run copy whose first positive's broken module passed through ``change``."""

        edited = {}

        def edit(records):
            target = first_positive(records)
            edited.update(id=target["id"], before=broken_text(target))
            rebind_broken(target, change(target))
            edited["after"] = broken_text(target)
            self.assertTrue(views.is_positive(target))

        return self.copies.copy(name, edit), edited

    def test_a_consistently_renamed_broken_module_is_a_structural_duplicate(self):
        run_a, _run_b = runs()
        renamed, edited = self._edited_positive("renamed", lambda r: rename_identifiers(
            broken_text(r), r["scenario"]["source"]["upstream"]["function"]))
        self.assertNotEqual(edited["before"], edited["after"])
        self.assertEqual(lineage.structure_digest(edited["before"]),
                         lineage.structure_digest(edited["after"]))
        manifest = report(run_a, renamed)
        dropped = {d["id"]: d for d in manifest["dropped"]}
        self.assertEqual(dropped[edited["id"]], {
            "id": edited["id"], "run": 1, "duplicate_of": edited["id"],
            "code": cv.DEDUP_DUPLICATE_STRUCTURAL,
        })
        self.assertEqual({d["code"] for i, d in dropped.items() if i != edited["id"]},
                         {cv.DEDUP_DUPLICATE_EXACT})
        self.assertEqual(manifest["counts"]["by_code"][cv.DEDUP_DUPLICATE_STRUCTURAL], 1)
        # A dropped record never claims keys: the renamed copy passed twice is structural both
        # times (of the kept original), never an exact duplicate of its dropped twin.
        again = [d for d in report(run_a, renamed, renamed)["dropped"] if d["id"] == edited["id"]]
        self.assertEqual([(d["run"], d["code"]) for d in again],
                         [(1, cv.DEDUP_DUPLICATE_STRUCTURAL), (2, cv.DEDUP_DUPLICATE_STRUCTURAL)])

    def test_the_same_site_under_a_differing_module_is_a_site_duplicate(self):
        run_a, _run_b = runs()
        shifted, edited = self._edited_positive("shifted", lambda r: broken_text(r) + TAIL)
        self.assertNotEqual(lineage.structure_digest(edited["before"]),
                            lineage.structure_digest(edited["after"]))
        manifest = report(run_a, shifted)
        dropped = {d["id"]: d for d in manifest["dropped"]}
        self.assertEqual((dropped[edited["id"]]["code"], dropped[edited["id"]]["duplicate_of"]),
                         (cv.DEDUP_DUPLICATE_SITE, edited["id"]))
        self.assertEqual(manifest["counts"]["by_code"][cv.DEDUP_DUPLICATE_SITE], 1)

    def test_the_same_site_of_a_revised_original_module_is_kept(self):
        """A catalog revision keeps the program id and site; the site key is bound to its bytes."""
        run_a, _run_b = runs()
        revised = {}

        def edit(records):
            target = first_positive(records)
            target["id"] = revised["id"] = target["id"][:-5] + "99998"
            rebind_broken(target, broken_text(target) + TAIL)
            # The repair restores the revised original, so every digest bound to it moves.
            repair = target["candidate_prediction"]["predicted_repair"]
            repair["files"][cv.PROGRAM_FILENAME] += TAIL
            source_sha = catalog.sha256_text(repair["files"][cv.PROGRAM_FILENAME])
            repair["sha256"] = target["result"]["repaired_sha256"] = source_sha
            target["scenario"]["source"]["module_sha256"] = source_sha
            for name in ("original", "original_repeat", "repaired"):
                target["result"]["phases"][name]["module_sha256"] = source_sha
            target["result"]["evidence_sha256"] = verify.result_hash(target["result"]["phases"])
            target["provenance"]["record_sha256"] = envelope.record_digest(target)
            self.assertTrue(views.is_positive(target))

        manifest = report(run_a, self.copies.copy("revised", edit))
        self.assertIn(revised["id"], manifest["kept"])
        self.assertEqual(manifest["counts"]["by_code"][cv.DEDUP_DUPLICATE_SITE], 0)
        self.assertEqual({d["code"] for d in manifest["dropped"]}, {cv.DEDUP_DUPLICATE_EXACT})


class Refusals(unittest.TestCase):
    def setUp(self):
        self.copies = RunCopies(self)

    def test_a_run_whose_digest_binding_fails_is_refused(self):
        run_a, _run_b = runs()
        tampered = self.copies.copy("tampered",
                                    run_edit=lambda s: s.update(candidates_sha256="0" * 64))
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, "candidates_sha256", tampered.name):
            report(run_a, tampered)
        appended = self.copies.copy("appended")
        with (appended / generate.CANDIDATES_FILENAME).open("ab") as handle:
            handle.write(b"\n")
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, "candidates_sha256"):
            report(appended)
        unpinned = self.copies.copy("unpinned", run_edit=lambda s: s.pop("candidates_sha256"))
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, "candidates_sha256"):
            report(unpinned)

    def test_a_rehashed_record_whose_evidence_disagrees_with_its_rows_refuses_its_run(self):
        run_a, _run_b = runs()

        def edit(records):
            target = first_positive(records)
            required_item(target["result"]["public_failure_evidence"])["got"] += "drift"
            target["provenance"]["record_sha256"] = envelope.record_digest(target)
            self.assertTrue(views.is_positive(target))

        drifted = self.copies.copy("drifted", edit)
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, "fails integrity", drifted.name,
                     cv.EXPORT_RECORD_FAILS_CONTRACT):
            report(run_a, drifted)

    def test_missing_run_files_and_a_foreign_summary_are_refused(self):
        empty = self.copies.root / "empty"
        empty.mkdir()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, generate.CANDIDATES_FILENAME):
            report(empty)
        no_run = self.copies.copy("no-run")
        (no_run / generate.RUN_FILENAME).unlink()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, generate.RUN_FILENAME):
            report(no_run)
        legacy = self.copies.copy("legacy", run_edit=lambda s: s.update(format="code-repair-run/1"))
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, "not a code-repair"):
            report(legacy)
        garbled = self.copies.copy("garbled")
        (garbled / generate.RUN_FILENAME).write_bytes(b"{not json")
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, "not JSON"):
            report(garbled)
        # How deep a nesting the parser follows depends on the interpreter, so the overflow
        # itself is simulated: it must still be the coded refusal, not a generic error.
        overflow = RecursionError("maximum recursion depth exceeded")
        deep = self.copies.copy("deep")
        with (mock.patch.object(candidate_io, "load_strict_json", side_effect=overflow),
              refusal(self, cv.FINDING_RUN_FILE_MISSING, "not JSON", "RecursionError")):
            report(deep)
        with refusal(self, cv.FINDING_RUN_FILE_MISSING, "at least one"):
            report()

    def test_a_destination_that_exists_or_aliases_raw_is_refused_before_any_run_is_read(self):
        existing = self.copies.root / "existing.json"
        existing.write_text("{}", encoding="utf-8")
        nowhere = self.copies.root / "nowhere"
        with refusal(self, cv.FINDING_DESTINATION_EXISTS, "already exists"):
            report(nowhere, out=existing)
        raw = self.copies.root / "outputs" / "raw" / "dedup.json"
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW, "raw tree"):
            report(nowhere, out=raw)
        self.assertFalse(raw.parent.exists())
        self.assertEqual(existing.read_text(encoding="utf-8"), "{}")

    def test_a_destination_inside_a_run_directory_is_refused(self):
        run_a, run_b = runs()
        before = tree_digests(run_b)
        for out in (run_b / "DEDUP.json", run_b / "reports" / "DEDUP.json"):
            with (self.subTest(out=out.relative_to(run_b)),
                  refusal(self, cv.FINDING_DESTINATION_INSIDE_RUN, "read-only")):
                report(run_a, run_b, out=out)
        self.assertEqual(tree_digests(run_b), before)
        alias = self.copies.root / "alias"
        alias.symlink_to(run_a, target_is_directory=True)
        with refusal(self, cv.FINDING_DESTINATION_INSIDE_RUN):
            report(run_a, out=alias / "DEDUP.json")
        self.assertFalse((run_a / "DEDUP.json").exists())

    def test_one_id_naming_two_different_candidates_is_refused(self):
        run_a, _run_b = runs()

        def edit(records):
            target = first_positive(records)
            rebind_broken(target, broken_text(target) + TAIL)
            target["scenario"]["source"]["program_id"] += "-other"
            target["provenance"]["record_sha256"] = envelope.record_digest(target)
            self.assertTrue(views.is_positive(target))

        collided = self.copies.copy("collided", edit)
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, "more than one kept candidate"):
            report(run_a, collided)

        def edit_beside_the_original(records):
            original = copy.deepcopy(first_positive(records))
            edit(records)
            records.append(original)

        # Within one run nothing is compared, so a repeated id is refused as the run loads,
        # before any id could become a kept entry in one run and a dropped one in another.
        doubled = self.copies.copy("doubled", edit_beside_the_original)
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, "repeat within the run", doubled.name):
            report(doubled)
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY, "repeat within the run"):
            report(run_a, doubled)


class ReadOnlyAndWriting(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-dedup-out-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_runs_are_never_touched_and_the_manifest_lands_once_in_a_new_destination(self):
        run_a, run_b = runs()
        before = (tree_digests(run_a), tree_digests(run_b))
        out = self.root / "reports" / "stacked.json"
        manifest = report(run_a, run_b, out=out)
        after = (tree_digests(run_a), tree_digests(run_b))
        self.assertEqual(after, before)
        expected = dumps_exact_json(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        self.assertEqual(out.read_text(encoding="utf-8"), expected)
        self.assertEqual(load_strict_json(out.read_bytes()), manifest)
        self.assertEqual([p.name for p in out.parent.iterdir()], [out.name])
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            report(run_a, out=out)
        self.assertEqual(out.read_text(encoding="utf-8"), expected)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-dedup-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_duplicates_exit_one_with_coded_findings_and_the_written_manifest(self):
        run_a, run_b = runs()
        out = self.root / "DEDUP.json"
        code, text, err = invoke([
            "dedup", "--run", str(run_a), "--run", str(run_b), "--out", str(out), "--json",
        ])
        self.assertEqual((code, err), (1, ""))
        payload = load_strict_json(text)
        self.assertEqual((payload["command"], payload["status"]), ("dedup", "findings"))
        self.assertTrue(payload["findings"])
        self.assertLessEqual({f["code"] for f in payload["findings"]}, cv.DEDUP_CODE_SET)
        self.assertEqual([f["record_id"] for f in payload["findings"]],
                         [d["id"] for d in payload["manifest"]["dropped"]])
        self.assertEqual(payload["manifest"], load_strict_json(out.read_bytes()))
        code, text, err = invoke(["dedup", "--run", str(run_a), "--run", str(run_b)])
        self.assertEqual((code, err), (1, ""))
        self.assertIn(cv.DEDUP_DUPLICATE_EXACT, text)
        self.assertIn("\ndedup: ", text)

    def test_no_duplicates_exit_zero(self):
        run_a, _run_b = runs()
        code, text, err = invoke(["dedup", "--run", str(run_a), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = load_strict_json(text)
        self.assertEqual((payload["status"], payload["findings"]), ("ok", []))
        self.assertEqual(payload["manifest"]["counts"]["dropped"], 0)
        code, text, err = invoke(["dedup", "--run", str(run_a)])
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(text.startswith("dedup: "), text)

    def test_refusals_exit_two_as_coded_messages(self):
        run_a, _run_b = runs()
        code, out, err = invoke(["dedup", "--run", str(self.root / "missing")])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith(cv.FINDING_RUN_FILE_MISSING + ": "), err)
        taken = self.root / "taken"
        taken.mkdir()
        code, out, err = invoke(["dedup", "--run", str(run_a), "--out", str(taken), "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = load_strict_json(out)
        self.assertEqual((payload["status"], payload["code"], payload["command"]),
                         ("refused", cv.FINDING_DESTINATION_EXISTS, "dedup"))
        raw = self.root / "outputs" / "raw" / "report"
        code, out, err = invoke(["dedup", "--run", str(run_a), "--out", str(raw)])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith(cv.FINDING_DESTINATION_UNDER_RAW + ": "), err)
        self.assertFalse(raw.parent.exists())


if __name__ == "__main__":
    unittest.main()
