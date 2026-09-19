"""A completed protocol response cannot authenticate pipes that never reached EOF."""

import io
import itertools
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
from oracle_grounded import oracles


def inline_thread(*, target, args=(), **_options):
    """Run controlled I/O schedules without wall-clock races between readers."""
    return SimpleNamespace(
        start=lambda: target(*args), join=lambda **_kwargs: None, is_alive=lambda: False,
    )


class OracleProtocolDeadlineTests(unittest.TestCase):
    def test_complete_stdout_with_unclosed_stderr_is_always_a_timeout(self):
        response = json.dumps({
            "protocol": "sf-oracle/1", "runtime_version": "fixture-1",
            "runtime_commit": "a" * 40, "measured": {"ok": True},
            "units": {"ok": "unit"},
        }).encode()
        for expired_before_select in (False, True):
            with self.subTest(expired_before_select=expired_before_select):
                self._assert_stderr_timeout(response, expired_before_select)

    def _assert_stderr_timeout(self, response, expired_before_select):
        process = SimpleNamespace(
            stdin=io.BytesIO(), stdout=mock.Mock(), stderr=mock.Mock(),
            pid=12345, poll=mock.Mock(return_value=None),
            wait=mock.Mock(return_value=0), kill=mock.Mock(),
        )
        process.stdout.fileno.return_value = 101
        process.stderr.fileno.return_value = 102
        clock = itertools.chain((0, 0, 0), itertools.repeat(2 if expired_before_select else 0))

        def readiness(readers, _writers, _errors, _timeout):
            return (readers if readers == [101] else [], [], [])

        with (
            mock.patch.object(oracles.subprocess, "Popen", return_value=process),
            mock.patch.object(oracles.threading, "Thread", side_effect=inline_thread),
            mock.patch.object(oracles.time, "monotonic", side_effect=lambda: next(clock)),
            mock.patch.object(oracles.select, "select", side_effect=readiness),
            mock.patch.object(oracles.os, "read", side_effect=[response, b""]),
            mock.patch.object(oracles.os, "killpg") as kill_group,
            mock.patch.object(oracles.os, "dup2"),
        ):
            with self.assertRaisesRegex(oracles.OracleError, "timed out"):
                oracles._run_protocol_command(["fixture-command"], b"{}", 1, "fixture-runtime")
        kill_group.assert_called_once_with(process.pid, oracles.signal.SIGKILL)
        self.assertEqual(process.wait.call_count, 2)


if __name__ == "__main__":
    unittest.main()
