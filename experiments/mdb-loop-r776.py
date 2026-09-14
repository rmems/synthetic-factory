#!/usr/bin/env python3
"""Reserve → mill → publish monorepo-dep-bump-factory until catalog or stop.

If mdb is reserved, hop another unreserved named factory (never sandbox-refusal).
Never steal. Never rewrite raw. No idle sleep.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "mdb-mill-r840.py"
TXN = ROOT / "pipelines" / "round_txn.py"
AGENTIC = ROOT / "outputs" / "raw" / "2026-08-19-agentic"
FACTORY = AGENTIC / "monorepo-dep-bump-factory"
SKIP_HOP = {"sandbox-refusal-factory"}

import importlib.util


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
    nxt = json.loads(proc.stdout)["next_round"]
    print(f"frontier {factory.name} next_round={nxt}", flush=True)
    return nxt


def reserved(factory: Path, n: int) -> bool:
    return (factory / f"ROUND-r{n:02d}.reserved.json").exists()


def publish_round(
    factory: Path,
    n: int,
    expected: int,
    mill: Path,
    token: str | None = None,
    staging: str | None = None,
) -> None:
    if token is None or staging is None:
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
        payload = json.loads(proc.stdout)
        print(proc.stdout, flush=True)
        token = payload["token"]
        staging = payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token} staging={staging}", flush=True)
    mill_proc = run(
        [
            sys.executable,
            str(mill),
            "--round",
            str(n),
            "--staging",
            staging,
        ]
    )
    if mill_proc.stderr:
        sys.stderr.write(mill_proc.stderr)
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


def reload_catalog() -> tuple[int, int]:
    spec = importlib.util.spec_from_file_location("mdb_mill_live", MILL)
    mill = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mill)
    return mill.CATALOG_FIRST, len(mill.PAIRS)


def hop_targets() -> list[Path]:
    out: list[Path] = []
    if not AGENTIC.is_dir():
        return out
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir() or path.name.startswith("."):
            continue
        if path.name in SKIP_HOP:
            continue
        if path.resolve() == FACTORY.resolve():
            continue
        n = None
        try:
            n = frontier(path)
        except Exception as exc:
            print(f"hop skip {path.name}: frontier failed {exc}", flush=True)
            continue
        if reserved(path, n):
            print(f"hop skip {path.name} r{n} reserved", flush=True)
            continue
        out.append(path)
    return out


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    pre_token = sys.argv[2] if len(sys.argv) > 2 else None
    pre_staging = sys.argv[3] if len(sys.argv) > 3 else None
    done = 0
    hops = 0
    published: list[str] = []
    while done < max_rounds:
        first, length = reload_catalog()
        last = first + length - 1
        n = frontier(FACTORY)
        if n > last:
            print(f"mdb catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if n < first:
            print(f"mdb frontier {n} below catalog first {first}; hop", flush=True)
            hops += 1
            break
        if reserved(FACTORY, n) and not (pre_token and n == first and done == 0):
            print(f"mdb r{n} already reserved; hop (no steal)", flush=True)
            hops += 1
            targets = hop_targets()
            if not targets:
                print("no unreserved hop target; stop", flush=True)
                break
            print("unreserved hop candidates:", [p.name for p in targets[:8]], flush=True)
            print("mdb reserved; no hop mill in this loop; stop rather than idle", flush=True)
            break
        try:
            if done == 0 and pre_token and pre_staging and n == first:
                publish_round(FACTORY, n, 2, MILL, token=pre_token, staging=pre_staging)
                pre_token = None
                pre_staging = None
            else:
                publish_round(FACTORY, n, 2, MILL)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n) and not (FACTORY / f"ROUND-r{n:02d}.complete.json").exists():
                print("lost race or mill/publish failed after reserve", flush=True)
                return 4
            print(f"reserve/mill/publish failed for r{n}", flush=True)
            return 5
        done += 1
        published.append(f"mdb-r{n}")
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
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
