"""The direct CLI script and the package spelling of the gate, exercised in this process."""

import contextlib
import importlib
import io
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate import denylist, procedural
from task_gate_test_support import REPO, cv, write_denylist_json

SCRIPT = REPO / "pipelines" / "task_gate_cli.py"
FIXTURE = REPO / "tests" / "fixtures" / "code-repair"
PIPELINES = REPO / "pipelines"


def run_script(*argv, path=None):
    """Run ``task_gate_cli.py`` as ``__main__`` in this process; return (exit code, out, err).

    ``path`` replaces ``sys.path`` for the run (default: unchanged).
    """

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with mock.patch.object(sys, "argv", [str(SCRIPT), *argv]), \
                mock.patch.object(sys, "path", sys.path if path is None else path):
            try:
                runpy.run_path(str(SCRIPT), run_name="__main__")
            except SystemExit as exited:
                return exited.code, out.getvalue(), err.getvalue()
    return None, out.getvalue(), err.getvalue()


class DirectScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.deny = self.root / "deny.json"
        write_denylist_json(self.deny, ["eval-only-program"])

    def test_procedural_subcommand_exits_zero_and_writes_a_new_run(self):
        out = self.root / "procedural"
        code, stdout, _ = run_script(
            "procedural", "--catalog", str(FIXTURE), "--denylist", str(self.deny), "--seed", "5",
            "--count", "1", "--timeout", "5", "--out", str(out),
        )
        self.assertEqual(code, 0)
        summary = json.loads((out / cv.SUMMARY_FILENAME).read_text())
        self.assertEqual(json.loads(stdout)["total"], summary["total"])
        proposals = summary["inputs"]["proposals"]
        self.assertEqual(proposals["origin"], "procedural")
        self.assertEqual((proposals["seed"], proposals["requested_count"]), (5, 1))
        self.assertEqual(proposals["per_program_cap"], 3)
        self.assertEqual(proposals["count"], summary["total"])

    def test_verify_subcommand_exits_zero_on_a_proposals_file(self):
        rows = self.root / "rows.jsonl"
        rows.write_text(json.dumps(
            {"program_id": "eval-only-program", "replacement_text": "0", "original_text": "x"},
        ) + "\n")
        out = self.root / "verified"
        code, _, _ = run_script(
            "verify", "--catalog", str(FIXTURE), "--denylist", str(self.deny),
            "--proposals", str(rows), "--out", str(out), "--timeout", "5",
        )
        self.assertEqual(code, 0)
        verdicts = json.loads((out / cv.SUMMARY_FILENAME).read_text())["verdicts"]
        self.assertEqual(verdicts[cv.VERDICT_DENYLISTED], 1)

    def test_refusals_exit_two_name_the_code_and_write_nothing(self):
        cases = {
            cv.REFUSE_DENYLIST_MISSING: [
                "--seed", "5", "--count", "1", "--denylist", str(self.root / "missing-denylist.txt"),
            ],
            cv.REFUSE_DESTINATION_EXISTS: ["--seed", "5", "--count", "1", "--denylist", str(self.deny)],
        }
        for code_name, extra in cases.items():
            out = self.root / f"refused-{code_name}"
            if code_name == cv.REFUSE_DESTINATION_EXISTS:
                out.mkdir()
            with self.subTest(code=code_name):
                code, _, stderr = run_script(
                    "procedural", "--catalog", str(FIXTURE), "--out", str(out), *extra,
                )
                self.assertEqual(code, 2)
                self.assertIn(f"refused: {code_name}", stderr)
                self.assertEqual(sorted(out.iterdir()) if out.exists() else [], [])

    def test_the_script_puts_pipelines_on_the_path_when_it_is_missing(self):
        bare = [entry for entry in sys.path if Path(entry or ".").resolve() != PIPELINES]
        with mock.patch.dict(sys.modules):  # cached task_gate modules would mask the path insert
            PackageSpelling.forget_repository_modules()
            code, _, stderr = run_script(
                "procedural", "--catalog", str(FIXTURE),
                "--denylist", str(self.root / "missing-denylist.txt"),
                "--seed", "5", "--count", "1", "--out", str(self.root / "bare"), path=bare,
            )
        self.assertEqual(code, 2)
        self.assertIn(cv.REFUSE_DENYLIST_MISSING, stderr)
        self.assertIn(str(PIPELINES), bare)

    def test_importing_the_script_as_a_module_runs_nothing(self):
        namespace = runpy.run_path(str(SCRIPT), run_name="task_gate_cli_imported")
        self.assertTrue(callable(namespace["main"]))

    def test_verify_denies_validation_and_held_out_catalog_programs(self):
        catalog = procedural.load_catalog(FIXTURE)
        eval_ids = sorted(procedural.eval_program_ids(catalog))
        self.assertEqual(len(eval_ids), 2)
        rows = self.root / "eval-splits.jsonl"
        rows.write_text("".join(
            json.dumps({"program_id": program_id, "replacement_text": "0", "original_text": "x"})
            + "\n"
            for program_id in eval_ids
        ))
        out = self.root / "verified-splits"
        code, _, _ = run_script(
            "verify", "--catalog", str(FIXTURE), "--denylist", str(self.deny),
            "--proposals", str(rows), "--out", str(out), "--timeout", "5",
        )
        self.assertEqual(code, 0)
        verdicts = json.loads((out / cv.SUMMARY_FILENAME).read_text())["verdicts"]
        self.assertEqual(verdicts[cv.VERDICT_DENYLISTED], 2)

    def test_an_unreadable_proposals_file_is_a_coded_refusal(self):
        code, _, stderr = run_script(
            "verify", "--catalog", str(FIXTURE), "--denylist", str(self.deny),
            "--proposals", str(self.root / "missing.jsonl"), "--out", str(self.root / "never"),
        )
        self.assertEqual(code, 2)
        self.assertIn(cv.REFUSE_PROPOSALS_INVALID, stderr)
        self.assertFalse((self.root / "never").exists())

    def test_omitted_denylist_denies_a_held_out_catalog_program(self):
        catalog = procedural.load_catalog(REPO / "catalogs" / "python-repair-v1")
        program = next(item for item in catalog.programs if item.split == "held_out")
        vendored = denylist.load_denylist(None)
        self.assertIn(program.program_id, vendored.program_ids)
        rows = self.root / "held-out.jsonl"
        rows.write_text(json.dumps(
            {"program_id": program.program_id, "replacement_text": "0", "original_text": "x"},
        ) + "\n")
        out = self.root / "held-out-run"
        code, _, stderr = run_script(
            "verify", "--catalog", str(catalog.directory), "--proposals", str(rows),
            "--out", str(out), "--timeout", "5",
        )
        self.assertEqual(code, 0, stderr)
        summary = json.loads((out / cv.SUMMARY_FILENAME).read_text())
        self.assertEqual(summary["verdicts"][cv.VERDICT_DENYLISTED], 1)
        self.assertEqual(summary["inputs"]["denylist"]["sha256"], vendored.sha256)
        self.assertEqual(summary["inputs"]["denylist"]["entries"], 19)
        task = json.loads((out / cv.TASKS_FILENAME).read_text().splitlines()[0])
        self.assertEqual(
            (task["program_id"], task["verdict"], task["detail"]),
            (program.program_id, cv.VERDICT_DENYLISTED, cv.DETAIL_ON_DENYLIST),
        )

    def test_an_explicit_text_denylist_is_recorded_by_its_digest(self):
        catalog = procedural.load_catalog(REPO / "catalogs" / "python-repair-v1")
        program = next(item for item in catalog.programs if item.split == "held_out")
        text = self.root / "legacy.txt"
        text.write_bytes(f"{program.program_id}\n".encode())
        rows = self.root / "legacy-rows.jsonl"
        rows.write_text(json.dumps(
            {"program_id": program.program_id, "replacement_text": "0", "original_text": "x"},
        ) + "\n")
        out = self.root / "legacy-run"
        code, _, stderr = run_script(
            "verify", "--catalog", str(catalog.directory), "--denylist", str(text),
            "--proposals", str(rows), "--out", str(out), "--timeout", "5",
        )
        self.assertEqual(code, 0, stderr)
        summary = json.loads((out / cv.SUMMARY_FILENAME).read_text())
        self.assertEqual(summary["verdicts"][cv.VERDICT_DENYLISTED], 1)
        self.assertEqual(summary["inputs"]["denylist"]["sha256"], denylist.load_denylist(text).sha256)
        self.assertNotEqual(summary["inputs"]["denylist"]["sha256"], denylist.load_denylist(None).sha256)

    def _vendored_refusal(self, path: Path, code_name: str) -> None:
        out = self.root / f"vendored-{path.name}"
        with mock.patch.object(denylist, "VENDORED_DENYLIST", path):
            code, _, stderr = run_script(
                "procedural", "--catalog", str(FIXTURE), "--seed", "5", "--count", "1",
                "--out", str(out),
            )
        self.assertEqual(code, 2)
        self.assertIn(f"refused: {code_name}", stderr)
        self.assertFalse(out.exists())

    def test_a_missing_vendored_denylist_exits_two_and_writes_nothing(self):
        self._vendored_refusal(self.root / "absent-vendored.json", cv.REFUSE_DENYLIST_MISSING)

    def test_a_malformed_vendored_denylist_exits_two_and_writes_nothing(self):
        bad = self.root / "bad-vendored.txt"
        bad.write_bytes(b"")
        self._vendored_refusal(bad, cv.REFUSE_DENYLIST_MALFORMED)


# Literal module names only: each loader imports exactly one fixed package path.
FRESH_LOADERS = {
    "pipelines.task_gate._contract": lambda: importlib.import_module("pipelines.task_gate._contract"),
    "pipelines.task_gate.procedural": lambda: importlib.import_module("pipelines.task_gate.procedural"),
    "pipelines.task_gate.sandboxed": lambda: importlib.import_module("pipelines.task_gate.sandboxed"),
}


class PackageSpelling(unittest.TestCase):
    """``pipelines.task_gate.*`` imported fresh binds to the same objects as ``task_gate.*``."""

    @staticmethod
    def forget_repository_modules():
        for name, module in list(sys.modules.items()):
            origin = str(getattr(module, "__file__", None) or "")
            if name == "pipelines" or origin.startswith(str(PIPELINES)):
                del sys.modules[name]

    def import_fresh(self, *names):
        with mock.patch.dict(sys.modules), mock.patch.object(sys, "path", [str(REPO), *sys.path]):
            self.forget_repository_modules()
            modules = [FRESH_LOADERS[name]() for name in names]
            twins = [sys.modules[name.removeprefix("pipelines.")] for name in names]
            return [(m.__name__, m is t) for m, t in zip(modules, twins)]

    def test_contract_and_procedural_bind_their_flat_twins(self):
        found = self.import_fresh("pipelines.task_gate._contract", "pipelines.task_gate.procedural")
        self.assertEqual(
            found,
            [("pipelines.task_gate._contract", True), ("pipelines.task_gate.procedural", True)],
        )

    def test_the_sandboxed_harness_and_its_contract_bind_their_flat_twins(self):
        found = self.import_fresh("pipelines.task_gate.sandboxed")
        self.assertEqual(found, [("pipelines.task_gate.sandboxed", True)])

    def test_the_flat_spelling_of_the_same_modules_is_untouched_afterwards(self):
        before = sys.modules.get("task_gate._contract")
        self.import_fresh("pipelines.task_gate._contract")
        self.assertIs(sys.modules.get("task_gate._contract"), before)


if __name__ == "__main__":
    unittest.main()
