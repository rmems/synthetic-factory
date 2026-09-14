#!/usr/bin/env python3
"""frontier → reserve --expected 2 → unique-llll32 mill → publish. Never steal."""
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
src = (ROOT / "experiments/ntp-loop-unique-llll3.py").read_text()
src = src.replace("ntp-mill-unique-llll3.py", "ntp-mill-unique-llll32.py")
ns: dict = {"__name__": "__main__"}
exec(compile(src, str(ROOT / "experiments/ntp-loop-unique-llll32.py"), "exec"), ns)
