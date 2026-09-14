#!/usr/bin/env python3
"""Reserve → mill → publish proto-breaking-change-factory from r988 until catalog/quota dies.

Never exit after one batch. Hop an unreserved named factory if this seat is
already reserved. Never steal. Never rewrite raw.
Not eval-harness. Not sandbox-refusal (reserved or writing).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "pbc-mill-r988.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "proto-breaking-change-factory"
AGENTIC = FACTORY.parent
SKIP_HOP = {
    "eval-harness-trajectory-factory",
    "sandbox-refusal-factory",
}

import importlib.util


def load_mill():
    spec = importlib.util.spec_from_file_location("pbc_mill_r988", MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    return mill


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


COMPLETE_RE = __import__("re").compile(r"^ROUND-r(\d+)\.complete\.json$")


def frontier(factory: Path) -> int:
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    print(proc.stdout, flush=True)
    return json.loads(proc.stdout)["next_round"]


def next_round_fast(factory: Path) -> int:
    highest = 0
    for path in factory.glob("ROUND-r*.complete.json"):
        match = COMPLETE_RE.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def writing(factory: Path) -> bool:
    return any(factory.glob("ROUND-r*.reserved.json")) or any(
        factory.glob("ROUND-r*.publishing.json")
    )


def publish_one(factory: Path, n: int, mill: Path) -> None:
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
    print(f"reserved r{n} token={token} staging={staging}", flush=True)
    mill_proc = run([sys.executable, str(mill), "--round", str(n), "--staging", staging])
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


def hop_candidates() -> list[Path]:
    hops = []
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir():
            continue
        if path.name in SKIP_HOP or path == FACTORY:
            continue
        if writing(path):
            continue
        if not (path / ".round-marker-mode.json").exists() and not list(
            path.glob("batch-r*.jsonl")
        ):
            continue
        hops.append(path)
    return hops


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    done = 0
    hops = 0
    published: list[int] = []
    mill = load_mill()
    taken = mill.used_slugs()

    def unused_n() -> int:
        return sum(
            1
            for suc, xf in mill.PAIRS
            if suc["slug"] not in taken and xf["slug"] not in taken
        )

    while done < max_rounds:
        n = next_round_fast(FACTORY)
        if reserved(FACTORY, n) or writing(FACTORY):
            hops += 1
            print(f"proto-breaking-change r{n} reserved/writing; never steal", flush=True)
            hopped = False
            for hop in hop_candidates():
                hn = next_round_fast(hop)
                if reserved(hop, hn) or writing(hop):
                    print(f"{hop.name} r{hn} reserved/writing; skip", flush=True)
                    continue
                print(
                    json.dumps(
                        {
                            "hop": hop.name,
                            "next_round": hn,
                            "unreserved": True,
                            "note": "PBC seat held; hop listed, keep looping PBC when free",
                        }
                    ),
                    flush=True,
                )
                hopped = True
                break
            if not hopped:
                print("no unreserved hop factory", flush=True)
            n2 = next_round_fast(FACTORY)
            if reserved(FACTORY, n2) or writing(FACTORY):
                continue
            n = n2
        left = unused_n()
        if left <= 0:
            print(f"catalog exhausted at frontier {n}", flush=True)
            break
        try:
            publish_one(FACTORY, n, MILL)
        except subprocess.CalledProcessError as exc:
            text = f"{exc.stdout or ''}{exc.stderr or ''}"
            print(exc.stdout, exc.stderr, flush=True)
            if "already exists" in text or "is not the frontier" in text:
                print("lost race; retry next frontier", flush=True)
                continue
            if reserved(FACTORY, n):
                print("mill/publish failed with our seat held", flush=True)
                return 4
            print("reserve/mill/publish failed; retry", flush=True)
            continue
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds}) unused_left={left - 1}", flush=True)
        mill = load_mill()
        taken = mill.used_slugs()
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "frontier": frontier(FACTORY),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
