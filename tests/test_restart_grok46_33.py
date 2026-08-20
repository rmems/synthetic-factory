#!/usr/bin/env python3
"""Regression checks for the Grok 4.6 weekly restart launcher."""

import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "pipelines" / "restart_grok46_33.sh"


class RestartGrok46Tests(unittest.TestCase):
    def test_nohup_path_has_a_separate_liveness_guard(self):
        text = SCRIPT.read_text()

        self.assertIn("PID_FILE=/tmp/grok46-restart-33.pid", text)
        self.assertIn('kill -0 "$existing_pid"', text)
        self.assertIn('echo $! >"$PID_FILE"', text)
        self.assertNotIn('echo $! >"$LOCK"', text)
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


if __name__ == "__main__":
    unittest.main()
