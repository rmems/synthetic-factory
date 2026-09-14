#!/usr/bin/env python3
"""Print diagnosis briefs for Session B. Never opens rejected JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

STAGE = Path("/tmp/ffpc-r28")
ROUND_TAG = "r28"
SECTIONS = (
    "Root cause",
    "Cascade effects",
    "Supervisor catch",
    "Repair sketch",
    "Target reward delta",
)


def section(text: str, heading: str, nxt: str | None) -> str:
    start = text.index(f"## {heading}")
    if nxt is None:
        return text[start:]
    end = text.index(f"## {nxt}")
    return text[start:end]


def main() -> int:
    stage = Path(sys.argv[1]) if len(sys.argv) > 1 else STAGE
    if not stage.is_dir():
        print(f"drop absent: {stage}")
        return 1
    for index in (1, 2, 3):
        path = stage / f"diagnosis-{index:02d}-{ROUND_TAG}.md"
        if not path.is_file():
            print(f"MISSING {path.name}")
            return 1
        text = path.read_text(encoding="utf-8")
        i = text.index("## Shared context")
        j = text.index("## Root cause")
        block = text[i:j]
        start = block.index("```json")
        rest = block[start + len("```json") :]
        end = rest.index("```")
        payload = json.loads(rest[:end].strip())
        st = payload["state"]
        pa = payload["proposed_action"]
        unit = (st.get("environment") or {}).get("unit", "")
        plant = unit.split(",")[0].strip() if unit else "?"
        print(f"=== {path.name} bytes={path.stat().st_size} ===")
        print(f"plant={plant}")
        print(f"domain={st.get('domain')}")
        print(f"sim_or_real={st.get('sim_or_real')}")
        print(f"timestamp_local={st.get('timestamp_local')}")
        print(f"proposed.actor={pa.get('actor')}")
        print(f"proposed.type={pa.get('type')}")
        print(f"proposed.summary={pa.get('summary')}")
        delta_block = section(text, "Target reward delta", None)
        d0 = delta_block.index("```json")
        drest = delta_block[d0 + len("```json") :]
        dend = drest.index("```")
        delta = json.loads(drest[:dend].strip())
        print(f"target_delta={json.dumps(delta, ensure_ascii=True)}")
        for heading, nxt in zip(SECTIONS, list(SECTIONS[1:]) + [None]):
            body = section(text, heading, nxt)
            prose = body.split("\n", 1)[-1].strip()
            if heading == "Target reward delta":
                continue
            print(f"--- {heading} ---")
            print(prose)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
