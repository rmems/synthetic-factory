#!/usr/bin/env python3
"""Take over abandoned r2631, then frontier → reserve --expected 2 → mill → publish.

Never steal a live reservation. Never rewrite published raw. Never sandbox-refusal hop.
Loops until mill bank exhausts or 6h.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
TXN = REPO / "pipelines/round_txn.py"
MILL = Path("/tmp/dpr_mill_r2631.py")
DPR = REPO / "outputs/raw/2026-08-19-agentic/data-pipeline-repair-factory"
AGENTIC = REPO / "outputs/raw/2026-08-19-agentic"
ORPHAN = 2631
ORPHAN_TOKEN = "66f59864388f45fdb32f3168084d78d7"
SKIP_HOP = {"sandbox-refusal-factory", "data-pipeline-repair-factory"}


def run(args, check=True):
    proc = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"cmd failed {args}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def frontier(factory: Path) -> dict:
    return json.loads(run([sys.executable, str(TXN), "frontier", str(factory)]).stdout)


def reserved_here(factory: Path, rnd: int) -> bool:
    return (factory / f"ROUND-r{rnd:02d}.reserved.json").exists()


def complete_here(factory: Path, rnd: int) -> bool:
    return (factory / f"ROUND-r{rnd:02d}.complete.json").exists()


def mill_into(rnd: int, staging: Path) -> dict:
    out = run(
        [sys.executable, str(MILL), "--round", str(rnd), "--staging", str(staging)]
    )
    return json.loads(out.stdout)


def publish(rnd: int, token: str) -> dict:
    return json.loads(
        run(
            [
                sys.executable,
                str(TXN),
                "publish",
                str(DPR),
                "--round",
                str(rnd),
                "--token",
                token,
            ]
        ).stdout
    )


def abort(rnd: int, token: str) -> None:
    run(
        [
            sys.executable,
            str(TXN),
            "abort",
            str(DPR),
            "--round",
            str(rnd),
            "--token",
            token,
        ],
        check=False,
    )


def takeover_orphan() -> dict | None:
    rpath = DPR / f"ROUND-r{ORPHAN:02d}.reserved.json"
    if not rpath.exists() or complete_here(DPR, ORPHAN):
        return None
    res = json.loads(rpath.read_text())
    token = res.get("token")
    staging = Path(res.get("staging_dir") or "")
    if token != ORPHAN_TOKEN:
        print(
            json.dumps(
                {
                    "skip_orphan": ORPHAN,
                    "reason": "token mismatch; another writer holds it",
                    "token": token,
                }
            ),
            flush=True,
        )
        return None
    if not staging.is_dir():
        print(json.dumps({"skip_orphan": ORPHAN, "reason": "staging missing"}), flush=True)
        return None
    try:
        info = mill_into(ORPHAN, staging)
        pub = publish(ORPHAN, token)
    except Exception as exc:
        print(
            json.dumps({"orphan_failed": ORPHAN, "error": str(exc)[:800]}),
            flush=True,
        )
        return None
    rec = {
        "factory": DPR.name,
        "round": ORPHAN,
        "ids": info["ids"],
        "records": pub.get("records"),
        "orphan": True,
    }
    print(json.dumps({"published": rec}), flush=True)
    return rec


def mill_one(rnd: int) -> dict | None:
    if reserved_here(DPR, rnd):
        return None
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(DPR),
            "--round",
            str(rnd),
            "--expected",
            "2",
        ],
        check=False,
    )
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").splitlines()[-1:] or [""]
        print(
            json.dumps({"skip": rnd, "reason": msg[0][:240]}),
            flush=True,
        )
        return None
    res = json.loads(proc.stdout)
    token = res["token"]
    staging = Path(res["staging_dir"])
    try:
        info = mill_into(rnd, staging)
        pub = publish(rnd, token)
    except Exception as exc:
        abort(rnd, token)
        print(
            json.dumps({"failed": rnd, "error": str(exc)[:800]}),
            flush=True,
        )
        return None
    rec = {
        "factory": DPR.name,
        "round": rnd,
        "ids": info["ids"],
        "records": pub.get("records"),
    }
    print(json.dumps({"published": rec}), flush=True)
    return rec


def hop_target() -> tuple[str, int] | None:
    if not AGENTIC.is_dir():
        return None
    for child in sorted(p for p in AGENTIC.iterdir() if p.is_dir()):
        if child.name in SKIP_HOP:
            continue
        try:
            st = frontier(child)
        except Exception:
            continue
        rnd = st.get("next_round")
        if not isinstance(rnd, int):
            continue
        if reserved_here(child, rnd):
            continue
        return child.name, rnd
    return None


def main():
    published = []
    hops = []
    started = time.time()
    one = takeover_orphan()
    if one:
        published.append(one)
    consecutive_skip = 0
    while (time.time() - started) < 6 * 3600:
        st = frontier(DPR)
        rnd = st["next_round"]
        if reserved_here(DPR, rnd) and not complete_here(DPR, rnd):
            hop = hop_target()
            hops.append({"dpr_reserved": rnd, "hop": hop})
            print(
                json.dumps({"blocked": rnd, "reason": "dpr reserved", "hop": hop}),
                flush=True,
            )
            consecutive_skip += 1
            if consecutive_skip >= 80:
                print(json.dumps({"stop": "reserved too long", "next": rnd}), flush=True)
                break
            time.sleep(2)
            continue
        one = mill_one(rnd)
        if one:
            published.append(one)
            consecutive_skip = 0
            continue
        consecutive_skip += 1
        if consecutive_skip >= 40:
            print(
                json.dumps(
                    {
                        "stop": "skip loop",
                        "next": rnd,
                        "published_n": len(published),
                    }
                ),
                flush=True,
            )
            break
        time.sleep(2)
    print(
        json.dumps(
            {
                "done": True,
                "published_n": len(published),
                "published": published,
                "hops": hops,
                "elapsed_s": int(time.time() - started),
            }
        )
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
