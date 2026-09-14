#!/usr/bin/env python3
"""Reserve → mill → publish monorepo-dep-bump-factory from r1407 until catalog/quota.

If mdb is reserved, hop another unreserved named factory (never sandbox-refusal
if reserved or writing). Never steal. Never rewrite raw. No idle sleep.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL = ROOT / "experiments" / "mdb-mill-r1407.py"
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


def writing(factory: Path) -> bool:
    return any(factory.glob("ROUND-r*.reserved.json"))


def catalog_last(mill: Path) -> tuple[int, int] | None:
    try:
        spec = importlib.util.spec_from_file_location("mill_live", mill)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
    except Exception as exc:
        print(f"mill load fail {mill.name}: {exc}", flush=True)
        return None
    first = getattr(mod, "CATALOG_FIRST", None)
    pairs = getattr(mod, "PAIRS", None)
    if isinstance(first, int) and pairs:
        return first, first + len(pairs) - 1
    return None


def publish_round(factory: Path, n: int, expected: int, mill: Path) -> None:
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
    print(f"reserved {factory.name} r{n} token={token} staging={staging}", flush=True)
    mill_proc = run(
        [sys.executable, str(mill), "--round", str(n), "--staging", staging]
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


def hop_named() -> tuple[Path, Path, int] | None:
    """Scan other unreserved named factories. Never sandbox-refusal if reserved/writing."""
    for factory in sorted(p for p in AGENTIC.iterdir() if p.is_dir()):
        name = factory.name
        if name == FACTORY.name:
            continue
        if name == "sandbox-refusal-factory" and (writing(factory) or reserved(factory, frontier(factory))):
            print("hop skip sandbox-refusal reserved/writing", flush=True)
            continue
        if name in SKIP_HOP:
            continue
        n = frontier(factory)
        if reserved(factory, n) or writing(factory):
            print(f"hop skip {name} r{n} reserved/writing", flush=True)
            continue
        print(f"named factory {name} r{n} unreserved but no mill mapping; skip", flush=True)
    return None


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    done = 0
    hops = 0
    published: list[str] = []
    span = catalog_last(MILL)
    if span is None:
        print("mdb mill catalog missing", flush=True)
        return 3
    first, last = span
    while done < max_rounds:
        n = frontier(FACTORY)
        if n > last:
            print(f"mdb catalog exhausted at frontier {n} (last={last})", flush=True)
            break
        if n < first:
            print(f"mdb frontier {n} below catalog first {first}; hop", flush=True)
            hops += 1
            picked = hop_named()
            if picked is None:
                print("no unreserved hop mill; stop rather than idle", flush=True)
                break
            factory, mill, hn = picked
            try:
                publish_round(factory, hn, 2, mill)
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                continue
            done += 1
            published.append(f"{factory.name}-r{hn}")
            print(f"published hop {factory.name} r{hn} ({done}/{max_rounds})", flush=True)
            continue
        if reserved(FACTORY, n):
            print(f"mdb r{n} already reserved; hop (no steal)", flush=True)
            hops += 1
            picked = hop_named()
            if picked is None:
                print("no unreserved hop mill; stop rather than idle", flush=True)
                break
            factory, mill, hn = picked
            try:
                publish_round(factory, hn, 2, mill)
            except subprocess.CalledProcessError as exc:
                print(exc.stdout, exc.stderr, flush=True)
                if reserved(factory, hn) and not (factory / f"ROUND-r{hn:02d}.complete.json").exists():
                    print("lost hop race; hop next", flush=True)
                    continue
                return 4
            done += 1
            published.append(f"{factory.name}-r{hn}")
            print(f"published hop {factory.name} r{hn} ({done}/{max_rounds})", flush=True)
            continue
        try:
            publish_round(FACTORY, n, 2, MILL)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved(FACTORY, n) and not (FACTORY / f"ROUND-r{n:02d}.complete.json").exists():
                print("lost race or mill/publish failed after reserve", flush=True)
                hops += 1
                continue
            print(f"reserve/mill/publish failed for r{n}", flush=True)
            return 5
        done += 1
        published.append(f"mdb-r{n}")
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    nxt = frontier(FACTORY) if FACTORY.exists() else None
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "hops": hops,
                "frontier": nxt,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
