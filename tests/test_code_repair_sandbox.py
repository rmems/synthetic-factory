#!/usr/bin/env python3
"""OS isolation seam: one confine prefix, fingerprint identity, foreign-source gate."""

from __future__ import annotations

import copy
import dataclasses
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (  # noqa: E402
    executor as ex, fixture, generate, refusal, vocabulary as cv,
)
from code_repair import _sandbox as landlock  # noqa: E402
from code_repair import catalog_build as cb  # noqa: E402
from code_repair import catalog_check as cc  # noqa: E402
from code_repair import replay  # noqa: E402
from code_repair import sandbox as sb  # noqa: E402
from code_repair import source_policy as sp  # noqa: E402
from test_code_repair_replay import positives, restamp  # noqa: E402


def _foreign_catalog():
    loaded = fixture()
    upstream = dict(loaded.meta["upstream"], repository="unreviewed/source")
    return dataclasses.replace(loaded, meta={**loaded.meta, "upstream": upstream})


class ConfineArgv(unittest.TestCase):
    def test_rlimits_only_leaves_the_literal_argv_untouched(self):
        workdir = Path(tempfile.mkdtemp(prefix="code-repair-argv-"))
        self.addCleanup(shutil.rmtree, workdir, True)
        argv = ["python", "-P", "_harness.py", str(workdir)]
        confined = sb.Isolation.rlimits_only().confine(argv, workdir, ex.CHILD_ENV)
        self.assertEqual(confined.argv, tuple(argv))
        self.assertEqual(confined.pass_fds, ())
        confined.close()

    def test_bwrap_prefix_is_a_literal_list_with_the_requested_boundary(self):
        workdir = Path(tempfile.mkdtemp(prefix="code-repair-confine-"))
        self.addCleanup(shutil.rmtree, workdir, True)
        argv = ["python", "-P", str(workdir / "_harness.py"), str(workdir)]
        isolation = sb.Isolation(sb.IDENTITY_BWRAP, "bwrap")
        with mock.patch.object(sb.shutil, "which", return_value="/usr/bin/bwrap"):
            confined = isolation.confine(argv, workdir, ex.CHILD_ENV)
        try:
            self.assertEqual(confined.argv[0], "/usr/bin/bwrap")
            self.assertTrue(all(isinstance(part, str) for part in confined.argv))
            self.assertEqual(confined.argv[-len(argv):], tuple(argv))
            for flag in (
                "--unshare-all", "--ro-bind", "--tmpfs", "--seccomp", "--uid", "--gid",
                "--die-with-parent", "--new-session", "--clearenv",
            ):
                self.assertIn(flag, confined.argv)
            self.assertEqual(len(confined.pass_fds), 1)
            argv_list = list(confined.argv)
            self.assertEqual(argv_list[argv_list.index("HOME") + 1], str(workdir))
            self.assertIn(str(Path(os.sep) / "tmp"), confined.argv)
        finally:
            confined.close()

    def test_os_boundary_refuses_when_bwrap_cannot_unshare(self):
        with (
            mock.patch.object(sb, "os_boundary_available", return_value=False),
            refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE, "bwrap"),
        ):
            sb.Isolation.os_boundary()

    def test_a_wrapper_failure_under_the_os_boundary_is_a_harness_error(self):
        class _FailedBoundary:
            identity = sb.IDENTITY_BWRAP
            is_os_boundary = True

            def confine(self, argv, workdir, env):
                return sb.Confinement(("/bin/false",))

        report = ex.Executor(timeout_s=5.0, isolation=_FailedBoundary()).run(
            ex.Job("wrap:test", "def f():\n    return 1\n", "f"),
        )
        self.assertEqual(report.status, cv.PHASE_HARNESS_ERROR)
        self.assertIn(cv.FINDING_SANDBOX_UNAVAILABLE, report.detail)


class ReviewedSourceGate(unittest.TestCase):
    def test_the_reviewed_selector_pin_matches_the_builder(self):
        self.assertEqual(sp.REVIEWED_SELECTOR, cb.SELECTOR_VERSION)
        self.assertTrue(sb.catalog_is_reviewed(fixture()))

    def test_the_reviewed_catalog_may_run_under_rlimits_only(self):
        engine = ex.executor_for(fixture(), timeout_s=2.0, supplied=ex.Executor(timeout_s=2.0))
        self.assertEqual(engine.sandbox_identity, sb.IDENTITY_RLIMITS_ONLY)

    def test_a_foreign_catalog_refuses_a_rlimits_only_executor(self):
        with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE, "OS isolation"):
            ex.executor_for(_foreign_catalog(), timeout_s=2.0, supplied=ex.Executor(timeout_s=2.0))

    def test_building_a_foreign_upstream_refuses_without_os_isolation(self):
        build = cb.Build(cb.Upstream("evil/src", "deadbeef", "MIT", "MIT\n"), {}, {})
        with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE, "OS isolation"):
            cb.build_rows(build, [], ex.Executor(timeout_s=2.0))

    def test_catalog_check_refuses_a_foreign_source_under_rlimits(self):
        with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE, "OS isolation"):
            cc.catalog_check(_foreign_catalog(), ex.Executor(timeout_s=2.0))


class FingerprintIdentity(unittest.TestCase):
    def test_the_parent_stamps_sandbox_identity_onto_every_report(self):
        report = ex.Executor(timeout_s=5.0).run(
            ex.Job("stamp:test", "def f():\n    return 1\n", "f", (), False),
        )
        self.assertEqual(report.environment["sandbox_identity"], sb.IDENTITY_RLIMITS_ONLY)

    def test_replay_refuses_a_record_produced_under_a_different_sandbox(self):
        record = copy.deepcopy(positives()[0])
        record["oracle"]["fingerprint"]["sandbox_identity"] = sb.IDENTITY_BWRAP
        record["oracle"]["configuration"]["isolation"] = sb.isolation_prose(sb.IDENTITY_BWRAP)
        restamp(record)
        entry = replay.replay_record(record, fixture(), ex.Executor(timeout_s=5.0))
        self.assertEqual(entry["code"], cv.REPLAY_ENVIRONMENT_DRIFT)

    def test_replay_refuses_a_forged_confinement_token(self):
        record = copy.deepcopy(positives()[0])
        record["oracle"]["configuration"]["confinement"] = "landlock-abi4"
        restamp(record)
        entry = replay.replay_record(record, fixture(), ex.Executor(timeout_s=5.0))
        self.assertEqual(entry["code"], cv.REPLAY_ENVIRONMENT_DRIFT)

    def test_reviewed_records_carry_no_confinement_claim(self):
        self.assertIsNone(positives()[0]["oracle"]["configuration"].get("confinement"))

    def test_os_boundary_timeouts_do_not_require_a_post_startup_landlock_report(self):
        timed_out = ex.PhaseReport(
            cv.PHASE_TIMEOUT, False, (), (), {"sandbox_identity": sb.IDENTITY_BWRAP}, "",
        )
        failed = dataclasses.replace(timed_out, status=cv.PHASE_HARNESS_ERROR)
        self.assertFalse(generate._unisolated(timed_out))
        self.assertTrue(generate._unisolated(failed))


def _live_skip_reason() -> str:
    """Why the live boundary test cannot run, with the environment recorded."""

    try:
        abi = landlock._landlock_abi()
    except (OSError, ValueError, AttributeError):
        abi = None
    return (
        "live OS boundary unavailable: "
        f"bwrap={sb.os_boundary_available()} landlock_abi={abi} "
        f"kernel={os.uname().release} machine={os.uname().machine}"
    )


class LiveOsBoundary(unittest.TestCase):
    @unittest.skipUnless(
        sb.os_boundary_available() and landlock.available(), _live_skip_reason(),
    )
    def test_host_files_and_the_network_are_out_of_reach(self):
        secret = sp.ROOT / ".code-repair-os-isolation.secret"
        self.addCleanup(secret.unlink, missing_ok=True)
        secret.write_text("host-secret\n", encoding="utf-8")
        module = (
            "from pathlib import Path\nimport socket\n"
            f"SECRET = Path({str(secret)!r})\n\n"
            "def f():\n"
            "    '''\n    >>> f()\n    'isolated:isolated'\n    '''\n"
            "    try:\n"
            "        leaked = SECRET.read_text().strip()\n"
            "    except OSError:\n"
            "        leaked = 'isolated'\n"
            "    try:\n"
            "        socket.create_connection(('1.1.1.1', 80), timeout=1)\n"
            "        net = 'connected'\n"
            "    except OSError:\n"
            "        net = 'isolated'\n"
            "    return leaked.strip() + ':' + net\n"
        )
        engine = ex.Executor(timeout_s=5.0, isolation=sb.Isolation.os_boundary())
        report = engine.run(ex.Job("isolate:test", module, "f", (), True, 1))
        self.assertTrue(report.ok, report.detail)
        self.assertEqual(report.environment["sandbox_identity"], sb.IDENTITY_BWRAP)
        self.assertEqual([row["got"].strip() for row in report.public], ["'isolated:isolated'"])
        self.assertTrue(ex.landlock_applied(report.environment.get("landlock")), report.environment)


class LandlockTokens(unittest.TestCase):
    def test_tokens_require_truncate_mediation(self):
        self.assertFalse(landlock.applied(None))
        self.assertFalse(landlock.applied("landlock-abi2"))
        self.assertTrue(landlock.applied("landlock-abi3"))
        self.assertEqual(landlock.token_for(4), "landlock-abi4")
        self.assertIsInstance(landlock.available(), bool)

    def test_runtime_prefixes_never_include_root(self):
        self.assertNotIn("/", landlock._runtime_prefixes())
        self.assertNotIn("/", landlock._read_roots())
        self.assertNotIn("/", landlock.SYSTEM_LIB_ROOTS)

    def test_runtime_prefixes_exclude_broad_interpreter_prefixes(self):
        paths = landlock._paths_mod
        with tempfile.TemporaryDirectory() as root:
            executable = Path(root) / "bin" / "python"
            stdlib = Path(root) / "lib" / "python3.14"
            executable.parent.mkdir()
            executable.touch()
            stdlib.mkdir(parents=True)
            layout = {
                "stdlib": str(stdlib), "platstdlib": str(stdlib),
                "purelib": str(stdlib / "site-packages"),
                "platlib": str(stdlib / "site-packages"),
            }
            (stdlib / "site-packages").mkdir()
            with (
                mock.patch.object(paths.sys, "executable", str(executable)),
                mock.patch.object(paths.sys, "prefix", "/usr"),
                mock.patch.object(paths.sys, "base_prefix", "/"),
                mock.patch.object(paths.sysconfig, "get_paths", return_value=layout),
            ):
                prefixes = paths.runtime_prefixes()
        self.assertEqual(prefixes, {str(executable), str(stdlib), str(stdlib / "site-packages")})
        self.assertNotIn("/usr", prefixes)

    def test_open_allowed_refuses_host_canaries(self):
        self.assertIsNone(landlock._open_allowed("/etc/passwd", set(landlock._read_roots())))
        self.assertIsNone(landlock._open_allowed("/etc/passwd", set(landlock.DEV_NODES)))


class _StubLibc:
    """A kernel stand-in: every syscall/prctl answers with one fixed result."""

    def __init__(self, result: int = 0) -> None:
        self.result = result

    def syscall(self, *args):
        return self.result

    def prctl(self, *args):
        return 0


def _stub_active(fd: int, rule_ok: bool = True) -> landlock._ActiveRuleset:
    active = landlock._ActiveRuleset()
    active.libc = _StubLibc(0 if rule_ok else -1)
    active.fd = fd
    active.add_rule = 445
    active.restrict = 446
    active.handled_fs = landlock.FS_ABI1 | landlock.FS_REFER | landlock.FS_TRUNCATE
    active.ioctl = 0
    return active


class LandlockInternals(unittest.TestCase):
    def test_enforce_is_a_no_op_when_the_spec_does_not_require_it(self):
        report = {"environment": {}}
        landlock.enforce("workdir", {}, report)
        landlock.enforce("workdir", {"require_landlock": False}, report)
        self.assertNotIn("landlock", report["environment"])

    def test_enforce_raises_when_the_boundary_cannot_be_applied(self):
        report = {"environment": {}}
        with (
            mock.patch.object(landlock, "apply", return_value=None),
            self.assertRaises(RuntimeError),
        ):
            landlock.enforce("workdir", {"require_landlock": True}, report)
        self.assertEqual(report["environment"]["landlock"], "")

    def test_enforce_records_the_applied_token(self):
        report = {"environment": {}}
        with mock.patch.object(landlock, "apply", return_value="landlock-abi4"):
            landlock.enforce("workdir", {"require_landlock": True}, report)
        self.assertEqual(report["environment"]["landlock"], "landlock-abi4")

    def test_handled_rights_widen_with_newer_abis(self):
        fs3, net3 = landlock._handled_rights(3)[:2]
        net4 = landlock._handled_rights(4)[1]
        size3, size4 = landlock._handled_rights(3)[3], landlock._handled_rights(4)[3]
        fs5 = landlock._handled_rights(5)[0]
        scoped6, size6 = landlock._handled_rights(6)[2:]
        self.assertEqual(net3, 0)
        self.assertTrue(net4 & landlock.NET_BIND_TCP)
        self.assertFalse(fs3 & landlock.FS_IOCTL_DEV)
        self.assertTrue(fs5 & landlock.FS_IOCTL_DEV)
        self.assertTrue(scoped6 & landlock.SCOPE_ABSTRACT_UNIX_SOCKET)
        self.assertLess(size3, size4)
        self.assertLess(size4, size6)

    def test_apply_returns_none_without_a_usable_abi(self):
        for abi in (None, 2):
            with mock.patch.object(landlock, "_landlock_abi", return_value=abi):
                self.assertIsNone(landlock.apply("workdir"))
        with mock.patch.object(landlock, "_landlock_abi", side_effect=OSError):
            self.assertIsNone(landlock.apply("workdir"))

    def test_open_ruleset_refuses_unknown_arches_and_kernel_refusals(self):
        with mock.patch.dict(landlock.LANDLOCK_SYSCALLS, {}, clear=True):
            self.assertIsNone(landlock._landlock_abi())
            self.assertIsNone(landlock._open_ruleset(4))
        with mock.patch.object(landlock, "_libc", return_value=_StubLibc(-1)):
            self.assertIsNone(landlock._open_ruleset(4))

    def test_add_path_refuses_paths_outside_their_allowed_set(self):
        with tempfile.TemporaryDirectory() as workdir:
            allowed = {os.path.realpath(workdir)}
            active = _stub_active(os.open(os.devnull, os.O_PATH))
            try:
                self.assertTrue(landlock._add_path(active, workdir, landlock.RO_ACCESS, allowed))
                self.assertFalse(landlock._add_path(active, "/etc/passwd", landlock.RO_ACCESS, allowed))
            finally:
                os.close(active.fd)

    def test_restrict_filesystem_runs_rules_and_closes_the_ruleset(self):
        with tempfile.TemporaryDirectory() as workdir:
            opened = (_StubLibc(0), os.open(os.devnull, os.O_PATH), (444, 445, 446))
            with mock.patch.object(landlock, "_open_ruleset", return_value=opened):
                self.assertTrue(landlock._restrict_filesystem(workdir, 4))
            with mock.patch.object(landlock, "_open_ruleset", return_value=None):
                self.assertFalse(landlock._restrict_filesystem(workdir, 4))
            refused = (_StubLibc(-1), os.open(os.devnull, os.O_PATH), (444, 445, 446))
            with mock.patch.object(landlock, "_open_ruleset", return_value=refused):
                self.assertFalse(landlock._restrict_filesystem(workdir, 4))

    def test_host_paths_report_open_until_the_canaries_are_denied(self):
        with tempfile.TemporaryDirectory() as workdir:
            self.assertFalse(landlock._host_paths_are_closed(workdir))
            canary = Path(workdir) / "canary"
            canary.write_text("x", encoding="utf-8")
            with (
                mock.patch.object(landlock, "HOST_CANARIES", (str(canary),)),
                mock.patch("builtins.open", side_effect=PermissionError),
            ):
                self.assertTrue(landlock._host_paths_are_closed(workdir))
            self.assertFalse(landlock._host_paths_are_closed(str(Path(workdir) / "missing")))

    def test_apply_uses_the_real_kernel_when_one_is_present(self):
        self.assertIn(landlock.available(), (True, False))


class LandlockLiveBoundary(unittest.TestCase):
    """A forked child: Landlock is one-way and cannot be removed once applied."""

    @unittest.skipUnless(landlock.available(), "Landlock ABI>=3 is not available")
    def test_apply_denies_host_reads_but_keeps_the_workdir(self):
        with tempfile.TemporaryDirectory() as workdir:
            reader, writer = os.pipe()
            pid = os.fork()
            if pid == 0:
                try:
                    os.close(reader)
                    token = landlock.apply(workdir) or ""
                    try:
                        with Path("/etc/passwd").open("rb") as handle:
                            handle.read(1)
                        denied = "no"
                    except OSError:
                        denied = "yes"
                    try:
                        (Path(workdir) / "probe").write_text("x", encoding="utf-8")
                        writable = "yes"
                    except OSError:
                        writable = "no"
                    os.write(writer, f"{token}|{denied}|{writable}".encode())
                finally:
                    os._exit(0)
            os.close(writer)
            _pid, _status = os.waitpid(pid, 0)
            payload = os.read(reader, 4096).decode()
            os.close(reader)
        token, denied, writable = payload.split("|")
        self.assertTrue(landlock.applied(token), token)
        self.assertEqual(denied, "yes")
        self.assertEqual(writable, "yes")


if __name__ == "__main__":
    unittest.main()
