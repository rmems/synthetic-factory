#!/usr/bin/env python3
"""Wait for Wave-40 chain, then start Wave-41. Never hop to sandbox-refusal."""
from __future__ import annotations
import json, os, signal, subprocess, sys, time
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

PID = int(sys.argv[1]) if len(sys.argv) > 1 else None
LOG40 = Path("/tmp/irc_loop_r3739.log")
LOG41 = Path("/tmp/irc_loop_r3779.log")
MILL41 = Path("/tmp/irc_mill_r3779.py")
LOOP41 = Path("/tmp/irc_loop_r3779.py")


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
    text = LOG40.read_text() if LOG40.exists() else ""
    if '"reserve_failed"' in text:
        print(json.dumps({"chain41": "stop", "reason": "reserve_failed"}), flush=True)
        return 2
    proc = subprocess.run([sys.executable, str(MILL41)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(json.dumps({"chain41": "mill_fail", "stderr": proc.stderr[-2000:]}), flush=True)
        return 3
    print(proc.stdout.strip(), flush=True)
    with LOG41.open("w") as fh:
        rc = subprocess.call(
            [sys.executable, "-u", str(LOOP41)],
            stdout=fh,
            stderr=subprocess.STDOUT,
        )
    print(json.dumps({"chain41": "loop41", "rc": rc}), flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
