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
    executor as ex, fixture, refusal, vocabulary as cv,
)
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
        with mock.patch.object(sb, "os_boundary_available", return_value=False):
            with refusal(self, cv.FINDING_SANDBOX_UNAVAILABLE, "bwrap"):
                sb.Isolation.os_boundary()


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


class LiveOsBoundary(unittest.TestCase):
    @unittest.skipUnless(
        sb.os_boundary_available(), "bwrap user-namespace sandbox is not available",
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
            "    leaked = SECRET.read_text() if SECRET.is_file() else 'isolated'\n"
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


if __name__ == "__main__":
    unittest.main()
