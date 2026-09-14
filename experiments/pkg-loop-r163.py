#!/usr/bin/env python3
"""Reserve → mill → publish package-release-factory until catalog or max_rounds."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL_163 = ROOT / "experiments" / "pkg-mill-r163.py"
MILL_181 = ROOT / "experiments" / "pkg-mill-r181.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
AGENTIC = FACTORY.parent
SKIP_HOP = {"eval-harness-trajectory-factory"}

import importlib.util


def _load_mill(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_m163 = _load_mill(MILL_163)
_m181 = _load_mill(MILL_181)
CATALOG_FIRST = _m163.CATALOG_FIRST
CATALOG_LAST = _m181.CATALOG_FIRST + len(_m181.PAIRS) - 1


def mill_for(n: int) -> Path:
    if n >= _m181.CATALOG_FIRST:
        return MILL_181
    return MILL_163


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("+", " ".join(str(a) for a in args), flush=True)
    return subprocess.run(
        [str(a) for a in args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def frontier(factory: Path) -> dict:
    proc = run([sys.executable, TXN, "frontier", factory])
    return json.loads(proc.stdout)


def reserved_path(factory: Path, n: int) -> Path:
    return factory / f"ROUND-r{n:02d}.reserved.json"


def list_hop_targets() -> list[Path]:
    out = []
    for path in sorted(AGENTIC.iterdir()):
        if not path.is_dir():
            continue
        if path.name in SKIP_HOP or path.name == FACTORY.name:
            continue
        if not (path / ".round-marker-mode.json").exists() and not any(
            path.glob("ROUND-r*.complete.json")
        ):
            continue
        out.append(path)
    return out


def main() -> int:
    max_rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    done = 0
    published: list[int] = []
    while done < max_rounds:
        status = frontier(FACTORY)
        n = status["next_round"]
        last = CATALOG_LAST
        if n > last:
            print(f"catalog exhausted at frontier {n} (last {last})", flush=True)
            break
        if reserved_path(FACTORY, n).exists():
            print(f"package-release r{n} already reserved; scanning hops", flush=True)
            hopped = False
            for hop in list_hop_targets():
                hs = frontier(hop)
                hn = hs["next_round"]
                if reserved_path(hop, hn).exists():
                    print(f"hop {hop.name} r{hn} reserved; skip", flush=True)
                    continue
                print(
                    f"hop candidate {hop.name} r{hn} unreserved — no mill for hop; skip",
                    flush=True,
                )
            print("all hops reserved or unimplemented; never steal; stop", flush=True)
            return 3
        try:
            proc = run(
                [
                    sys.executable,
                    TXN,
                    "reserve",
                    FACTORY,
                    "--round",
                    str(n),
                    "--expected",
                    "2",
                ]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            if reserved_path(FACTORY, n).exists():
                print("lost race on reserve; never steal", flush=True)
                return 4
            print("reserve failed", flush=True)
            return 5
        payload = json.loads(proc.stdout)
        token = payload["token"]
        staging = payload["staging_dir"]
        print(f"reserved r{n} token={token} staging={staging}", flush=True)
        try:
            mill = run(
                [sys.executable, mill_for(n), "--round", str(n), "--staging", staging]
            )
            sys.stderr.write(mill.stderr or "")
            print(mill.stdout, flush=True)
            pub = run(
                [
                    sys.executable,
                    TXN,
                    "publish",
                    FACTORY,
                    "--round",
                    str(n),
                    "--token",
                    token,
                ]
            )
        except subprocess.CalledProcessError as exc:
            print(exc.stdout, exc.stderr, flush=True)
            print(f"mill/publish failed for r{n}; abort reservation", flush=True)
            run(
                [
                    sys.executable,
                    TXN,
                    "abort",
                    FACTORY,
                    "--round",
                    str(n),
                    "--token",
                    token,
                ],
                check=False,
            )
            return 6
        print(pub.stdout, flush=True)
        done += 1
        published.append(n)
        print(f"published r{n} ({done}/{max_rounds})", flush=True)
    nxt = frontier(FACTORY)["next_round"]
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "frontier": nxt,
                "catalog_last": CATALOG_LAST,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
