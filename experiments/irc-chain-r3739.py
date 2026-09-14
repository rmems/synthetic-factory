#!/usr/bin/env python3
"""Wait for Wave-39 chain, then start Wave-40. Never hop to sandbox-refusal."""
from __future__ import annotations
import json, os, signal, subprocess, sys, time
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

PID = int(sys.argv[1]) if len(sys.argv) > 1 else None
LOG39 = Path("/tmp/irc_loop_r3699.log")
LOG40 = Path("/tmp/irc_loop_r3739.log")
MILL40 = Path("/tmp/irc_mill_r3739.py")
LOOP40 = Path("/tmp/irc_loop_r3739.py")


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def main() -> int:
    if PID:
        while alive(PID):
            time.sleep(12)
    text = LOG39.read_text() if LOG39.exists() else ""
    if '"reserve_failed"' in text:
        print(json.dumps({"chain40": "stop", "reason": "reserve_failed"}), flush=True)
        return 2
    proc = subprocess.run([sys.executable, str(MILL40)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(json.dumps({"chain40": "mill_fail", "stderr": proc.stderr[-2000:]}), flush=True)
        return 3
    print(proc.stdout.strip(), flush=True)
    with LOG40.open("w") as fh:
        rc = subprocess.call(
            [sys.executable, "-u", str(LOOP40)],
            stdout=fh,
            stderr=subprocess.STDOUT,
        )
    print(json.dumps({"chain40": "loop40", "rc": rc}), flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
