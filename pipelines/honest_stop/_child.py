"""Child interpreter for the acceptance gate.

Started as ``python -P -s -B -X utf8 _child.py WORKDIR`` with ``PYTHONPATH`` set
to ``pipelines/`` and a scrubbed environment. It imports this package itself, so
a patch in the parent process does not apply.
"""

from __future__ import annotations

import sys
from pathlib import Path

from honest_stop._contract import dumps_exact_json, load_strict_json
from honest_stop.measure import judge
from honest_stop.vocabulary import GATE_MARKER, GATE_PROTOCOL, MAX_RECORD_BYTES


def _emit(report: dict) -> None:
    body = {"protocol": GATE_PROTOCOL, **report}
    sys.stdout.write(GATE_MARKER + dumps_exact_json(body) + "\n")
    sys.stdout.flush()


def _reject(code: str) -> None:
    _emit(
        {
            "accepted": False,
            "code": code,
            "measured_blocker": None,
            "counterfactual_holds": None,
        }
    )


def main(argv: list[str]) -> int:
    """Judge ``WORKDIR/record.json`` and print one report line."""

    work = Path(argv[1])
    payload = (work / "record.json").read_bytes()
    if len(payload) > MAX_RECORD_BYTES:
        _reject("record.too_large")
        return 0
    try:
        record = load_strict_json(payload.decode("utf-8"))
    except ValueError, RecursionError:
        _reject("record.json")
        return 0
    _emit(judge(record))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
