#!/usr/bin/env python3
"""Chain DBC unique-pair loops after the live r1125 catalog.

Runs remaining catalogs in order until a loop fails or quota/reservation dies.
Does not steal a reserved seat. Never hops to sandbox-refusal.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOOPS = [
    ROOT / "experiments" / "dbc-loop-r1173.py",
    ROOT / "experiments" / "dbc-loop-r1221.py",
    ROOT / "experiments" / "dbc-loop-r1269.py",
    ROOT / "experiments" / "dbc-loop-r1317.py",
    ROOT / "experiments" / "dbc-loop-r1365.py",
]


def main() -> int:
    for loop in LOOPS:
        if not loop.exists():
            print(f"missing {loop}", flush=True)
            return 2
        print(f"+ {loop.name}", flush=True)
        proc = subprocess.run([sys.executable, str(loop)], cwd=ROOT)
        if proc.returncode != 0:
            print(f"{loop.name} exited {proc.returncode}", flush=True)
            return proc.returncode
        print(f"{loop.name} exhausted/ok", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
