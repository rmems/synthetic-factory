#!/usr/bin/env python3
"""Loop rag-retrieval-debug-factory from live frontier until catalog or max_rounds.

Writes only via pipelines/round_txn.py reserve --expected 2 / publish
(invoked in-process by /tmp/rag_mill/mill.py --loop). Never steal a reservation.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

MILL = Path("/tmp/rag_mill/mill.py")
sys.argv = [
    str(MILL),
    "--loop",
    "--min-rounds",
    sys.argv[1] if len(sys.argv) > 1 else "1",
    "--max-rounds",
    sys.argv[2] if len(sys.argv) > 2 else "80",
]
runpy.run_path(str(MILL), run_name="__main__")
