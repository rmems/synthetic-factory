#!/usr/bin/env python3
"""Reserve → mill → publish browser-tool-use-factory from r395 until catalog or quota dies."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
DIR = AGENTIC / "browser-tool-use-factory"
TXN = [sys.executable, str(ROOT / "pipelines/round_txn.py")]
MILL_PATH = ROOT / "experiments/brw-mill-r395.py"
MILL = [sys.executable, str(MILL_PATH)]
_spec = importlib.util.spec_from_file_location("brw_mill_r395", MILL_PATH)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def frontier(factory: Path) -> dict:
    rc, out = run(TXN + ["frontier", str(factory)])
    if rc != 0:
        raise SystemExit(f"frontier failed:\n{out}")
    return json.loads(out[out.find("{") :])


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    if list(factory.glob("ROUND-r*.reserved.json")):
        return True
    if list(factory.glob("ROUND-r*.publishing.json")):
        return True
    return False


def catalog_last() -> int:
    return _mill.CATALOG_FIRST + len(_mill.PAIRS) - 1


def hop_target() -> Path | None:
    for child in sorted(AGENTIC.iterdir()):
        if not child.is_dir() or child.name == DIR.name:
            continue
        if child.name == "sandbox-refusal-factory" and (reserved(child, frontier(child)["next_round"]) or writing(child)):
            continue
        nxt = frontier(child)["next_round"]
        if not reserved(child, nxt):
            return child
    return None


def main() -> int:
    published: list[int] = []
    while True:
        status = frontier(DIR)
        nxt = status["next_round"]
        last = catalog_last()
        if nxt > last:
            print(json.dumps({"stop": "catalog_exhausted", "next_round": nxt, "published": published}))
            return 0
        if reserved(DIR, nxt):
            hop = hop_target()
            print(json.dumps({"stop": "browser_reserved", "round": nxt, "hop": None if hop is None else hop.name, "published": published}))
            return 2
        rc, out = run(TXN + ["reserve", str(DIR), "--round", str(nxt), "--expected", "2"])
        if rc != 0:
            print(json.dumps({"stop": "reserve_failed", "round": nxt, "out": out[-2000:], "published": published}))
            return 2
        payload = json.loads(out[out.find("{") :])
        token = payload["token"]
        stage = payload["staging_dir"]
        print(f"RESERVED r{nxt} {token[:8]} {stage}", flush=True)
        try:
            eps, notes = _mill.build_round(nxt)
            _mill._m.write_stage(Path(stage), nxt, eps, notes)
            print(json.dumps({"round": nxt, "ids": [e["id"] for e in eps]}), flush=True)
        except Exception as exc:
            run(TXN + ["abort", str(DIR), "--round", str(nxt), "--token", token])
            print(json.dumps({"stop": "mill_failed", "round": nxt, "out": str(exc)[-2000:], "published": published}))
            return 3
        rc, pout = run(TXN + ["publish", str(DIR), "--round", str(nxt), "--token", token])
        if rc != 0:
            print(json.dumps({"stop": "publish_failed", "round": nxt, "out": pout[-4000:], "published": published}))
            return 4
        spec = _mill.spec_for_round(nxt)
        batch = DIR / f"batch-r{nxt:02d}.jsonl"
        eps = [json.loads(line) for line in batch.read_text().splitlines() if line.strip()]
        _mill.append_used(eps, spec)
        published.append(nxt)
        print(f"PUBLISHED r{nxt}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
