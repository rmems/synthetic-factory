#!/usr/bin/env python3
"""Regression checks for the Grok 4.6 weekly restart launcher."""

import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "pipelines" / "restart_grok46_33.sh"


class RestartGrok46Tests(unittest.TestCase):
    def test_launcher_uses_private_identity_checked_worker_state(self):
        text = SCRIPT.read_text()

        self.assertIn('STATE_DIR="${XDG_STATE_HOME:-/home/raulmc/.local/state}/synthetic-factory-grok46"', text)
        self.assertIn('chmod 700 "$STATE_DIR"', text)
        self.assertIn("process_start_token()", text)
        self.assertIn('write_worker_state "$worker_pid"', text)
        self.assertIn('exec nohup flock "$LOCK"', text)
        self.assertNotIn("/tmp/grok46-restart-33", text)
        self.assertNotIn("--always-approve", text)
        self.assertIn('if ! "$ROOT/.claude/skills/run-synthetic-factory/driver.py" frontiers', text)
        self.assertIn("warning: frontier preflight failed; continuing weekly launch", text)
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


if __name__ == "__main__":
    unittest.main()
