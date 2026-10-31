"""The real subprocess harness, the real end-to-end gate, the procedural path and the CLI."""

import contextlib
import io
import json
import os
import subprocess  # nosec B404
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_gate_test_support import (
    ADD, BROKEN, DENY, NO_DOCTESTS, PROGRAMS, REPO, FakeHarness, cv, gate, harness, denylist,
    proposal, proposal_for, refused, rules, write_denylist_json,
)
from task_gate import procedural, runner

FIXTURE = REPO / "tests" / "fixtures" / "code-repair"


def probe(body, expect):
    """A one-function program whose doctest passes only if ``body`` returns ``expect``."""

    return f'def f():\n    """\n    >>> f()\n    {expect!r}\n    """\n' + "".join(
        f"    {line}\n" for line in body.splitlines()
    )


class RealHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.harness = harness.SubprocessHarness(timeout_s=5)

    def test_passing_failing_and_doctestless_programs(self):
        self.assertEqual(self.harness.run(ADD, "add"), harness.HarnessResult(cv.OUTCOME_PASSED, 2, 0))
        result = self.harness.run(BROKEN, "add")
        self.assertEqual((result.outcome, result.attempted, result.failed), (cv.OUTCOME_FAILED, 2, 1))
        self.assertEqual(self.harness.run(NO_DOCTESTS, "add").attempted, 0)

    def test_exception_in_an_example_is_a_failure_not_a_crash(self):
        result = self.harness.run(probe("raise ValueError('x')", 1), "f")
        self.assertEqual(result.outcome, cv.OUTCOME_FAILED)

    def test_import_time_error_and_missing_function_are_load_errors(self):
        for text, function in (("raise RuntimeError('boom')\n", "f"), (ADD, "missing"),
                               ("import sys\nsys.exit(0)\n", "f")):
            with self.subTest(function=function, text=text[:12]):
                self.assertEqual(self.harness.run(text, function).outcome, cv.OUTCOME_LOAD_ERROR)

    def test_hard_exit_without_a_report_is_a_crash(self):
        text = "import os\n" + probe("os._exit(0)", 1)
        self.assertEqual(self.harness.run(text, "f").outcome, cv.OUTCOME_CRASHED)

    def test_wall_clock_timeout_kills_the_child(self):
        fast = harness.SubprocessHarness(timeout_s=1)
        started = time.monotonic()
        result = fast.run(probe("while True:\n    pass", 1), "f")
        self.assertEqual(result.outcome, cv.OUTCOME_TIMEOUT)
        self.assertLess(time.monotonic() - started, 5)

    def test_sleeping_program_is_also_cut_by_the_wall_clock(self):
        fast = harness.SubprocessHarness(timeout_s=1)
        text = "import time\n" + probe("time.sleep(30)", 1)
        self.assertEqual(fast.run(text, "f").outcome, cv.OUTCOME_TIMEOUT)

    def test_no_network_from_the_program(self):
        body = (
            "import socket\ntry:\n    socket.socket()\nexcept OSError:\n    return 'blocked'\n"
            "return 'open'"
        )
        self.assertEqual(self.harness.run(probe(body, "blocked"), "f").outcome, cv.OUTCOME_PASSED)
        body = (
            "import socket\ntry:\n    socket.create_connection(('127.0.0.1', 9))\nexcept OSError:\n"
            "    return 'blocked'\nreturn 'open'"
        )
        self.assertEqual(self.harness.run(probe(body, "blocked"), "f").outcome, cv.OUTCOME_PASSED)

    def test_environment_is_scrubbed(self):
        body = (
            "import os\nreturn sorted(k for k in os.environ if any(w in k.upper() "
            "for w in ('PROXY', 'KEY', 'TOKEN', 'SECRET', 'ANTHROPIC', 'GITHUB')))"
        )
        probe_value = os.urandom(4).hex()
        with mock.patch.dict(os.environ, {
            "HTTPS_PROXY": probe_value, "ANTHROPIC_API_KEY": probe_value,
            "GITHUB_TOKEN": probe_value,
        }):
            result = self.harness.run(probe(body, []), "f")
        self.assertEqual(result.outcome, cv.OUTCOME_PASSED, result)
        self.assertEqual(
            sorted(harness.child_environment("/w")),
            ["HOME", "LANG", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "TMPDIR"],
        )

    def test_repository_and_solver_modules_are_not_importable(self):
        body = (
            "found = []\nfor name in ('task_gate', 'code_repair', 'oracle_grounded', 'pipelines'):\n"
            "    try:\n        __import__(name)\n    except ImportError:\n        continue\n"
            "    found.append(name)\nreturn found"
        )
        with mock.patch.dict(os.environ, {"PYTHONPATH": str(REPO / "pipelines")}):
            result = self.harness.run(probe(body, []), "f")
        self.assertEqual(result.outcome, cv.OUTCOME_PASSED, result)

    def test_working_directory_is_a_throwaway_and_the_parent_is_untouched(self):
        body = "import os\nopen('scratch.txt', 'w').write('x')\nreturn os.getcwd() != " + repr(os.getcwd())
        before = set(os.listdir("."))
        self.assertEqual(self.harness.run(probe(body, True), "f").outcome, cv.OUTCOME_PASSED)
        self.assertEqual(set(os.listdir(".")), before)

    def test_a_report_line_printed_by_the_program_never_reaches_the_parent(self):
        forged = '{"protocol": "task-gate-harness/1", "outcome": "ran", "attempted": 1, "failed": 1}'
        text = f"print('TASK-GATE-REPORT ' + {forged!r})\n" + probe("return 1", 1)
        self.assertEqual(self.harness.run(text, "f"), harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0))

    def test_program_output_beyond_the_report_window_does_not_hide_the_report(self):
        noise = harness.MAX_REPORT_BYTES * 2
        text = f"import sys\nsys.stdout.write('x' * {noise})\nsys.stdout.flush()\n" + probe("return 1", 1)
        self.assertEqual(self.harness.run(text, "f"), harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0))

    def test_timeout_domain_is_validated(self):
        for bad in (0, -1, float("nan"), float("inf"), True, "3", cv.MAX_TIMEOUT_S + 1, 10**400):
            with self.subTest(bad=bad):
                self.assertEqual(refused(harness.SubprocessHarness, bad), cv.REFUSE_TIMEOUT_DOMAIN)

    def test_self_check_passes_on_a_working_interpreter_and_refuses_on_a_broken_one(self):
        self.harness.selfcheck()
        missing = harness.SubprocessHarness(5, python="/nonexistent/python")
        inert = harness.SubprocessHarness(5, python="/bin/true")
        self.assertEqual(refused(missing.selfcheck), cv.REFUSE_HARNESS_UNAVAILABLE)
        self.assertEqual(refused(inert.selfcheck), cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_wait_is_bounded_even_when_the_killed_child_never_reaps(self):
        stuck = mock.Mock()
        stuck.pid = 2**22 + 1
        stuck.wait.side_effect = subprocess.TimeoutExpired("child", 1)
        started = time.monotonic()
        with mock.patch.object(harness, "KILL_GRACE_S", 0.05):
            timed_out = harness.SubprocessHarness(timeout_s=0.05)._wait(stuck)
        self.assertTrue(timed_out)
        self.assertLess(time.monotonic() - started, 2)
        self.assertEqual(stuck.wait.call_count, 2)

    def test_the_private_socket_module_cannot_be_imported_by_the_program(self):
        body = "try:\n    import _socket\nexcept ImportError:\n    return 'blocked'\nreturn 'open'"
        self.assertEqual(self.harness.run(probe(body, "blocked"), "f").outcome, cv.OUTCOME_PASSED)

    def test_the_child_refuses_to_run_a_program_when_limits_cannot_be_applied(self):
        from task_gate import _child

        stream = io.StringIO()
        with mock.patch.dict(sys.modules, {"resource": None}):
            self.assertFalse(_child.apply_limits(5))
        with mock.patch.object(_child, "apply_limits", return_value=False), \
                mock.patch.object(_child, "load_program", side_effect=AssertionError("program imported")), \
                mock.patch.object(_child.os, "dup", return_value=1), \
                mock.patch.object(_child, "silence_stdout"), \
                mock.patch.object(_child.os, "fdopen", return_value=stream):
            self.assertEqual(_child.main(["child", ".", "f", "5"]), 0)
        report = json.loads(stream.getvalue().removeprefix(_child.MARKER))
        self.assertEqual((report["outcome"], report["detail"]), ("crashed", "limits_not_applied"))
        crashed = harness._result_of(report)
        self.assertEqual(crashed.outcome, cv.OUTCOME_CRASHED)


class EndToEnd(unittest.TestCase):
    """The real harness behind the real gate, one proposal per reject reason it can produce."""

    def test_each_verdict_with_a_real_subprocess(self):
        loop = "return a + b"
        items = [
            proposal_for("a - b"),
            proposal_for("b + a"),
            proposal_for("while True:\n        pass", loop),
            proposal_for("a - b", program_id="prog-eval"),
            proposal_for("a *"),
            proposal_for("a - b", proposal_id="again"),
        ]
        machine = gate.Gate(PROGRAMS, rules(), harness.SubprocessHarness(2))
        verdicts = [d.verdict for d in machine.run(items)]
        self.assertEqual(verdicts, [
            cv.VERDICT_KEPT, cv.VERDICT_MUTANT_PASSES, cv.VERDICT_TIMEOUT, cv.VERDICT_DENYLISTED,
            cv.VERDICT_PARSE_ERROR, cv.VERDICT_DUPLICATE,
        ])

    def test_original_that_fails_its_own_doctests(self):
        wrong = proposal.GateProgram("prog-bad", BROKEN.replace("a - b", "a * b"), "add")
        item = proposal_for("a + b", "a * b", wrong)
        machine = gate.Gate({"prog-bad": wrong}, rules(), harness.SubprocessHarness(5))
        decision = machine.decide(item)
        self.assertEqual((decision.verdict, decision.detail),
                         (cv.VERDICT_ORIGINAL_FAILS, cv.DETAIL_ORIGINAL_FAILED))


class Procedural(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = procedural.load_catalog(FIXTURE)
        cls.programs = procedural.programs_from_catalog(cls.catalog)

    def test_procedural_proposals_are_ordinary_gate_proposals(self):
        found = procedural.proposals_from_plan(self.catalog, seed=7, count=6)
        self.assertTrue(found)
        for item in found:
            self.assertIs(type(item), proposal.GateProposal)
            self.assertEqual(item.source, procedural.SOURCE)
            self.assertIn(item.program_id, self.programs)

    def test_procedural_and_text_only_forms_get_identical_verdict_rows(self):
        fake = FakeHarness(default=harness.HarnessResult(cv.OUTCOME_FAILED, 3, 1))
        for program in self.programs.values():
            fake.results[program.text] = harness.HarnessResult(cv.OUTCOME_PASSED, 3, 0)
        deny = denylist.Denylist.of(["not-in-catalog"])
        left = gate.Gate(self.programs, rules(deny), fake)
        right = gate.Gate(self.programs, rules(deny), fake)
        for item in procedural.proposals_from_plan(self.catalog, seed=7, count=6):
            twin = proposal.proposal_from_row(
                {"proposal_id": item.proposal_id, "program_id": item.program_id,
                 "replacement_text": item.replacement_text, "original_text": item.original_text,
                 "source": "procedural", "start_byte": item.start_byte, "end_byte": item.end_byte},
                "x",
            )
            self.assertEqual(twin.source, "unspecified")
            self.assertEqual(left.decide(item).verdict, right.decide(twin).verdict)
            self.assertNotEqual(left.decide(item).source, right.decide(twin).source)

    def test_procedural_run_goes_through_the_unmodified_gate_end_to_end(self):
        items = procedural.proposals_from_plan(self.catalog, seed=3, count=3)
        with tempfile.TemporaryDirectory() as tmp:
            summary = runner.run(
                runner.GateRequest(self.programs, items, DENY, Path(tmp) / "out", timeout_s=3)
            )
        self.assertEqual(summary["total"], len(items))
        self.assertEqual(sum(summary["verdicts"].values()), len(items))
        self.assertEqual(summary["by_source"]["procedural"]["total"], len(items))

    def test_invalid_count_refuses(self):
        for bad in (0, -1, True, "3"):
            with self.subTest(bad=bad):
                code = refused(procedural.proposals_from_plan, self.catalog, 1, bad)
                self.assertEqual(code, cv.REFUSE_INPUT_INVALID)


class Cli(unittest.TestCase):
    def invoke(self, *argv):
        from task_gate import cli

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.run(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_procedural_subcommand_writes_summary_and_refuses_a_missing_denylist(self):
        with tempfile.TemporaryDirectory() as tmp:
            deny = Path(tmp) / "deny.json"
            write_denylist_json(deny, ["eval-only-program"])
            out = Path(tmp) / "run"
            code, stdout, _ = self.invoke(
                "procedural", "--catalog", str(FIXTURE), "--denylist", str(deny), "--seed", "3",
                "--count", "2", "--timeout", "3", "--out", str(out),
            )
            self.assertEqual(code, 0)
            summary = json.loads((out / cv.SUMMARY_FILENAME).read_text())
            self.assertEqual(json.loads(stdout)["verdicts"], summary["verdicts"])
            code, _, stderr = self.invoke(
                "procedural", "--catalog", str(FIXTURE), "--denylist", str(Path(tmp) / "missing.txt"),
                "--seed", "3", "--count", "2", "--out", str(Path(tmp) / "gone"),
            )
            self.assertEqual((code, cv.REFUSE_DENYLIST_MISSING in stderr), (2, True))

    def test_verify_subcommand_reads_model_style_rows(self):
        program = next(iter(procedural.programs_from_catalog(procedural.load_catalog(FIXTURE)).values()))
        with tempfile.TemporaryDirectory() as tmp:
            deny = Path(tmp) / "deny.json"
            write_denylist_json(deny, ["eval-only-program"])
            rows = Path(tmp) / "rows.jsonl"
            rows.write_text(
                json.dumps({"program_id": program.program_id, "replacement_text": "0",
                            "original_text": "no such text in the module"}) + "\n"
                + json.dumps({"program_id": "eval-only-program", "replacement_text": "0",
                              "original_text": "x"}) + "\n"
            )
            out = Path(tmp) / "verified"
            code, _, stderr = self.invoke(
                "verify", "--catalog", str(FIXTURE), "--denylist", str(deny),
                "--proposals", str(rows), "--out", str(out), "--timeout", "3",
            )
            self.assertEqual(code, 0, stderr)
            verdicts = json.loads((out / cv.SUMMARY_FILENAME).read_text())["verdicts"]
        self.assertEqual((verdicts[cv.VERDICT_PARSE_ERROR], verdicts[cv.VERDICT_DENYLISTED]), (1, 1))

    def test_direct_entry_point_runs_as_a_script(self):
        done = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
            [sys.executable, str(REPO / "pipelines" / "task_gate_cli.py"), "verify", "--help"],
            capture_output=True, text=True, timeout=60, check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("--denylist", done.stdout)
        self.assertIn("config/eval-exclusion/", done.stdout)


class ImportTwins(unittest.TestCase):
    SCRIPT = (
        "import sys\nsys.path[:0] = {paths!r}\n"
        "{imports}\n"
        "import task_gate.gate as flat, pipelines.task_gate.gate as packaged\n"
        "import task_gate.vocabulary as fv, pipelines.task_gate.vocabulary as pv\n"
        "print(flat is packaged and fv.GateRefusal is pv.GateRefusal)\n"
    )

    def spawn(self, imports):
        script = self.SCRIPT.format(paths=[str(REPO), str(REPO / "pipelines")], imports=imports)
        done = subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit  # nosec B603
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=60, check=False,
            cwd=tempfile.gettempdir(),
        )
        self.assertEqual(done.stdout.strip(), "True", done.stderr)

    def test_both_spellings_are_one_object_in_either_order(self):
        self.spawn("import task_gate.cli")
        self.spawn("import pipelines.task_gate.cli")


if __name__ == "__main__":
    unittest.main()
