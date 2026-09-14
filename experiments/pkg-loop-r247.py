#!/usr/bin/env python3
"""Unbounded reserve → mill → publish for package-release-factory r247+.

Never steal a reserved round. If package-release is reserved, hop another
unreserved named factory that has a mill covering its frontier. Never hop
sandbox-refusal-factory. Writes only via round_txn.py reserve/publish.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MILL_247 = ROOT / "experiments" / "pkg-mill-r247.py"
MILL_275 = ROOT / "experiments" / "pkg-mill-r275.py"
MILL_290 = ROOT / "experiments" / "pkg-mill-r290.py"
MILL_296 = ROOT / "experiments" / "pkg-mill-r296.py"
SSL_MILL = ROOT / "experiments" / "ssl-mill-r35.py"
TXN = ROOT / "pipelines" / "round_txn.py"
FACTORY = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
AGENTIC = FACTORY.parent
SKIP_HOP = {"eval-harness-trajectory-factory", "sandbox-refusal-factory"}

import importlib.util


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_pkg247 = _load(MILL_247)
_pkg275 = _load(MILL_275)
_pkg290 = _load(MILL_290)
_pkg296 = _load(MILL_296)
CATALOG_FIRST = _pkg247.CATALOG_FIRST
CATALOG_LAST = _pkg296.CATALOG_FIRST + len(_pkg296.PAIRS) - 1


def mill_for(n: int) -> Path:
    if n >= _pkg296.CATALOG_FIRST:
        return MILL_296
    if n >= _pkg290.CATALOG_FIRST:
        return MILL_290
    if n >= _pkg275.CATALOG_FIRST:
        return MILL_275
    return MILL_247
SSL_FIRST = SSL_LAST = None
if SSL_MILL.exists():
    _ssl = _load(SSL_MILL)
    SSL_FIRST = _ssl.CATALOG_FIRST
    SSL_LAST = SSL_FIRST + len(_ssl.PAIRS) - 1


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
    proc = run([sys.executable, str(TXN), "frontier", str(factory)])
    return json.loads(proc.stdout)


def reserved_path(factory: Path, n: int) -> Path:
    return factory / f"ROUND-r{n:02d}.reserved.json"


def publish_round(factory: Path, mill: Path, n: int, expected: str = "2") -> None:
    proc = run(
        [
            sys.executable,
            str(TXN),
            "reserve",
            str(factory),
            "--round",
            str(n),
            "--expected",
            expected,
        ]
    )
    payload = json.loads(proc.stdout)
    token, staging = payload["token"], payload["staging_dir"]
    print(f"reserved {factory.name} r{n} token={token}", flush=True)
    try:
        mill_out = run(
            [sys.executable, str(mill), "--round", str(n), "--staging", staging]
        )
        print(mill_out.stdout, flush=True)
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
    except subprocess.CalledProcessError as exc:
        print(exc.stdout or "", exc.stderr or "", flush=True)
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


def hop_mill_for(factory: Path, n: int) -> Path | None:
    if factory.name == "ssl-cert-rotation-factory" and SSL_FIRST is not None:
        if SSL_FIRST <= n <= SSL_LAST:
            return SSL_MILL
    return None


def try_hop() -> str | None:
    ssl = AGENTIC / "ssl-cert-rotation-factory"
    hops = [ssl] + [
        path
        for path in sorted(AGENTIC.iterdir())
        if path.is_dir()
        and path.name not in SKIP_HOP
        and path != FACTORY
        and path != ssl
    ]
    for hop in hops:
        if not (hop / ".round-marker-mode.json").exists() and not any(
            hop.glob("ROUND-r*.complete.json")
        ):
            continue
        try:
            hs = frontier(hop)
        except Exception as exc:
            print(f"hop {hop.name} frontier failed: {exc}", flush=True)
            continue
        hn = hs["next_round"]
        if reserved_path(hop, hn).exists():
            print(f"hop {hop.name} r{hn} reserved; skip", flush=True)
            continue
        mill = hop_mill_for(hop, hn)
        if mill is None:
            print(f"hop {hop.name} r{hn} unreserved — no mill covering frontier; skip", flush=True)
            continue
        print(f"hop {hop.name} r{hn} mill={mill.name}", flush=True)
        publish_round(hop, mill, hn)
        return f"{hop.name}-{hn}"
    return None


def main() -> int:
    done = 0
    published: list[str] = []
    while True:
        status = frontier(FACTORY)
        n = status["next_round"]
        if n > CATALOG_LAST:
            print(
                f"catalog exhausted at frontier {n} (last {CATALOG_LAST})",
                flush=True,
            )
            break
        if reserved_path(FACTORY, n).exists():
            print(f"package-release r{n} already reserved; hop", flush=True)
            hopped = try_hop()
            if hopped is None:
                print("all hops reserved or unimplemented; never steal; stop", flush=True)
                return 3
            done += 1
            published.append(hopped)
            print(f"published hop {hopped} ({done})", flush=True)
            continue
        try:
            publish_round(FACTORY, mill_for(n), n)
        except subprocess.CalledProcessError as exc:
            text = (exc.stderr or "") + (exc.stdout or "")
            if reserved_path(FACTORY, n).exists() and "already" in text.lower():
                print("lost race on reserve; never steal; hop", flush=True)
                hopped = try_hop()
                if hopped is None:
                    return 4
                done += 1
                published.append(hopped)
                continue
            print("reserve/mill/publish failed", flush=True)
            return 6
        done += 1
        published.append(f"pkg-{n}")
        print(f"published package-release r{n} ({done})", flush=True)
    nxt = frontier(FACTORY)["next_round"]
    print(
        json.dumps(
            {
                "published": done,
                "rounds": published,
                "pkg_frontier": nxt,
                "catalog_last": CATALOG_LAST,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
