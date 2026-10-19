"""The sandboxed gate harness (#509): the code_repair OS boundary under the gate's protocol.

The kernel classes run only where bwrap and Landlock work; the refusal classes run everywhere,
and ``test_task_gate_sandboxed_report.py`` covers the plan, the sealed records, the judge and
the child in process. ``SandboxedRealHarness`` replays the whole ``RealHarness`` suite against
the new harness, so verdict semantics are the ones the subprocess harness already pins.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_task_gate_harness as base
from task_gate_test_support import (
    ADD, PROGRAMS, cv, gate, harness, proposal_for, refused, rules,
)
from code_repair import _sandbox
from task_gate import _executor_contract as ec
from task_gate import procedural, sandboxed

AVAILABLE = ec.sandbox.os_boundary_available() and _sandbox.available()
NEEDS_BWRAP = unittest.skipUnless(AVAILABLE, "bwrap/Landlock isolation is not available here")
KEY = bytes(range(32))
ATTESTED = (
    b"code-repair-limits-attestation/1 true\n"
    b"code-repair-landlock-attestation/1 landlock-abi7\n"
)


class FakeIsolation:
    """An OS-boundary-shaped isolation that runs argv as is: only for the refusal paths."""

    identity = ec.sandbox.IDENTITY_BWRAP
    is_os_boundary = True

    def __init__(self, argv):
        self.argv = argv

    def confine(self, _argv, _workdir, _env):
        return ec.sandbox.Confinement(tuple(self.argv))


class Refusals(unittest.TestCase):
    def test_unavailable_boundary_refuses_instead_of_falling_back(self):
        with mock.patch.object(ec.sandbox, "os_boundary_available", return_value=False):
            self.assertEqual(refused(sandboxed.SandboxedHarness, 5), cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_an_isolation_that_is_not_an_os_boundary_is_refused(self):
        weak = ec.sandbox.Isolation.rlimits_only()
        self.assertEqual(refused(sandboxed.SandboxedHarness, 5, None, weak),
                         cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_timeout_domain_is_validated(self):
        for bad in (0, -1, float("nan"), float("inf"), True, "3", cv.MAX_TIMEOUT_S + 1, 10**400):
            with self.subTest(bad=bad):
                self.assertEqual(refused(sandboxed.SandboxedHarness, bad, None, FakeIsolation([])),
                                 cv.REFUSE_TIMEOUT_DOMAIN)

    def test_unreadable_child_files_refuse(self):
        with mock.patch.object(Path, "read_bytes", side_effect=OSError("gone")):
            self.assertEqual(refused(sandboxed.SandboxedHarness, 5, None, FakeIsolation([])),
                             cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_a_run_whose_proofs_are_not_attested_refuses_rather_than_judging(self):
        for argv in ([sys.executable, "-c", "pass"],
                     [sys.executable, "-c", "print('code-repair-limits-attestation/1 true')"],
                     [sys.executable, "-c", "print('code-repair-limits-attestation/1 false')"]):
            with self.subTest(argv=argv[-1]):
                fake = sandboxed.SandboxedHarness(5, isolation=FakeIsolation(argv))
                self.assertEqual(refused(fake.run, ADD, "add"), cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_a_timeout_is_a_timeout_only_when_the_program_was_attested_to_run(self):
        hang = [sys.executable, "-c", "import time; time.sleep(30)"]
        unattested = sandboxed.SandboxedHarness(0.3, isolation=FakeIsolation(hang))
        self.assertEqual(refused(unattested.run, ADD, "add"), cv.REFUSE_HARNESS_UNAVAILABLE)
        script = (
            "import sys, time\nsys.stdout.write('code-repair-limits-attestation/1 true\\n"
            "code-repair-landlock-attestation/1 landlock-abi7\\n')\nsys.stdout.flush()\n"
            "time.sleep(30)"
        )
        attested = sandboxed.SandboxedHarness(
            0.5, isolation=FakeIsolation([sys.executable, "-c", script]),
        )
        self.assertEqual(attested.run(ADD, "add").outcome, cv.OUTCOME_TIMEOUT)

    def test_an_unstartable_sandbox_refuses(self):
        fake = sandboxed.SandboxedHarness(5, isolation=FakeIsolation(["/nonexistent/bwrap"]))
        self.assertEqual(refused(fake.run, ADD, "add"), cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_attestation_helper_accepts_only_both_proofs(self):
        sandboxed._require_attested(ATTESTED)
        for stdout in (b"", ATTESTED.split(b"\n")[0] + b"\n",
                       b"code-repair-limits-attestation/1 true\ncode-repair-landlock-attestation/1 none\n"):
            with self.subTest(stdout=stdout):
                self.assertEqual(refused(sandboxed._require_attested, stdout),
                                 cv.REFUSE_HARNESS_UNAVAILABLE)

    def test_cli_sandbox_flag_refuses_when_the_boundary_is_missing(self):
        from task_gate import cli

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            ec.sandbox, "os_boundary_available", return_value=False,
        ), contextlib.redirect_stderr(io.StringIO()) as err:
            code = cli.run([
                "procedural", "--catalog", str(base.FIXTURE), "--denylist", str(Path(tmp, "d")),
                "--seed", "1", "--count", "1", "--sandbox", "--out", str(Path(tmp, "out")),
            ])
        self.assertEqual(code, 2)
        self.assertIn(cv.REFUSE_HARNESS_UNAVAILABLE, err.getvalue())
        self.assertFalse(Path(tmp, "out").exists())


class Description(unittest.TestCase):
    def test_describe_records_which_harness_ran(self):
        described = sandboxed.SandboxedHarness(7, isolation=FakeIsolation([])).describe()
        self.assertEqual(
            (described["kind"], described["isolation"], described["timeout_s"]),
            ("sandboxed", ec.sandbox.IDENTITY_BWRAP, 7.0),
        )
        self.assertEqual(len(described["child_sha256"]), 64)
        self.assertEqual(harness.SubprocessHarness(3).describe()["kind"], "subprocess")


def forge_everywhere(then):
    """A program that writes a failing-looking report to every low descriptor at import."""

    report = json.dumps({"payload": json.dumps({"seq": 0, "body": {"kind": "end", "count": 1}}),
                         "mac": "00" * 32}) + "\n"
    return (
        "import os\nREPORT = " + repr(report) + "\n"
        "for fd in range(0, 128):\n"
        "    try:\n        os.lseek(fd, 0, 0)\n        os.write(fd, REPORT.encode())\n"
        "        os.ftruncate(fd, len(REPORT))\n    except OSError:\n        pass\n"
        + then + "def f():\n    '''\n    >>> f()\n    1\n    '''\n    return 1\n"
    )


# Forks at import and keeps rewriting the report so that the genuine pass reads as a failure:
# the old nonce-echo report's count, and a sealed record's base64 output ("1\n" -> "2\n").
POLLER = r"""
import os, sys
fd = int(sys.argv[4])
if os.fork() == 0:
    seen = b""
    while True:
        data = os.pread(fd, 1 << 20, 0)
        if data and data != seen:
            seen = data.replace(b'"failed": 0', b'"failed": 1').replace(b'data\\":\\"MQo=', b'data\\":\\"Mgo=')
            os.pwrite(fd, seen, 0)
"""
REWRITTEN = b'data\\":\\"Mgo='  # what the poller leaves in a report it reached


@NEEDS_BWRAP
class Kernel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = sandboxed.SandboxedHarness(timeout_s=5)

    def test_self_check_and_describe(self):
        self.sandbox.selfcheck()
        self.assertEqual(self.sandbox.describe()["isolation"], ec.sandbox.IDENTITY_BWRAP)

    def test_a_forged_report_on_any_inherited_fd_cannot_change_the_verdict(self):
        honest = harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0)
        self.assertEqual(self.sandbox.run(forge_everywhere(""), "f"), honest)
        crashed = self.sandbox.run(forge_everywhere("os._exit(0)\n"), "f")
        self.assertEqual((crashed.outcome, crashed.detail), (cv.OUTCOME_CRASHED, "report_seal"))
        forged_pass = forge_everywhere("").replace("return 1", "return 2")
        self.assertEqual(self.sandbox.run(forged_pass, "f").outcome, cv.OUTCOME_FAILED)

    def test_a_forked_poller_rewriting_the_report_is_a_crash_never_a_verdict(self):
        """The Blocks finding on #513: a poller that rewrites each record it sees.

        The poller races the child, so the report is captured as the judge sees it: at least
        one run must actually carry the rewrite, and every run that does is a crash.
        """

        runs = self.poller_runs(attempts=5)
        self.assertIn(REWRITTEN, runs[-1][1], "the poller never reached the report")
        for result, report in runs:
            expected = cv.OUTCOME_CRASHED if REWRITTEN in report else cv.OUTCOME_PASSED
            self.assertEqual(result.outcome, expected, result)

    def poller_runs(self, attempts):
        """``(result, report)`` per run of the poller, stopping at the first rewritten report."""

        reports = []
        judge = sandboxed.judged

        def capture(examples, body, key):
            reports.append(body)
            return judge(examples, body, key)

        with mock.patch.object(sandboxed, "judged", side_effect=capture):
            results = [self.sandbox.run(POLLER + base.probe("return 1", 1), "f")]
            while REWRITTEN not in reports[-1] and len(results) < attempts:
                results.append(self.sandbox.run(POLLER + base.probe("return 1", 1), "f"))
        return list(zip(results, reports, strict=True))

    def test_a_pass_cannot_be_forged_even_by_tampering_with_the_child(self):
        """The residual: a program can rebind the child's checker and seal what it likes.

        It still cannot pass, because the expected output is not in the sandbox to copy.
        """

        tamper = (
            "import sys\nrecorder = sys.modules['__main__']._Recorder\n"
            "def forged(self, want, got, flags):\n"
            "    self._channel.send(self._codec.observation('out', b'forged\\n'))\n"
            "    return True\n"
            "recorder.check_output = forged\n"
        )
        result = self.sandbox.run(tamper + base.probe("return 2", "e5f1c0a7"), "f")
        self.assertEqual(result, harness.HarnessResult(cv.OUTCOME_FAILED, 1, 1))

    def test_the_expected_output_never_reaches_the_sandbox(self):
        body = (
            "import os\nneedle = ('>' * 3 + ' f()').encode()\nfound = []\n"
            "for name in os.listdir('.'):\n    with open(name, 'rb') as handle:\n"
            "        if needle in handle.read():\n            found.append(name)\n"
            "return found, f.__doc__"
        )
        self.assertEqual(self.sandbox.run(base.probe(body, ([], "")), "f"),
                         harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0))

    def test_the_key_is_not_in_the_environment_any_workdir_file_or_stdin(self):
        body = (
            "import os\nneedles = (bytes(range(32)), bytes(range(32)).hex().encode())\n"
            "found = [k for k, v in os.environ.items() if any(n in v.encode() for n in needles)]\n"
            "for name in os.listdir('.'):\n    with open(name, 'rb') as handle:\n"
            "        data = handle.read()\n    if any(n in data for n in needles):\n"
            "        found.append(name)\nreturn found, os.read(0, 8)"
        )
        with mock.patch.object(sandboxed.secrets, "token_bytes", return_value=KEY):
            result = self.sandbox.run(base.probe(body, ([], b"")), "f")
        self.assertEqual(result.outcome, cv.OUTCOME_PASSED, result)

    def test_long_output_passes_and_only_the_run_budget_is_a_crash(self):
        """Blocks on #513: output past 4096 characters used to be judged a failure."""

        x200k = "x" * 200000
        long = f"def f():\n    '''\n    >>> print('x' * 200000)\n    {x200k}\n    '''\n"
        self.assertEqual(self.sandbox.run(long, "f"), harness.HarnessResult(cv.OUTCOME_PASSED, 1, 0))
        flood = "def f():\n    '''\n    >>> print('x' * 1100000)\n    1\n    '''\n"
        self.assertEqual(self.sandbox.run(flood, "f"),
                         harness.HarnessResult(cv.OUTCOME_CRASHED, detail="output_truncated"))

    def test_the_child_cannot_read_its_own_memory_through_proc(self):
        body = (
            "out = []\nfor path in ('/proc/self/mem', '/proc/self/maps', '/proc/self/environ'):\n"
            "    try:\n        open(path, 'rb').read(1)\n        out.append(path)\n"
            "    except OSError:\n        pass\nreturn out"
        )
        self.assertEqual(self.sandbox.run(base.probe(body, []), "f").outcome, cv.OUTCOME_PASSED)

    def test_network_is_denied_below_the_socket_module(self):
        body = (
            "import ctypes, socket, struct\nlibc = ctypes.CDLL(None, use_errno=True)\n"
            "addr = struct.pack('=HH4s8s', 2, socket.htons(80), bytes([1, 1, 1, 1]), b'')\n"
            "tcp = libc.syscall(41, 2, 1, 0)\n"
            "connect = (libc.syscall(42, tcp, addr, 16), ctypes.get_errno())\n"
            "udp = libc.syscall(41, 2, 2, 0)\n"
            "sendto = (libc.syscall(44, udp, b'x', 1, 0, addr, 16), ctypes.get_errno())\n"
            "return connect[0] == -1 and sendto[0] == -1, connect[1] == 1, sendto[1] in (101, 1)"
        )
        self.assertEqual(self.sandbox.run(base.probe(body, (True, True, True)), "f").outcome,
                         cv.OUTCOME_PASSED)

    def test_loopback_listening_is_denied_too(self):
        body = (
            "import socket\ntry:\n    s = socket.socket()\n    s.bind(('127.0.0.1', 0))\n"
            "    s.listen()\nexcept OSError:\n    return 'denied'\nreturn 'open'"
        )
        self.assertEqual(self.sandbox.run(base.probe(body, "denied"), "f").outcome, cv.OUTCOME_PASSED)

    def test_host_files_and_the_home_tree_are_not_readable(self):
        body = (
            "import os\nout = []\nfor path in ('/etc/passwd', os.path.expanduser('~/.bashrc'), "
            "'/root/.bash_history', '/proc/1/environ'):\n    try:\n        open(path, 'rb').read(1)\n"
            "        out.append(path)\n    except OSError:\n        pass\nreturn out"
        )
        self.assertEqual(self.sandbox.run(base.probe(body, []), "f").outcome, cv.OUTCOME_PASSED)

    def test_system_exit_and_interrupts_at_import_are_load_errors(self):
        for raised in ("SystemExit(3)", "KeyboardInterrupt()", "GeneratorExit()"):
            with self.subTest(raised=raised):
                text = f"raise {raised}\n" + base.probe("return 1", 1)
                self.assertEqual(self.sandbox.run(text, "f").outcome, cv.OUTCOME_LOAD_ERROR)

    def test_runaway_programs_are_cut_by_the_wall_clock(self):
        fast = sandboxed.SandboxedHarness(timeout_s=1)
        self.assertEqual(fast.run(base.probe("while True:\n    pass", 1), "f").outcome,
                         cv.OUTCOME_TIMEOUT)

    def test_a_kernel_killed_child_is_a_crash_not_a_refusal(self):
        text = "import os, signal\n" + base.probe("os.kill(os.getpid(), signal.SIGKILL)", 1)
        self.assertEqual(self.sandbox.run(text, "f").outcome, cv.OUTCOME_CRASHED)


@NEEDS_BWRAP
class SandboxedRealHarness(base.RealHarness):
    """Every ``RealHarness`` case, against the sandboxed harness."""

    @classmethod
    def setUpClass(cls):
        cls.harness = sandboxed.SandboxedHarness(timeout_s=5)

    def test_no_network_from_the_program(self):
        body = (
            "import socket\ntry:\n    socket.create_connection(('127.0.0.1', 9))\nexcept OSError:\n"
            "    return 'blocked'\nreturn 'open'"
        )
        self.assertEqual(self.harness.run(base.probe(body, "blocked"), "f").outcome, cv.OUTCOME_PASSED)

    def test_the_private_socket_module_cannot_be_imported_by_the_program(self):
        self.skipTest("the in-process _socket block is the subprocess harness's; here it is the kernel")


@NEEDS_BWRAP
class SandboxedEndToEnd(unittest.TestCase):
    def test_each_verdict_with_the_sandboxed_harness(self):
        loop = "return a + b"
        items = [
            proposal_for("a - b"), proposal_for("b + a"),
            proposal_for("while True:\n        pass", loop),
            proposal_for("a - b", program_id="prog-eval"), proposal_for("a *"),
            proposal_for("a - b", proposal_id="again"),
        ]
        machine = gate.Gate(PROGRAMS, rules(), sandboxed.SandboxedHarness(2))
        self.assertEqual([d.verdict for d in machine.run(items)], [
            cv.VERDICT_KEPT, cv.VERDICT_MUTANT_PASSES, cv.VERDICT_TIMEOUT, cv.VERDICT_DENYLISTED,
            cv.VERDICT_PARSE_ERROR, cv.VERDICT_DUPLICATE,
        ])

    def test_verdicts_match_the_subprocess_harness_on_the_procedural_fixture(self):
        catalog = procedural.load_catalog(base.FIXTURE)
        programs = procedural.programs_from_catalog(catalog)
        items = procedural.proposals_from_plan(catalog, seed=3, count=4)
        subprocess_rows = gate.Gate(programs, rules(), harness.SubprocessHarness(5)).run(items)
        sandboxed_rows = gate.Gate(programs, rules(), sandboxed.SandboxedHarness(5)).run(items)
        self.assertEqual([d.as_row() for d in sandboxed_rows], [d.as_row() for d in subprocess_rows])

    def test_summary_records_the_sandboxed_harness_and_the_cli_flag_selects_it(self):
        from task_gate import cli

        with tempfile.TemporaryDirectory() as tmp:
            deny = Path(tmp, "deny.txt")
            deny.write_text("eval-only-program\n")
            out = Path(tmp, "run")
            with contextlib.redirect_stdout(io.StringIO()):
                code = cli.run(["procedural", "--catalog", str(base.FIXTURE), "--denylist", str(deny),
                                "--seed", "3", "--count", "2", "--timeout", "5", "--sandbox",
                                "--out", str(out)])
            summary = json.loads((out / cv.SUMMARY_FILENAME).read_text())
        self.assertEqual(code, 0)
        self.assertEqual(summary["inputs"]["harness"]["kind"], "sandboxed")
        self.assertEqual(summary["inputs"]["harness"]["isolation"], ec.sandbox.IDENTITY_BWRAP)


if __name__ == "__main__":
    unittest.main()
