#!/usr/bin/env python3
"""Prefer docker-build-cache r598 mill; hop websocket-reconnect if docker reserved.

Never steal. Never rewrite raw. Never hop sandbox-refusal.
Keep looping until catalog/quota dies.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
DBC = AGENTIC / "docker-build-cache-factory"
WSR = AGENTIC / "websocket-reconnect-factory"
DBC_MILL = ROOT / "experiments" / "dbc-mill-r598.py"
WSR_MILL = ROOT / "experiments" / "wsr-mill-r73.py"

SKIP_HOP = {
    "sandbox-refusal-factory",
    "eval-harness-trajectory-factory",
}

import importlib.util


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


DBC_M = load(DBC_MILL, "dbc_mill_r598")
WSR_M = load(WSR_MILL, "wsr_mill_r73")


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    text = proc.stdout.strip()
    payload = json.loads(text[text.rfind("{") :])
    print(
        json.dumps(
            {
                "factory": payload.get("factory"),
                "next_round": payload.get("next_round"),
                "highest_flushed": payload.get("highest_flushed"),
            }
        ),
        flush=True,
    )
    return payload["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    return any(factory.glob("ROUND-r*.reserved.json"))


def publish_one(factory: Path, n: int, mill: Path, extra: list[str]) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            "2",
        ]
    )
    payload = json.loads(proc.stdout)
    print(proc.stdout, flush=True)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    mill_proc = run(
        [sys.executable, str(mill), "--round", str(n), "--staging", staging, *extra]
    )
    sys.stderr.write(mill_proc.stderr or "")
    print(mill_proc.stdout, flush=True)
    pub = run(
        [
            sys.executable,
            str(TXN),
            "publish",
            str(factory),
            "--round",
            str(n),
            "--token",
            token,
        ]
    )
    print(pub.stdout, flush=True)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 32
    deadline = time.time() + 70 * 60
    done = 0
    published: list[str] = []
    DBC_M.catalog_selfcheck()
    WSR_M.self_check()
    dbc_used: set[str] = set()
    wsr_used = WSR_M.harvest_used(WSR)
    print(
        json.dumps(
            {
                "dbc_catalog": len(DBC_M.PAIRS),
                "wsr_catalog": len(WSR_M.PAIRS),
                "max_rounds": max_rounds,
            }
        ),
        flush=True,
    )
    while done < max_rounds and time.time() < deadline:
        dn = frontier(DBC)
        if not reserved(DBC, dn) and not writing(DBC):
            idx = DBC_M.next_free_idx(dbc_used)
            if idx is not None:
                try:
                    publish_one(DBC, dn, DBC_MILL, ["--idx", str(idx)])
                except subprocess.CalledProcessError as exc:
                    print(exc.stdout, exc.stderr, flush=True)
                    if reserved(DBC, dn) or writing(DBC):
                        print("docker reserved during reserve; hop", flush=True)
                    else:
                        return 5
                else:
                    suc, leftp = DBC_M.PAIRS[idx]
                    dbc_used.add(suc["slug"])
                    dbc_used.add(leftp["slug"])
                    done += 1
                    published.append(f"dbc-r{dn}")
                    print(f"published docker r{dn} ({done}/{max_rounds})", flush=True)
                    continue
        wn = frontier(WSR)
        if reserved(WSR, wn) or writing(WSR) or WSR.name in SKIP_HOP:
            print(
                json.dumps(
                    {
                        "docker_reserved": dn,
                        "wsr_busy": wn,
                        "note": "never steal; never sandbox-refusal",
                    }
                ),
                flush=True,
            )
            time.sleep(2)
            continue
        idx = WSR_M.next_free_idx(wsr_used)
        if idx is None:
            print("wsr catalog exhausted", flush=True)
            break
        try:
            publish_one(WSR, wn, WSR_MILL, ["--idx", str(idx)])
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(WSR, wn) or writing(WSR):
                print("wsr reserved during reserve; retry", flush=True)
                time.sleep(1)
                continue
            print("wsr mill/publish failed without seat", flush=True)
            return 4
        okp, badp = WSR_M.PAIRS[idx]
        wsr_used.add(okp["slug"])
        wsr_used.add(badp["slug"])
        done += 1
        published.append(f"wsr-r{wn}")
        print(f"published wsr r{wn} ({done}/{max_rounds}) idx={idx}", flush=True)
    print(json.dumps({"published": done, "rounds": published}))
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
