#!/usr/bin/env python3
"""Reserve → mill → publish git-ops-recovery-factory until catalog, 12 rounds, or 40 minutes.

Hop secret-scan-remediation-factory when the git-ops seat is reserved.
Never steal. Never rewrite raw.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "gor-mill-r1044.py"
SSR_MILL = ROOT / "experiments" / "ssr-mill-r332.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "git-ops-recovery-factory"
HOP = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "secret-scan-remediation-factory"

import importlib.util

_spec = importlib.util.spec_from_file_location("gor_mill_r1044", MILL)
_mill = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mill)
CATALOG_LEN = len(_mill.PAIRS)

_ssr_spec = importlib.util.spec_from_file_location("ssr_mill_r332", SSR_MILL)
_ssr = importlib.util.module_from_spec(_ssr_spec)
assert _ssr_spec.loader is not None
_ssr_spec.loader.exec_module(_ssr)
SSR_CATALOG_LEN = len(_ssr.PAIRS)


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
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def mill_and_publish(factory: Path, mill: Path, n: int, token: str, staging: str, pair_index: int) -> None:
    mill_run = run(
        [
            sys.executable,
            str(mill),
            "--round",
            str(n),
            "--staging",
            staging,
            "--pair-index",
            str(pair_index),
        ]
    )
    sys.stderr.write(mill_run.stderr or "")
    if mill_run.stdout:
        print(mill_run.stdout, flush=True)
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


def abort(factory: Path, n: int, token: str) -> None:
    run(
        [
            sys.executable,
            str(TXN),
            "abort",
            str(factory),
            "--round",
            str(n),
            "--token",
            token,
        ],
        check=False,
    )


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else CATALOG_LEN
    min_rounds = 12
    deadline = time.monotonic() + 40 * 60
    done = 0
    hops = 0
    published: list[int] = []
    hop_published: list[int] = []
    pair_i = 0
    hop_pair_i = 0
    while done < max_rounds and time.monotonic() < deadline:
        n = frontier(FACTORY)
        if pair_i >= CATALOG_LEN:
            print(f"catalog exhausted after {pair_i} pairs (frontier {n})", flush=True)
            break
        if reserved(FACTORY, n):
            print(f"git-ops r{n} already reserved; hop secret-scan", flush=True)
            hn = frontier(HOP)
            if reserved(HOP, hn):
                print("secret-scan also reserved; never steal; retry git-ops shortly", flush=True)
                time.sleep(2)
                continue
            if hop_pair_i >= SSR_CATALOG_LEN:
                print(f"secret-scan catalog exhausted at frontier {hn}; wait for git-ops", flush=True)
                time.sleep(2)
                continue
            try:
                proc = run(
                    [
                        sys.executable,
                        str(TXN),
                        "reserve",
                        str(HOP),
                        "--round",
                        str(hn),
                        "--expected",
                        "2",
                    ]
                )
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                if reserved(HOP, hn):
                    print("lost race on secret-scan reserve; never steal", flush=True)
                    time.sleep(2)
                    continue
                print("secret-scan reserve failed", flush=True)
                return 5
            payload = json.loads(proc.stdout)
            print(f"hop reserved ssr r{hn} token={payload['token']}", flush=True)
            try:
                mill_and_publish(
                    HOP,
                    SSR_MILL,
                    hn,
                    payload["token"],
                    payload["staging_dir"],
                    hop_pair_i,
                )
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                abort(HOP, hn, payload["token"])
                return 6
            hops += 1
            hop_published.append(hn)
            hop_pair_i += 1
            print(f"hop published ssr r{hn} (hops={hops})", flush=True)
            continue
        try:
            proc = run(
                [
                    sys.executable,
                    str(TXN),
                    "reserve",
                    str(FACTORY),
                    "--round",
                    str(n),
                    "--expected",
                    "2",
                ]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                print("lost race on reserve; never steal; hop next loop", flush=True)
                continue
            print("reserve failed", flush=True)
            return 5
        payload = json.loads(proc.stdout)
        token = payload["token"]
        staging = payload["staging_dir"]
        print(f"reserved r{n} token={token} staging={staging} pair={pair_i}", flush=True)
        try:
            mill_and_publish(FACTORY, MILL, n, token, staging, pair_i)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print(f"mill/publish failed for r{n}; abort reservation", flush=True)
            abort(FACTORY, n, token)
            return 6
        done += 1
        pair_i += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
        if done >= min_rounds and time.monotonic() >= deadline:
            break
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "hop_rounds": hop_published,
                "frontier": frontier(FACTORY),
            }
        )
    )
    return 0 if done >= min_rounds or published or hop_published else 1


if __name__ == "__main__":
    raise SystemExit(main())
