#!/usr/bin/env python3
"""Reserve → mill → publish git-ops-recovery-factory until catalog or max_rounds.

Never steal. Never rewrite raw. If git-ops is reserved, hop
observability-debug-factory when that seat is unreserved and in catalog.
Never hop sandbox-refusal. Never hop eval-harness.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "gor-mill-r1046.py"
OBS_MILL = ROOT / "scripts" / "observability_debug_mill" / "mill.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "git-ops-recovery-factory"
HOP = AGENTIC / "observability-debug-factory"
HOP_EXPECTED = 2
HOP_START = 159
HOP_LAST = 271

import importlib.util


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


GOR = load(MILL, "gor_mill_r1046")


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
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish_one(factory: Path, n: int, mill: Path, expected: int = 2) -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            str(expected),
        ]
    )
    print(proc.stdout, flush=True)
    payload = json.loads(proc.stdout)
    token = payload["token"]
    staging = payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    try:
        if mill == OBS_MILL:
            mill_cmd = [sys.executable, str(mill), "emit", str(n), staging]
        else:
            mill_cmd = [sys.executable, str(mill), "--round", str(n), "--staging", staging]
        mill_proc = run(mill_cmd)
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
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, flush=True)
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
        raise
    print(pub.stdout, flush=True)


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    done = 0
    hops = 0
    published: list[str] = []

    def unused_count() -> int:
        gor = load(MILL, "gor_mill_r1046")
        used = gor._published_slugs()
        return sum(
            1
            for a, b in gor.PAIRS
            if a["slug"] not in used and b["slug"] not in used
        )

    while done < max_rounds:
        n = frontier(FACTORY)
        if reserved(FACTORY, n) or unused_count() == 0:
            why = "reserved" if reserved(FACTORY, n) else "catalog empty"
            print(f"git-ops r{n} {why}; hop observability", flush=True)
            hn = frontier(HOP)
            if reserved(HOP, hn) or hn < HOP_START or hn > HOP_LAST:
                if unused_count() == 0:
                    print("no unused unique pairs and hop unavailable; stop", flush=True)
                    break
                print("observability reserved or outside catalog; never steal; retry git-ops", flush=True)
                return 3
            try:
                publish_one(HOP, hn, OBS_MILL, expected=HOP_EXPECTED)
            except subprocess.CalledProcessError:
                print(f"hop mill/publish failed for observability r{hn}", flush=True)
                return 4
            hops += 1
            published.append(f"obs-{hn}")
            done += 1
            print(f"published observability r{hn} ({done}/{max_rounds})", flush=True)
            continue
        try:
            publish_one(FACTORY, n, MILL, expected=2)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n):
                print("lost race on reserve; never steal; hop next", flush=True)
                continue
            print("reserve/mill/publish failed", flush=True)
            return 5
        done += 1
        published.append(f"gor-{n}")
        print(f"published git-ops r{n} ({done}/{max_rounds})", flush=True)
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "frontier": frontier(FACTORY),
                "unused_pairs": unused_count(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
