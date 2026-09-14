#!/usr/bin/env python3
"""Prefer docker-build-cache r1125 mill; hop websocket-reconnect if DBC reserved.

Never steal a reservation. Never rewrite raw.
Never hop to sandbox-refusal when it is reserved or writing.
Keep looping until catalog/quota dies — do not exit after one batch.
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
DBC_MILL = ROOT / "experiments" / "dbc-mill-r1125.py"
WSR_MILL = ROOT / "experiments" / "wsr-mill-r73.py"
LEDGER = ROOT / "experiments" / ".dbc-used-slugs.txt"

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


DBC_M = load(DBC_MILL, "dbc_mill_r1125")


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


def hop_targets() -> list[str]:
    names: list[str] = []
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir() or path.name in SKIP_HOP or path == DBC:
            continue
        if writing(path):
            continue
        names.append(path.name)
    return names


def append_ledger(ids: list[str]) -> None:
    existing = LEDGER.read_text() if LEDGER.exists() else ""
    with LEDGER.open("a") as fh:
        for ident in ids:
            if ident and ident not in existing:
                fh.write(ident + "\n")


def publish_one(factory: Path, n: int, mill: Path, extra: list[str] | None = None) -> None:
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
    mill_args = [
        sys.executable,
        str(mill),
        "--round",
        str(n),
        "--staging",
        staging,
    ]
    if extra:
        mill_args.extend(extra)
    mill_proc = run(mill_args)
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
    try:
        mill_payload = json.loads(mill_proc.stdout.strip().splitlines()[-1])
        append_ledger(mill_payload.get("ids") or [])
    except (json.JSONDecodeError, IndexError, TypeError):
        pass


def hop_wsr() -> bool:
    if writing(WSR) or WSR.name in SKIP_HOP:
        return False
    n = frontier(WSR)
    if reserved(WSR, n) or writing(WSR):
        return False
    try:
        publish_one(WSR, n, WSR_MILL)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
        return False
    print(f"published hop websocket r{n}", flush=True)
    return True


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else len(DBC_M.PAIRS)
    deadline = time.time() + 6 * 60 * 60
    done = 0
    published: list[str] = []
    DBC_M.catalog_selfcheck()
    reserved_spins = 0
    print(
        json.dumps({"catalog": len(DBC_M.PAIRS), "max_rounds": max_rounds}),
        flush=True,
    )
    while done < max_rounds and time.time() < deadline:
        idx = DBC_M.next_free_idx()
        if idx is None:
            print("docker r1125 catalog exhausted", flush=True)
            break
        n = frontier(DBC)
        if reserved(DBC, n) or writing(DBC):
            reserved_spins += 1
            hops = hop_targets()
            print(
                json.dumps(
                    {
                        "docker_reserved": n,
                        "spin": reserved_spins,
                        "hop_candidates": hops[:12],
                        "skip": sorted(SKIP_HOP),
                    }
                ),
                flush=True,
            )
            if "websocket-reconnect-factory" in hops:
                if hop_wsr():
                    reserved_spins = 0
                    continue
            if reserved_spins >= 8:
                print("docker seat stayed reserved; stop without stealing", flush=True)
                break
            time.sleep(2)
            continue
        reserved_spins = 0
        try:
            publish_one(DBC, n, DBC_MILL, ["--idx", str(idx)])
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(DBC, n) or writing(DBC):
                print("docker reserved during reserve; hop/retry", flush=True)
                time.sleep(1)
                continue
            print("docker mill/publish failed without seat", flush=True)
            return 5
        done += 1
        published.append(f"dbc-r{n}")
        print(f"published docker r{n} ({done}/{max_rounds}) idx={idx}", flush=True)
    print(json.dumps({"published": done, "rounds": published}))
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
