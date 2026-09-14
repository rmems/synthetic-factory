#!/usr/bin/env python3
"""Wait for Wave-67–72 chain, then mill+loop Wave-73..78. Never hop to sandbox-refusal."""
from __future__ import annotations
import json, os, signal, subprocess, sys, time
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGHUP, signal.SIG_IGN)

PID = int(sys.argv[1]) if len(sys.argv) > 1 else None
PREV = Path("/tmp/irc_chain_r4441.log")
WAVES = (4561, 4581, 4601, 4621, 4641, 4661)


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
    text = PREV.read_text() if PREV.exists() else ""
    if '"reserve_failed"' in text or '"mill_fail"' in text:
        print(json.dumps({"chain73": "stop", "reason": "prev_failed"}), flush=True)
        return 2
    for base in WAVES:
        mill = Path(f"/tmp/irc_mill_r{base}.py")
        loop = Path(f"/tmp/irc_loop_r{base}.py")
        log = Path(f"/tmp/irc_loop_r{base}.log")
        proc = subprocess.run([sys.executable, str(mill)], capture_output=True, text=True)
        if proc.returncode != 0:
            print(json.dumps({"chain": "mill_fail", "base": base, "stderr": proc.stderr[-2000:]}), flush=True)
            return 3
        print(proc.stdout.strip(), flush=True)
        with log.open("w") as fh:
            rc = subprocess.call(
                [sys.executable, "-u", str(loop)],
                stdout=fh,
                stderr=subprocess.STDOUT,
            )
        ltxt = log.read_text() if log.exists() else ""
        if '"reserve_failed"' in ltxt:
            print(json.dumps({"chain": "stop", "reason": "reserve_failed", "base": base, "rc": rc}), flush=True)
            return 2
        print(json.dumps({"chain": "loop", "base": base, "rc": rc}), flush=True)
        if rc != 0:
            return rc
    print(json.dumps({"ok": True, "waves": list(WAVES)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
