#!/usr/bin/env python3
"""Wait for Wave-36 loop, then start Wave-37. Never hop to sandbox-refusal."""
from __future__ import annotations
import json, os, signal, subprocess, sys, time
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

PID = int(sys.argv[1]) if len(sys.argv) > 1 else None
LOG36 = Path("/tmp/irc_loop_r3577.log")
LOG37 = Path("/tmp/irc_loop_r3617.log")
MILL37 = Path("/tmp/irc_mill_r3617.py")
LOOP37 = Path("/tmp/irc_loop_r3617.py")


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
    text = LOG36.read_text() if LOG36.exists() else ""
    if '"reserve_failed"' in text:
        print(json.dumps({"chain": "stop", "reason": "reserve_failed"}), flush=True)
        return 2
    proc = subprocess.run([sys.executable, str(MILL37)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(json.dumps({"chain": "mill37_fail", "stderr": proc.stderr[-2000:]}), flush=True)
        return 3
    print(proc.stdout.strip(), flush=True)
    with LOG37.open("w") as fh:
        rc = subprocess.call(
            [sys.executable, "-u", str(LOOP37)],
            stdout=fh,
            stderr=subprocess.STDOUT,
        )
    print(json.dumps({"chain": "loop37", "rc": rc}), flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
