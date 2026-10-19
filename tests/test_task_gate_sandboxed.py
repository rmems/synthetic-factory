"""The sandboxed gate harness (#509): the code_repair OS boundary under the gate's protocol.

The kernel classes run only where bwrap and Landlock work; the refusal and parsing classes run
everywhere. ``SandboxedRealHarness`` replays the whole ``RealHarness`` suite against the new
harness, so verdict semantics are the ones the subprocess harness already pins.
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
from task_gate import _executor_contract as ec
from task_gate import procedural, sandboxed

AVAILABLE = ec.sandbox.os_boundary_available() and ec.landlock.available()
NEEDS_BWRAP = unittest.skipUnless(AVAILABLE, "bwrap/Landlock isolation is not available here")
NONCE = "ab" * 32
GOOD_REPORT = {"protocol": cv.HARNESS_PROTOCOL, "outcome": "ran", "attempted": 2, "failed": 0,
               "detail": "", "nonce": NONCE}
ATTESTED = (
    b"code-repair-limits-attestation/1 true\n"
    b"code-repair-landlock-attestation/1 landlock-abi7\n"
)


def body_of(report):
    return json.dumps(report).encode()


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

    def test_a_non_ascii_or_surrogate_nonce_is_a_crash_not_an_exception(self):
        for echoed in ("caf\u00e9" * 16, "\ud800" * 64):
            with self.subTest(echoed=echoed):
                body = json.dumps({**GOOD_REPORT, "nonce": echoed}).encode()
                self.assertEqual(sandboxed._result_of_body(body, NONCE).detail, "report_nonce")

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


class ReportParsing(unittest.TestCase):
    def result(self, body):
        return sandboxed._result_of_body(body, NONCE)

    def test_a_report_echoing_the_nonce_is_read_like_any_protocol_report(self):
        self.assertEqual(self.result(body_of(GOOD_REPORT)), harness.HarnessResult(cv.OUTCOME_PASSED, 2, 0))
        failed = {**GOOD_REPORT, "failed": 1}
        self.assertEqual(self.result(body_of(failed)).outcome, cv.OUTCOME_FAILED)

    def test_anything_else_is_a_crash_and_never_a_verdict(self):
        wrong = {**GOOD_REPORT, "nonce": "cd" * 32}
        missing = {key: value for key, value in GOOD_REPORT.items() if key != "nonce"}
        cases = {
            "wrong nonce": body_of(wrong), "no nonce": body_of(missing),
            "numeric nonce": body_of({**GOOD_REPORT, "nonce": 5}), "empty": b"",
            "not json": b"{", "list": b"[]", "nan": b'{"nonce": NaN}',
            "duplicate keys": b'{"nonce": "a", "nonce": "' + NONCE.encode() + b'"}',
            "oversize": b" " * (harness.MAX_REPORT_BYTES + 1),
        }
        for name, body in cases.items():
            with self.subTest(name):
                self.assertEqual(self.result(body).outcome, cv.OUTCOME_CRASHED)

    def test_describe_records_which_harness_ran(self):
        described = sandboxed.SandboxedHarness(7, isolation=FakeIsolation([])).describe()
        self.assertEqual(
            (described["kind"], described["isolation"], described["timeout_s"]),
            ("sandboxed", ec.sandbox.IDENTITY_BWRAP, 7.0),
        )
        self.assertEqual(len(described["child_sha256"]), 64)
        self.assertEqual(harness.SubprocessHarness(3).describe()["kind"], "subprocess")


def forge_everywhere(then):
    """A program that writes a perfect-looking failing report to every low descriptor."""

    report = json.dumps({"protocol": cv.HARNESS_PROTOCOL, "outcome": "ran", "attempted": 1,
                         "failed": 1, "detail": "", "nonce": "guess"})
    return (
        "import os\nREPORT = " + repr(report) + "\n"
        "for fd in range(0, 128):\n"
        "    try:\n        os.lseek(fd, 0, 0)\n        os.write(fd, REPORT.encode())\n"
        "        os.ftruncate(fd, len(REPORT))\n    except OSError:\n        pass\n"
        + then + "def f():\n    '''\n    >>> f()\n    1\n    '''\n    return 1\n"
    )


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
        self.assertEqual((crashed.outcome, crashed.detail), (cv.OUTCOME_CRASHED, "report_nonce"))
        forged_pass = forge_everywhere("").replace("return 1", "return 2")
        self.assertEqual(self.sandbox.run(forged_pass, "f").outcome, cv.OUTCOME_FAILED)

    def test_the_nonce_is_not_in_the_environment_or_any_workdir_file(self):
        body = (
            "import os\nneedle = (%r * %d).encode()\nfound = [k for k, v in os.environ.items() "
            "if needle in v.encode()]\nfor name in os.listdir('.'):\n    if os.path.isfile(name):\n"
            "        with open(name, 'rb') as handle:\n            if needle in handle.read():\n"
            "                found.append(name)\nreturn found"
        ) % (NONCE[:2], len(NONCE) // 2)
        with mock.patch.object(sandboxed.secrets, "token_hex", return_value=NONCE):
            result = self.sandbox.run(base.probe(body, []), "f")
        self.assertEqual(result.outcome, cv.OUTCOME_PASSED, result)

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

    def test_stdin_does_not_give_the_nonce_back(self):
        body = "import os\nreturn os.read(0, 8)"
        self.assertEqual(self.sandbox.run(base.probe(body, b""), "f").outcome, cv.OUTCOME_PASSED)

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
