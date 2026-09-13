"""Contracts for shared child-process lifecycle support."""

from __future__ import annotations

import multiprocessing
import time
import unittest

from tests.process_test_support import ProcessTimeout, spawned_process_exit_code


def _return_normally() -> None:
    return None


def _exit_with_status() -> None:
    raise SystemExit(7)


def _wait_for_termination() -> None:
    time.sleep(10)


class SpawnedProcessLifecycle(unittest.TestCase):
    def test_normal_child_is_joined_and_returns_zero(self):
        self.assertEqual(
            spawned_process_exit_code(
                _return_normally,
                timeout=ProcessTimeout(5.0, 1.0, "normal child timed out"),
            ),
            0,
        )

    def test_nonzero_child_exit_status_is_preserved(self):
        self.assertEqual(
            spawned_process_exit_code(
                _exit_with_status,
                timeout=ProcessTimeout(5.0, 1.0, "status child timed out"),
            ),
            7,
        )

    def test_timed_out_child_is_terminated_and_reaped(self):
        child_pids_before = {child.pid for child in multiprocessing.active_children()}

        with self.assertRaisesRegex(TimeoutError, "bounded child timed out"):
            spawned_process_exit_code(
                _wait_for_termination,
                timeout=ProcessTimeout(0.1, 1.0, "bounded child timed out"),
            )

        child_pids_after = {child.pid for child in multiprocessing.active_children()}
        self.assertEqual(child_pids_after, child_pids_before)


if __name__ == "__main__":
    unittest.main()
