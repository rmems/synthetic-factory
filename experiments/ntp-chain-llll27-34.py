#!/usr/bin/env python3
"""Chain NTP leftover mills 27-34. Stay on NTP. Never steal. Never hop sandbox-refusal."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")


def main() -> int:
    any_ok = False
    for n in range(27, 35):
        loop = ROOT / f"experiments/ntp-loop-unique-llll{n}.py"
        print(f"START mill{n}", flush=True)
        rc = subprocess.call(
            [sys.executable, "-u", str(loop)],
            cwd=str(ROOT),
        )
        print(f"END mill{n} rc={rc}", flush=True)
        if rc == 0:
            any_ok = True
    return 0 if any_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
