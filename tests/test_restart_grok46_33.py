#!/usr/bin/env python3
"""Regression checks for the Grok 4.6 weekly restart launcher."""

import os
import subprocess
import re
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "pipelines" / "restart_grok46_33.sh"
PROMPT = REPO / "pipelines" / "restart_grok46_33.md"
CONTRACT = REPO / "prompts" / "_agentic-factory-contract.md"


class RestartGrok46Tests(unittest.TestCase):
    @staticmethod
    def write_executable(path, text):
        path.write_text(text)
        path.chmod(0o755)

    def test_launcher_uses_private_identity_checked_worker_state(self):
        text = SCRIPT.read_text()

        self.assertIn('STATE_HOME="${XDG_STATE_HOME:-/home/raulmc/.local/state}"', text)
        self.assertIn('STATE_DIR="$STATE_HOME/synthetic-factory-grok46"', text)
        self.assertIn("ensure_private_state_dir()", text)
        self.assertIn("ensure_state_home()", text)
        self.assertIn("ensure_private_state_file()", text)
        self.assertIn('ensure_private_state_file "$LOCK"', text)
        self.assertIn('chmod 700 "$STATE_DIR"', text)
        self.assertIn("process_start_token()", text)
        self.assertIn('write_worker_state "$worker_pid"', text)
        self.assertIn('WINDOW_FILE="$STATE_DIR/last-launch-window"', text)
        self.assertIn("write_launch_window()", text)
        self.assertIn("resolve_grok()", text)
        self.assertIn("missing or non-executable Grok command", text)
        self.assertLess(
            text.index("missing or non-executable Grok command"),
            text.index("weekly launch already consumed"),
        )
        self.assertIn('write_launch_window "$launch_window"', text)
        self.assertIn("weekly launch already consumed", text)
        self.assertIn('STARTUP_GRACE_SECONDS="${GROK_STARTUP_GRACE_SECONDS:-5}"', text)
        self.assertIn("tmux worker exited during startup", text)
        self.assertIn("nohup worker exited during startup", text)
        tmux_launch = text.index("tmux new-session")
        tmux_confirmed = text.index("tmux worker exited during startup")
        tmux_consumed = text.index('write_launch_window "$launch_window"', tmux_launch)
        self.assertLess(tmux_launch, tmux_confirmed)
        self.assertLess(tmux_confirmed, tmux_consumed)
        nohup_launch = text.index("exec nohup flock")
        nohup_confirmed = text.index("nohup worker exited during startup")
        nohup_consumed = text.index('write_launch_window "$launch_window"', nohup_launch)
        self.assertLess(nohup_launch, nohup_confirmed)
        self.assertLess(nohup_confirmed, nohup_consumed)
        self.assertIn('exec 9>>"$LOCK"', text)
        self.assertIn('exec nohup flock "$LOCK"', text)
        self.assertNotIn("/tmp/grok46-restart-33", text)
        self.assertNotIn("--always-approve", text)
        self.assertIn('if ! python3 "$ROOT/.claude/skills/run-synthetic-factory/driver.py" frontiers', text)
        self.assertIn("warning: frontier preflight failed; continuing weekly launch", text)
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_launcher_refuses_symlinked_state_paths_before_opening_them(self):
        for name in ("synthetic-factory-grok46", "launcher.lock"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                state_home = root / "state"
                state_home.mkdir()
                state_dir = state_home / "synthetic-factory-grok46"
                outside = root / "outside"
                outside.write_text("do not touch\n")
                if name == state_dir.name:
                    state_dir.symlink_to(outside)
                else:
                    state_dir.mkdir()
                    (state_dir / name).symlink_to(outside)

                result = subprocess.run(
                    ["bash", str(SCRIPT)],
                    env={**os.environ, "XDG_STATE_HOME": str(state_home)},
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 1)
                self.assertIn("unsafe launcher state path", result.stderr)
                self.assertEqual(outside.read_text(), "do not touch\n")

    def test_launcher_creates_missing_state_home_ancestors(self):
        with tempfile.TemporaryDirectory() as td:
            state_home = Path(td) / "missing" / "nested" / "state"
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                env={**os.environ, "XDG_STATE_HOME": str(state_home)},
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            state_dir = state_home / "synthetic-factory-grok46"
            self.assertTrue(state_dir.is_dir())
            self.assertTrue((state_dir / "launcher.lock").is_file())

    def test_failed_tmux_startup_does_not_consume_the_weekly_window(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            commands = root / "bin"
            commands.mkdir()
            self.write_executable(
                commands / "date",
                """#!/usr/bin/env bash
case "${1:-}" in
  +%u) printf '3\\n' ;;
  +%H) printf '07\\n' ;;
  +%M) printf '00\\n' ;;
  +%G-W%V) printf '2099-W01\\n' ;;
  *) printf '2099-01-07T07:00:00-06:00\\n' ;;
esac
""",
            )
            self.write_executable(commands / "python3", "#!/usr/bin/env bash\nexit 0\n")
            self.write_executable(
                commands / "tmux",
                """#!/usr/bin/env bash
if [[ "${1:-}" == "new-session" ]]; then
  exit 0
fi
exit 1
""",
            )
            grok = root / "grok"
            self.write_executable(grok, "#!/usr/bin/env bash\nexit 1\n")
            state_home = root / "state"

            result = subprocess.run(
                ["bash", str(SCRIPT)],
                env={
                    **os.environ,
                    "PATH": f"{commands}:{os.environ['PATH']}",
                    "XDG_STATE_HOME": str(state_home),
                    "GROK": str(grok),
                    "GROK_STARTUP_GRACE_SECONDS": "0",
                },
                capture_output=True,
                text=True,
                check=False,
            )

            window = state_home / "synthetic-factory-grok46" / "last-launch-window"
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(window.read_text(), "")
            log = (state_home / "synthetic-factory-grok46" / "restart.log").read_text()
            self.assertIn("tmux worker exited during startup", log)

    def test_prompt_honors_plateau_stops_and_uses_fresh_snapshots(self):
        text = PROMPT.read_text()
        contract = CONTRACT.read_text()

        self.assertIn("token-efficiency outputs/raw/2026-08-19-agentic --json", text)
        self.assertIn('"postreset-$(date +%Y%m%d-%H%M%S)"', text)
        self.assertIn("whose `early_stop` is `true`", text)
        self.assertIn("at most **r26**", text)
        self.assertIn("Stop after a successful r26", text)
        self.assertIn("read `prompts/_agentic-factory-contract.md`", text)
        self.assertIn("at most 33", text)
        self.assertNotIn("snapshot outputs/raw/2026-08-19-agentic postreset", text)
        slugs = re.findall(r"^\d+\. ([a-z0-9-]+) Q=", text, flags=re.MULTILINE)
        self.assertEqual(len(slugs), 33)
        for slug in slugs:
            self.assertIn(f"| {slug} |", contract, slug)


if __name__ == "__main__":
    unittest.main()
