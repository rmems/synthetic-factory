#!/usr/bin/env python3
"""Wait for Wave-37 chain, then start Wave-38. Never hop to sandbox-refusal."""
from __future__ import annotations
import json, os, signal, subprocess, sys, time
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

PID = int(sys.argv[1]) if len(sys.argv) > 1 else None
LOG37 = Path("/tmp/irc_loop_r3617.log")
LOG38 = Path("/tmp/irc_loop_r3657.log")
MILL38 = Path("/tmp/irc_mill_r3657.py")
LOOP38 = Path("/tmp/irc_loop_r3657.py")


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
    text = LOG37.read_text() if LOG37.exists() else ""
    if '"reserve_failed"' in text:
        print(json.dumps({"chain38": "stop", "reason": "reserve_failed"}), flush=True)
        return 2
    proc = subprocess.run([sys.executable, str(MILL38)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(json.dumps({"chain38": "mill_fail", "stderr": proc.stderr[-2000:]}), flush=True)
        return 3
    print(proc.stdout.strip(), flush=True)
    with LOG38.open("w") as fh:
        rc = subprocess.call(
            [sys.executable, "-u", str(LOOP38)],
            stdout=fh,
            stderr=subprocess.STDOUT,
        )
    print(json.dumps({"chain38": "loop38", "rc": rc}), flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
